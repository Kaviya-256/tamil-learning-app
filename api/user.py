from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from datetime import datetime, timezone
from bson.errors import InvalidId

from schema import LearnerSchema, ProfileSchema
from database.mongo import profile_collection, user_collection
from utils.role_auth import require_roles
from utils.auth_utils import hash_password


router = APIRouter()


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
    result= await profile_collection.insert_one(data)
    if not result:
        raise HTTPException(status_code=500, detail="Adding learner failed")
    
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
        async for doc in profile_collection.find({'owner_id': user_id, 'role': 'learner'})
    ]

# getting specific learner details
@router.get('/api/user/learner/{learner_id}')
async def get_learner(
    learner_id: str,
    user = Depends(require_roles(['user'], [user_collection]))
):
    
    try:
        id = ObjectId(learner_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    data = await profile_collection.find_one({'_id': id, 'owner_id': user['id']})

    if data is None:
        raise HTTPException(status_code=404, detail="User not found")
    
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
    
    try:
        id = ObjectId(learner_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    update_data = {
        'name': learner.name,
        'age': learner.age,
        'grade': learner.grade
    }
    if learner.password:
        update_data['password'] = hash_password(learner.password)
    
    result = await profile_collection.find_one_and_update(
        {'_id': id, 'owner_id': user['id']},
        {
            '$set': update_data
        }
    )
    if not result:
        raise HTTPException(status_code=404, detail="Learner not found")
    
    return {'message': 'Profile updated'}

# deleting a learner
@router.delete('/api/user/learner/{learner_id}/delete-learner')
async def delete_learner(
    learner_id: str,
    user = Depends(require_roles(['user'], [user_collection]))   
):
    
    try:
        id = ObjectId(learner_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    result = await profile_collection.delete_one(
        {'_id': id, 'owner_id': user['id']}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Learner not found")
    
    return {'message': 'learner deleted'}

# User Profile Data
@router.get('/api/user/profile')
async def get_profile(user = Depends(require_roles(['user'], [user_collection]))):

    try:
        id = ObjectId(user['id'])
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    profile = await user_collection.find_one({'_id': id})
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
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

    try:
        id = ObjectId(user['id'])
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    result = await user_collection.update_one(
        {'_id': id},
        {
            '$set': profile.model_dump()
        }
    )
    if result.matched_count==0:
        raise HTTPException(status_code=404, detail="User not found")
    
    if result.modified_count == 0:
        return{'message': 'No changes made'}

    return {'message': 'Profile updated'}

