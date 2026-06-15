from fastapi import APIRouter, Depends, HTTPException
from bson.errors import InvalidId
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from utils.role_auth import require_roles
from database.mongo import user_collection, profile_collection
from games.service.games_service import GamesService
from database.db_dependency import get_game_service
from games.schema import GameRoundSchema

router = APIRouter(tags=["Game Section"])


@router.get('/api/lesson/{module_id}/{game_id}')
async def create_user_game_session(
    module_id: str, game_id: str,
    service: GamesService = Depends(get_game_service),
    user = Depends(require_roles(['user', 'admin', 'learner'], [user_collection, profile_collection]))
):
    
    if user.get('role') == 'user':
        user = await profile_collection.find_one({'owner_id': user.get('id'), 'role': 'user'})
        if not user:
            raise HTTPException(status_code=404, detail="Profile not found")
        user['id'] = str(user['_id'])

    return await service.create_game_user_session(user.get('id'), module_id, game_id)


@router.post('/api/lesson/{module_id}/{game_id}/round')
async def game_round_detail(
    module_id: str, game_id: str,
    game_round: GameRoundSchema,
    service: GamesService = Depends(get_game_service),
    user = Depends(require_roles(['user', 'learner', 'admin'], [user_collection, profile_collection]))
):
    
    if user.get('role') == 'user':
        user = await profile_collection.find_one({'owner_id': user.get('id'), 'role': 'user'})
        if not user:
            raise HTTPException(status_code=404, detail="Profile not found")
        user['id'] = str(user['_id'])
    
    game_round = game_round.model_dump()

    return await service.game_round_detail(user.get('id'), module_id, game_id, game_round)

@router.get('/api/lesson/{module_id}/{game_id}/result')
async def game_result(
    module_id: str, game_id: str,
    service: GamesService = Depends(get_game_service),
    user = Depends(require_roles(['user', 'learner', 'admin'], [user_collection, profile_collection]))
):
    
    if user.get('role') == 'user':
        user = await profile_collection.find_one({'owner_id': user.get('id'), 'role': 'user'})
        if not user:
            raise HTTPException(status_code=404, detail="Profile not found")
        user['id'] = str(user['_id'])

    return await service.game_result(user.get('id'), module_id, game_id)