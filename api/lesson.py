from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from bson import ObjectId
from fastapi.responses import FileResponse
from pymongo import ReturnDocument
from datetime import datetime, timezone
from bson.errors import InvalidId
import os

from database.mongo import module_collection, profile_collection, lesson_collection, user_collection, feedback_collection
from utils.role_auth import require_roles
from utils.progress import calculate_progress
from schema import FeedbackSchema

router = APIRouter()
security = HTTPBearer()

# List of lessons with user progress
@router.get('/api/lessons')
async def get_lessons(user = Depends(require_roles(['user','learner', 'admin'], [user_collection, profile_collection]))):

    if user['role'] == 'user':
        user = await profile_collection.find_one({'owner_id': user['id'],'role':'user'})
        
    elif user['role'] == 'learner':
        try:
            id = ObjectId(user['id'])
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid ID format")
        
        user = await profile_collection.find_one({'_id':id})

    if not user:
        raise HTTPException(status_code=404, detail="Profile not found")

    pipeline= [
        {
            '$sort': {
                '_id': 1
            }
        },
        {
            '$lookup': {
                'from':'modules',
                'let': {
                'lessonId': '$_id'
                },
                'pipeline': [
                    {
                        '$match': {
                            '$expr': {
                                '$eq': ['$lesson_id', '$$lessonId']
                            }
                        }
                    },
                    {
                        '$sort': {
                            '_id': 1
                        }
                    }
                ],
                'as': 'modules'
            }
        }
    ]
    lessons=[]
    async for doc in lesson_collection.aggregate(pipeline):
        lessons.append({
            'lesson_id': str(doc['_id']),
            'lesson_name': doc.get('lesson_name'),
            'modules': [{
                'module_id': str(module['_id']),
                'module_name': module.get('module_name')
            }for module in doc.get('modules',[])]
        })

    return {
        'name': user.get('name'),
        'progress': user.get('progress',0),
        'lessons': lessons
    }

# List of modules
@router.get('/api/lesson/{lesson_id}')
async def get_lesson_modules(
    lesson_id: str,
    user = Depends(require_roles(['user','learner', 'admin'], [user_collection, profile_collection]))
):
    
    try:
        id = ObjectId(lesson_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    lesson = await lesson_collection.find_one({'_id': id})
    if not lesson:
        raise HTTPException(status_code=409, detail="Lesson not found")
    
    if user['role'] == 'user':
        user = await profile_collection.find_one({'owner_id': user['id'],'role':'user'})
        if not user:
            raise HTTPException(status_code=404, detail="Profile not found")
        user['id'] = str(user['_id'])

    return [{
        'module_id': str(doc['_id']),
        'module_name': doc.get('module_name')
    } async for doc in module_collection.find({'lesson_id': id}).sort({"_id":1})]


# Module info
@router.get('/api/lesson/module/{module_id}')
async def get_module_data(
    module_id: str,
    user = Depends(require_roles(['user','learner', 'admin'], [user_collection, profile_collection]))
):

    if user['role'] == 'user':
        user = await profile_collection.find_one({'owner_id': user['id'], 'role': 'user'})
        if not user:
            raise HTTPException(status_code=404, detail="Profile not found")
        user['id'] = str(user['_id'])
    
    try:
        id = ObjectId(module_id)
        user_id = ObjectId(user['id'])
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    module = await module_collection.find_one({'_id': id})

    if module is None:
        raise HTTPException(
            status_code=404, detail="Module not found"
        )

    data = {
        'module_id': str(module['_id']),
        'module_name': module.get('module_name'),
        'audio': f"/api/media/audio/{module_id}"
    }

    if user['role'] != 'admin':
        result = await profile_collection.find_one_and_update(
            {'_id': user_id},
            {
                '$addToSet': {'lessons_attended': module['_id']}
            },
            return_document=ReturnDocument.AFTER
        )
        progress = await calculate_progress(len(result.get('lessons_attended',[])))

        await profile_collection.update_one(
            {'_id': user_id},
            {
                '$set': {'progress': progress}
            }
        )
    
    return data

# getting audio
@router.get('/api/media/audio/{module_id}')
async def get_audio(module_id: str, user = Depends(require_roles(['user','learner', 'admin'], [user_collection, profile_collection]))):

    try:
        id = ObjectId(module_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    module = await module_collection.find_one({'_id': id})
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    audio_path = module.get('audio_path')

    if not audio_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No audio path associated with this module"
        )

    if not os.path.exists(audio_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found on server"
        )
    
    return FileResponse(module.get('audio_path'), media_type="audio/mpeg")

# Feedback
@router.post('/api/feedback')
async def collect_feedback(
    feedback: FeedbackSchema,
    user = Depends(require_roles(['user','learner'], [user_collection, profile_collection]))
):
    
    try:
        id = ObjectId(user['id'])    
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid id"
        )
    
    if user['role'] == 'user':
        user = await profile_collection.find_one({'owner_id': user['id'], 'role': 'user'})
    elif user['role'] == 'learner':
        user = await profile_collection.find_one({'_id': id})
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found")
    user['id'] = str(user['_id'])

    
    result = await feedback_collection.update_one(
        {'user_id': user['id']},
        {
            '$set': {
                'name': user['name'],
                'rating': feedback.rating,
                'comments': feedback.comments,
                'admin_approved': False,
                'updated_at': datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    return {'message': 'feedback added successfully'}