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
