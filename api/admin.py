# admin.py
from fastapi import APIRouter, HTTPException, Depends

from database.mongo import user_collection, asset_collection, profile_collection, lesson_collection, module_collection, feedback_collection
from utils.role_auth import require_roles
from utils.validation import validate_object_id

router = APIRouter(tags=["Admin User Management"])

# UPLOAD_DIR_IMAGE = 'asset/image'
# UPLOAD_DIR_AUDIO = 'asset/audio'

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
    
    result=user_collection.find({'verified': True, 'disabled': False, 'deleted': False, 'role': 'user'}, {'name':1, 'progress':1, 'role':1})    
    user=[]
    async for doc in result:
            user.append({
                'user_id': str(doc['_id']),
                'name': doc.get('name'),
                'progress': doc.get('progress'),
                'role': doc.get('role')
            })
    return user

# List of Learners
@router.get('/api/admin/{user_id}/learners')
async def get_users_learners(
    user_id: str, 
    admin = Depends(require_roles(['admin'], [user_collection]))
):
    
    id = validate_object_id(user_id)
    
    user = await user_collection.find_one({'_id': id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = profile_collection.find({'owner_id': user_id, 'role': 'learner', 'disabled': False, 'deleted': False})
    learners=[]

    async for doc in result:
            learners.append({
                'learner_id': str(doc['_id']),
                'username': doc.get('username'),
                'name': doc.get('name'),
                'age': doc.get('age'),
                'progress': doc.get('progress'),
                'role': doc.get('role')
            })
            
    return learners


# Getting feedback
@router.get('/api/admin/feedback')
async def get_feedback(admin = Depends(require_roles(['admin'], [user_collection]))):
    feedback=[]

    async for doc in feedback_collection.find({}):
    
        feedback.append({
            'id': str(doc['_id']),
            'name': doc.get('name'),
            'rating': doc.get('rating'),
            'comments': doc.get('comments'),
            'admin_approved': doc.get('admin_approved')
        })
    
    return feedback

# Approve Feedback
@router.put('/api/admin/feedback/approve')
async def approve_feedback(feedback_id: str, admin = Depends(require_roles(['admin'], [user_collection]))):

    id = validate_object_id(feedback_id)
    
    result = await feedback_collection.update_one(
        {'_id': id},
        [{'$set': {'admin_approved': {'$not': '$admin_approved'}}}]
    )
    if result.matched_count==0:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    return {'message': 'Feedback is approved'}


# Disable User and their learner
@router.patch('/api/admin/user/{user_id}/disable')
async def disable_user(user_id: str, admin = Depends(require_roles(['admin'], [user_collection]))):

    id = validate_object_id(user_id)
    
    data=await profile_collection.update_many(
        {'owner_id': user_id},
        {'$set': {'disabled': True}}
    )
    
    result= await user_collection.update_one(
        {'_id': id},
        {'$set': {'disabled': True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {'message': 'Disabled'}


# Disable learner
@router.patch('/api/admin/learner/{learner_id}/disable')
async def disable_learner(learner_id: str, admin = Depends(require_roles(['admin'], [user_collection]))):
    
    id = validate_object_id(learner_id)
    
    result = await profile_collection.update_one(
        {'_id': id},
        {'$set': {'disabled': True}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Learner not found")

    return {'message': 'Learner disabled'}


# Delete User and their learner
@router.delete('/api/admin/user/{user_id}/delete')
async def delete_user(user_id: str, admin = Depends(require_roles(['admin'], [user_collection]))):

    id = validate_object_id(user_id)
    
    data=await profile_collection.update_many(
        {'owner_id': user_id},
        {'$set': {'deleted': True}}
    )
    
    result= await user_collection.update_one(
        {'_id': id},
        {'$set': {'deleted': True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {'message': 'Deleted user'}


# Delete learner
@router.delete('/api/admin/learner/{learner_id}/delete')
async def delete_learner(learner_id: str, admin = Depends(require_roles(['admin'], [user_collection]))):

    id = validate_object_id(learner_id)
    
    result = await profile_collection.update_one(
        {'_id': id},
        {'$set': {'deleted': True}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Learner not found")

    return {'message': 'Learner deleted'}