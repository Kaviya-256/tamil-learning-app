from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from datetime import datetime, timezone
from fastapi.security import HTTPBearer

from schema import LearnerSchema, ProfileSchema
from database.mongo import profile_collection, user_collection
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
            'grade': doc.get('grade'),
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
        'grade': data['grade'],
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

# User Profile Data
@router.get('/api/user/profile')
async def get_profile(user = Depends(require_roles(['user'], [user_collection]))):
    profile = await user_collection.find_one({'_id': ObjectId(user['id'])})
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not exist"
        )
    return {
        'name': profile.get('name'),
        'city': profile.get('city'),
        'state': profile.get('state'),
        'country': profile.get('country'),
        'valid_age': profile.get('valid_age')
    }

# User profile management
@router.post('/api/user/profile-update')
async def manage_profile(profile: ProfileSchema, user = Depends(require_roles(['user'], [user_collection]))):
    user_data = await user_collection.find_one({'_id': ObjectId(user['id'])})

    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await user_collection.update_one(
        {'_id': ObjectId(user['id'])},
        {
            '$set': profile.model_dump()
        }
    )

    return {'message': 'Profile updated'}

