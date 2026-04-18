# admin.py
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends
import uuid
import os
from bson import ObjectId
import re
from typing import Optional

from schema import ModuleSchema, LessonSchema
from database.mongo import user_collection, asset_collection, profile_collection, lesson_collection, module_collection
from utils.role_auth import require_roles

router = APIRouter()

UPLOAD_DIR_IMAGE = 'asset/image'
UPLOAD_DIR_AUDIO = 'asset/audio'

# Get admin
@router.get('/api/admin')
async def get_admin(admin = Depends(require_roles(['admin'], [user_collection]))):

    asset_count = await asset_collection.count_documents({})
    lesson_count = await lesson_collection.count_documents({})
    return {
        'name': admin['name'],
        'role': admin['role'],
        'asset_count': asset_count,
        'lesson_count': lesson_count
    }

# List of users: Dashboard
@router.get('/api/admin/users')
async def admin_dashboard(admin = Depends(require_roles(['admin'], [user_collection]))):
    
    result=user_collection.find({}, {'name':1, 'progress':1, 'role':1})    
    user=[]
    async for doc in result:
        if doc.get('role') != 'admin':
            user.append({
                'user_id': str(doc['_id']),
                'name': doc.get('name'),
                'progress': doc.get('progress'),
                'role': doc.get('role')
            })
    return user

@router.get('/api/admin/{user_id}/learners')
async def get_users_learners(
    user_id: str, 
    admin = Depends(require_roles(['admin'], [user_collection]))
):
    result = profile_collection.find({'owner_id': user_id})
    learners=[]

    async for doc in result:
        if doc.get('role') != 'user':
            learners.append({
                'learner_id': str(doc['_id']),
                'username': doc.get('username'),
                'name': doc.get('name'),
                'age': doc.get('age'),
                'progress': doc.get('progress'),
                'role': doc.get('role')
            })
            
    return learners

# Lessons that are present
@router.get('/api/admin/lesson')
async def list_lessons(admin = Depends(require_roles(['admin'], [user_collection]))):
    
    return [{
        'lesson_id': str(doc['_id']),
        'lesson_name': doc.get('lesson_name'),
        'modules_count': doc.get('modules_count')
    }async for doc in lesson_collection.find()]

# To add  new lessons
@router.post('/api/admin/add-lesson')
async def add_lesson(
    lesson: LessonSchema,
    admin = Depends(require_roles(['admin'], [user_collection]))
):
    data = {
        'lesson_name': lesson.lesson_name,
        'modules_count': 0
    }
    await lesson_collection.insert_one(data)
    return {
        'message': 'Lesson added'
    }

# To get list of modules from a lesson
@router.get('/api/admin/lesson/{lesson_id}')
async def lesson_modules(
    lesson_id: str,
    admin = Depends(require_roles(['admin'], [user_collection]))
):    
    return [
        {
            'module_id': str(doc['_id']),
            'module_name': doc.get('module_name')}
    async for doc in module_collection.find({'lesson_id': ObjectId(lesson_id)})]


# To add modules to an existing lesson
@router.post('/api/admin/{lesson_id}/add-module')
async def add_modules(
    module: ModuleSchema, lesson_id: str,
    admin = Depends(require_roles(['admin'], [user_collection]))
):
    
    data = module.model_dump()

    existing_module = await module_collection.find_one({'module_name': module.module_name, 'lesson_id': ObjectId(lesson_id)})

    if existing_module:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Module already exist in this lesson"
        )

    asset = await asset_collection.find_one({'asset_name': module.module_name})
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found in asset, upload first"
        )
    
    data.update({
        'lesson_id': ObjectId(lesson_id),
        'audio_path': asset['audio_path']
    })
    
    await module_collection.insert_one(data)
    

    result=await lesson_collection.update_one(
        {'_id':ObjectId(lesson_id)},
        {
            '$inc': {'modules_count': 1}
        }
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    return {
        'message': 'Module added to lesson'
    }

# Update lesson name
@router.put('/api/admin/{lesson_id}/update-lesson')
async def update_lesson(lesson: LessonSchema, lesson_id: str):
    data = await lesson_collection.find_one_and_update(
        {'_id': ObjectId(lesson_id)},
        {
            '$set': {'lesson_name': lesson.lesson_name}
        }
    )
    return {'message': 'lesson updated successfully'}


# Deleting lesson
@router.delete('/api/admin/{lesson_id}/delete-lesson')
async def delete_lesson(lesson_id: str):
    await module_collection.delete_many({'lesson_id': ObjectId(lesson_id)})
    await lesson_collection.delete_one({'_id': ObjectId(lesson_id)})
    return {'message': 'lesson deleted'}

# Deleting Module 
@router.delete('/api/admin/lesson/{module_id}/delete-module')
async def delete_module(module_id: str):
    await module_collection.delete_one({'_id': ObjectId(module_id)})
    return {'message': 'Module deleted'}

# Uploading Asset
@router.post('/api/admin/asset/upload-asset')
async def add_new_content(
    asset_name: str,
    image: Optional[UploadFile]=File(None),
    audio: UploadFile=File(...),
    admin = Depends(require_roles(['admin'], [user_collection]))
):
    asset = await asset_collection.find_one({'asset_name': asset_name})
    if asset:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Asset alreay exist for {asset_name}"
        )

    audio_name=f'{asset_name}_{uuid.uuid4()}'
    audio_path=os.path.join(UPLOAD_DIR_AUDIO, audio_name)    
    
    with open(audio_path,'wb') as f:
        f.write(await audio.read())
    
    data={
        'asset_name': asset_name,
        'audio_path': audio_path
    }
    
    if image:
        image_name=f'{asset_name}_{uuid.uuid4()}'
        image_path=os.path.join(UPLOAD_DIR_IMAGE, image_name)
        with open(image_path,'wb') as f:
            f.write(await image.read())
        
        data.update({
            'image_path': image_path
        })    
    
    await asset_collection.insert_one(data)
    
    return {
        'message':'asset added successfully'
    }

# Search asset
@router.get('/api/admin/search-asset')
async def search_asset(q: str='', admin = Depends(require_roles(['admin'], [user_collection]))):
    if not q:
        return {'results': []}
    
    escaped=re.escape(q)

    cursor = asset_collection.find(
        {'asset_name': {'$regex': f'^{escaped}'}},
        {'asset_name':1, '_id':0}
    ).collation({
        'locale':'ta',
        'strength':1
    }).limit(20)

    results=await cursor.to_list(length=20)
    return {'results': [r['asset_name'] for r in results]}

# displaying assets
# @router.get('/api/admin/asset')
# async def get_assets(admin: dict = Depends(get_current_admin)):
#     return [{
#         'name': doc.get('asset_name'),
#         # 'image': f'/api/media/image/{doc.get('image_path')}',
#         # 'audio': f'/api/media/audio/{doc.get('audio_path')}'
#     }async for doc in asset_collection.find()]

# # getting image
# @router.get('/api/media/image/{file_name}')
# def get_image(file_name: str, admin: dict = Depends(get_current_admin)):
#     print('1')
#     return FileResponse(f'{file_name}')

# # getting audio
# @router.get('/api/media/audio/{file_name}')
# def get_audio(file_name: str, admin: dict = Depends(get_current_admin)):
#     print('2')
#     return FileResponse(f'{file_name}')
