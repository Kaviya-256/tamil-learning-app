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
from utils.validation import validate_object_id

router = APIRouter()
security = HTTPBearer()

# List of lessons with user progress
@router.get('/api/lessons')
async def get_lessons(user = Depends(require_roles(['user','learner', 'admin'], [user_collection, profile_collection]))):

    user_id = ObjectId(user['id'])

    if user['role'] == 'learner':
        user = await profile_collection.find_one({'_id': user_id})
    else:
        user = await user_collection.find_one({'_id': user_id})
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
    
    data = {
        'name': user.get('name'),
        'progress': user.get('progress',0),
        'lessons': lessons
    }

    if user['role']!= 'admin':
        data.update({
            'lessons_attended': [
                str(lesson_id)
                for lesson_id in user.get('lessons_attended', [])
            ]
        })

    return data


# List of modules
@router.get('/api/lesson/{lesson_id}')
async def get_lesson_modules(
    lesson_id: str,
    user = Depends(require_roles(['user','learner', 'admin'], [user_collection, profile_collection]))
):
    
    lesson_id = validate_object_id(lesson_id)
    
    lesson = await lesson_collection.find_one({'_id': lesson_id})
    if not lesson:
        raise HTTPException(status_code=409, detail="Lesson not found")

    return [{
        'module_id': str(doc['_id']),
        'module_name': doc.get('module_name')
    } async for doc in module_collection.find({'lesson_id': lesson_id}).sort({"_id":1})]


# Module info
@router.get('/api/lesson/module/{module_id}')
async def get_module_data(
    module_id: str,
    user = Depends(require_roles(['user','learner', 'admin'], [user_collection, profile_collection]))
):

    module_id = validate_object_id(module_id)
    user_id = ObjectId(user.get('id'))

    module = await module_collection.find_one({'_id': module_id})

    if module is None:
        raise HTTPException(
            status_code=404, detail="Module not found"
        )

    data = {
        'module_id': str(module['_id']),
        'module_name': module.get('module_name'),
        'audio': f"/api/media/audio/{module_id}"
    }

    # if user['role'] != 'admin':
        
    if user['role'] == 'user' or user['role']=='admin':
        result = await user_collection.find_one_and_update(
            {'_id': user_id},
            {
                '$addToSet': {'lessons_attended': module['_id']}
            },
            return_document=ReturnDocument.AFTER
        )
        progress = await calculate_progress(len(result.get('lessons_attended',[])))

        await user_collection.update_one(
            {'_id': user_id},
            {
                '$set': {'progress': progress}
            }
        )

    elif user['role'] == 'learner':
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


    module_id = validate_object_id(module_id)
    
    module = await module_collection.find_one({'_id': module_id})
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