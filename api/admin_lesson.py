from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from motor.motor_asyncio import AsyncIOMotorCollection
import re
import uuid
from typing import Optional
import os
# import unicodedata
from fastapi.responses import Response
import json

from utils.role_auth import require_roles
from database.mongo import user_collection, lesson_collection, module_collection, asset_collection
from database.db_dependency import get_module_game_map_collection
from schema import LessonSchema, ModuleSchema
from utils.validation import validate_object_id

router = APIRouter(tags=['Admin Lesson Management'])

UPLOAD_DIR_IMAGE = 'asset/image'
UPLOAD_DIR_AUDIO = 'asset/audio'


# ------------- Lessons that are present -------------------
@router.get('/api/admin/lesson')
async def list_lessons(admin = Depends(require_roles(['admin'], [user_collection]))):
    
    return [{
        'lesson_id': str(doc['_id']),
        'lesson_name': doc.get('lesson_name'),
        'modules_count': doc.get('modules_count')
    }async for doc in lesson_collection.find().sort({"_id":1})]

# --------------------- To add  new lessons ------------------------
@router.post('/api/admin/add-lesson')
async def add_lesson(
    lesson: LessonSchema,
    admin = Depends(require_roles(['admin'], [user_collection]))
):
    result = await lesson_collection.find_one({'lesson_name': lesson.lesson_name})
    if result:
        raise HTTPException(status_code=409, detail="Lesson already exist")
    
    data = {
        'lesson_name': lesson.lesson_name,
        'modules_count': 0,
        'games': [],
        'games_count': 0
    }
    await lesson_collection.insert_one(data)
    return {
        'message': 'Lesson added'
    }

# ----------------- To get list of modules from a lesson ---------------
@router.get('/api/admin/lesson/{lesson_id}')
async def lesson_modules(
    lesson_id: str,
    admin = Depends(require_roles(['admin'], [user_collection]))
):
    
    lesson_id = validate_object_id(lesson_id)

    lesson = await lesson_collection.find_one({'_id': lesson_id})
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    modules=[
        {
            'module_id': str(doc['_id']),
            'module_name': doc.get('module_name')
        }async for doc in module_collection.find({'lesson_id': lesson_id}).sort({'_id':1})
    ]
    # if modules:
    #     raise HTTPException(status_code=404, detail="Lesson not found")
    return Response(
        content= json.dumps(modules, ensure_ascii=False),
        media_type='application/json; charset=utf-8'
    )
    # return modules


# ------------------- To add modules to an existing lesson --------------------
@router.post('/api/admin/{lesson_id}/add-module')
async def add_modules(
    module: ModuleSchema, lesson_id: str,
    admin = Depends(require_roles(['admin'], [user_collection])),
    module_game_map_col: AsyncIOMotorCollection = Depends(get_module_game_map_collection)
):
    
    lesson_id = validate_object_id(lesson_id)
    
    lesson = await lesson_collection.find_one({'_id': lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    data = module.model_dump()
    # text = unicodedata.normalize('NFC', data.get('module_name'))


    existing_module = await module_collection.find_one({'module_name': module.module_name, 'lesson_id': lesson_id})

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
        'lesson_id': lesson_id,
        'audio_path': asset['audio_path']
    })
    # data = {
    #     'module_name': text,
    #     'lesson_id': lesson_id,
    #     'audio_path': asset['audio_path']
    # }
    inserted_module = await module_collection.insert_one(data)

    result=await lesson_collection.update_one(
        {'_id':lesson_id},
        {
            '$inc': {'modules_count': 1}
        }
    )
     
    # if result.get('games_count') != 0:
    #     games = result.get('games')
    #     for game in games:
    #         data = await module_game_map_col.insert_one({
    #             'lesson_id': lesson_id,
    #             'module_id': inserted_module.inserted_id,
    #             'game_id': game
    #         })

    return {
        'message': 'Module added to lesson'
    }

# ------------------------ Update lesson name ---------------------------
@router.put('/api/admin/{lesson_id}/update-lesson')
async def update_lesson(
    lesson: LessonSchema, lesson_id: str,
    admin = Depends(require_roles(['admin'], [user_collection]))
):
    
    lesson_id = validate_object_id(lesson_id)
    
    data = await lesson_collection.update_one(
        {'_id': lesson_id},
        {
            '$set': {'lesson_name': lesson.lesson_name}
        }
    )
    if data.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    return {'message': 'lesson updated successfully'}


# --------------------------- Deleting lesson ---------------------------------
@router.delete('/api/admin/{lesson_id}/delete-lesson')
async def delete_lesson(
    lesson_id: str,
    admin = Depends(require_roles(['admin'], [user_collection])),
    module_game_map_col: AsyncIOMotorCollection = Depends(get_module_game_map_collection)
):

    lesson_id = validate_object_id(lesson_id)
    
    lesson = await lesson_collection.find_one_and_delete({'_id': lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    await module_game_map_col.delete_many({'lesson_id': lesson_id})
    await module_collection.delete_many({'lesson_id': lesson_id})

    return {'message': 'lesson deleted'}

# ---------------------------- Deleting Module  ------------------------------------
@router.delete('/api/admin/lesson/{module_id}/delete-module')
async def delete_module(
    module_id: str, admin = Depends(require_roles(['admin'], [user_collection])),
    module_game_map_col: AsyncIOMotorCollection = Depends(get_module_game_map_collection)
):

    module_id = validate_object_id(module_id)
    
    module =  await module_collection.find_one_and_delete({'_id':module_id})
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    await module_game_map_col.delete_many({'module_id': module_id})
        
    await lesson_collection.update_one(
        {'_id': module.get('lesson_id')},
        {'$inc': {'modules_count': -1}}
    )

    return {'message': 'Module deleted'}

# ----------------------------- Search asset ------------------------------------
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

# -------------------------- Uploading Asset ------------------------
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