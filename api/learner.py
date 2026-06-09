from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from utils.role_auth import require_roles
from database.mongo import profile_collection

router = APIRouter()

# get learner info
@router.get('/api/learner/profile')
async def get_learner_profile(learner = Depends(require_roles(['learner'], [profile_collection]))):

    learner_id = learner.get('id')
    data = await profile_collection.find_one(
        {'_id': ObjectId(learner_id)},
        {'username':1, 'name':1, 'age':1, 'grade':1, 'theme_color':1, '_id':0})
    
    if not data:
        raise HTTPException(status_code=404, detail="Learner not found")
    return data