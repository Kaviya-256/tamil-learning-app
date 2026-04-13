from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from datetime import datetime, timezone, timedelta
from fastapi.security import HTTPBearer

from schema import LearnerSchema
from database.mongo import profile_collection, lesson_collection, user_collection
from utils.role_auth import require_roles
from utils.auth_utils import hash_password


router = APIRouter()
security = HTTPBearer()


# @router.get('/api/user')
# async def get_user(user: dict =Depends(get_current_user)):
    
#     # try:        
#     #     user_id = ObjectId(user['user_id'])
#     # except Exception:
#     #     raise HTTPException(
#     #         status_code=status.HTTP_400_BAD_REQUEST,
#     #         detail='Invalid user id'
#     #     )
#     # result = await profile_collection.find_one({'owner_id': user['user_id'], 'role': 'user'})
#     # if result is None:
#     #     raise HTTPException(
#     #         status_code=status.HTTP_404_NOT_FOUND,
#     #         detail="User not found"
#     #     )
#     # print('six')
#     # return {
#     #     'name': result.get('name'),
#     #     'progress': result.get('progress')
#     # }
#     user = await profile_collection.find_one({'owner_id': user['user_id']})
#     if user is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Learner not found"
#         )

#     lessons=[]
#     async for doc in lesson_collection.find():
#         lessons.append({
#             'lesson_id': str(doc['_id']),
#             'lessons': doc.get('lesson_name'),
#             'modules_count': doc.get('modules_count'),
#             # 'message': 'hello'
#         })
#     return {
#         'name': user.get('name'),
#         'progress': user.get('progress'),
#         'lessons': lessons
#     }

# adding learner
@router.post('/api/user/add-learner')
async def add_learner(
    learner: LearnerSchema,
    user = Depends(require_roles(['user'], [user_collection]))
):
    user_id = user['id']

    existing_learner = await profile_collection.find_one(
        {'username': learner.username}
    )
    if existing_learner:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Learner with the username already exist"
        )

    data = {
        'username': learner.username,
        'name': learner.name,
        'age': learner.age,
        'grade': learner.grade,
        'owner_id': user_id,
        'role': 'learner',
        'progress': 0,
        'lessons_attended': [],
        'password': hash_password(learner.password),
        'created_at': datetime.now(timezone.utc)
    }
    await profile_collection.insert_one(data)
    return {
        'message': f'Learner created for owner {user_id}'
    }

# getting learners list
@router.get('/api/user/learners')
async def learners_list(user = Depends(require_roles(['user'], [user_collection]))):
    
    user_id = user['id']
    return [
        {
            'id': str(doc['_id']),
            'username': doc.get('username'),
            'name': doc.get('name'),
            'age': doc.get('age'), 
            'progress': doc.get('progress')
        }
        async for doc in profile_collection.find({'owner_id': user_id})
        if doc.get('role') != 'user'
    ]

# getting specific learner details
@router.get('/api/user/learner/{learner_id}')
async def get_learner(
    learner_id: str,
    user = Depends(require_roles(['user'], [user_collection]))
):
    
    data = await profile_collection.find_one({'_id': ObjectId(learner_id)})
    return {
        'username': data['username'],
        'name': data['name'],
        'age': data['age'],
        'progress': data['progress']
    }

# editing a learner
@router.put('/api/user/learner/{learner_id}/edit')
async def edit_learner(
    learner: LearnerSchema,learner_id: str,
    user = Depends(require_roles(['user'], [user_collection]))
):
    
    result = await profile_collection.find_one_and_update(
        {'_id': ObjectId(learner_id)},
        {
            '$set': {
                'name': learner.name,
                'age': learner.age,
                'grade': learner.grade,
                'password': hash_password(learner.password)
            }
        }
    )
    return {'message': 'Profile updated'}

# deleting a learner
@router.delete('/api/user/learner/{learner_id}/delete-learner')
async def delete_learner(
    learner_id: str,
    user = Depends(require_roles(['user'], [user_collection]))   
):
    
    await profile_collection.delete_one(
        {'_id': ObjectId(learner_id)}
    )
    return {'message': 'learner deleted'}


# # User learning code 
# @router.get('/api/learner/{lesson_id}')
# async def get_lesson(lesson_id: str, learner: dict = Depends(get_current_learner)):
#     lesson = await lesson_collection.find_one({'_id': ObjectId(lesson_id)})

#     result = await profile_collection.find_one_and_update(
#         {'_id': ObjectId(learner['learner_id'])},
#         {
#             '$addToSet': {'lessons_attended': lesson['lesson_name']}
#         }
#     )
#     print(str(result['_id']))
#     progress = await calculate_progress(len(result['lessons_attended'])-1)

#     await profile_collection.update_one(
#         {'_id': ObjectId(learner['learner_id'])},
#         {
#             '$set': {'progress': progress}
#         }
#     )
#     print('hello')

#     return {
#         'lessons': lesson['lesson_name'],
#         # 'attended by the user': learner.get('lessons_attended')
#     }