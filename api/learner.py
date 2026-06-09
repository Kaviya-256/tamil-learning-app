from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from utils.role_auth import require_roles
from database.mongo import profile_collection
from schema import ThemeColorEnum

router = APIRouter()

# get learner info
@router.get('/api/learner/profile')
async def get_learner_profile(learner = Depends(require_roles(['learner'], [profile_collection]))):

    learner_id = learner.get('id')
    data = await profile_collection.find_one({'_id': ObjectId(learner_id)})

    if not data:
        raise HTTPException(status_code=404, detail="Learner not found")

    learner = {
        'username': data.get('username'),
        'name': data.get('name'),
        'age': data.get('age'),
        'grade': data.get('grade'),
        'theme_color': getattr(ThemeColorEnum.__members__.get(data.get('theme_color')), 'value', None)
    }
    
    return learner