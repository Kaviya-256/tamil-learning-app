from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from bson import ObjectId

from database.mongo import module_collection, profile_collection, lesson_collection, user_collection
from utils.role_auth import require_roles
from utils.progress import calculate_progress

router = APIRouter()
security = HTTPBearer()

@router.get('/api/lessons')
async def get_lessons(user = Depends(require_roles(['user','learner'], [user_collection, profile_collection]))):

    if user['role'] == 'user':
        user = await profile_collection.find_one({'owner_id': user['id'],'role':'user'})

    pipeline= [
        {
            '$lookup': {
                'from':'modules',
                'localField': '_id',
                'foreignField': 'lesson_id',
                'as': 'modules'
            }
        }
    ]
    lessons=[]
    async for doc in lesson_collection.aggregate(pipeline):
        lessons.append({
            'lesson_id': str(doc['_id']),
            'lesson_name': doc.get('lesson_name'),
            'modules_count': doc.get('modules_count'),
            'modules': [{
                'module_id': str(module['_id']),
                'module_name': module.get('module_name')
            }for module in doc.get('modules',[])]
        })

    return {
        'name': user.get('name'),
        'progress': user.get('progress'),
        'lessons': lessons
    }


# @router.get('/api/lesson/{lesson_id}')
# async def get_lesson_modules(
#     lesson_id: str,
#     user = Depends(require_roles(['user','learner'], [user_collection, profile_collection]))
# ):
#     if user['role'] == 'user':
#         user = await profile_collection.find_one({'owner_id': user['id'],'role':'user'})
#         user['id'] = str(user['_id'])

#     lesson = await lesson_collection.find_one({'_id': ObjectId(lesson_id)})

#     result = await profile_collection.find_one_and_update(
#         {'_id': ObjectId(user['id'])},
#         {
#             '$addToSet': {'lessons_attended': lesson['lesson_name']}
#         }
#     )
#     print(str(result['_id']))
#     progress = await calculate_progress(len(result['lessons_attended'])-1)

#     await profile_collection.update_one(
#         {'_id': ObjectId(user['id'])},
#         {
#             '$set': {'progress': progress}
#         }
#     )
#     print('hello')

#     return [{
#         'module_id': str(doc['_id']),
#         'module_name': doc.get('module_name')
#     } async for doc in module_collection.find({'lesson_id': lesson_id})]

@router.get('/api/lesson/{module_id}')
async def get_module_data(
    module_id: str,
    user = Depends(require_roles(['user','learner'], [user_collection, profile_collection]))
):
    if user['role'] == 'user':
        user = await profile_collection.find_one({'owner_id': user['id'],'role':'user'})
        user['id'] = str(user['_id'])
    
    module = await module_collection.find_one({'_id': ObjectId(module_id)})


    