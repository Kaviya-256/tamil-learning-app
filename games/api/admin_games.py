from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from bson.errors import InvalidId

from utils.role_auth import require_roles
from database.db_dependency import get_games_collection, get_lessons_collection, get_module_game_map_collection
from database.mongo import user_collection
from games.service.admin_game_service import AdminGameService
from database.db_dependency import get_admin_game_service

router = APIRouter(tags=["Admin Game Management"])


# 1. List all games to admin
@router.get('/api/admin/games')
async def get_games(
    # game_collection: AsyncIOMotorCollection = Depends(get_games_collection),
    admin = Depends(require_roles(['admin'], [user_collection])),
    service: AdminGameService = Depends(get_admin_game_service)
):

    return await service.get_games()


# 2. Add game to lesson
@router.post('/api/admin/lesson/{lesson_id}/add-game/{game_id}')
async def add_game_to_lesson(
    lesson_id: str,
    game_id: str,
    service: AdminGameService = Depends(get_admin_game_service),
    admin = Depends(require_roles(['admin'], [user_collection]))
):
    
    return await service.add_game_to_lesson(lesson_id, game_id)


# 3. Get list of games for the lesson
@router.get('/api/admin/lesson/{lesson_id}/games')
async def lesson_games(
    lesson_id: str,
    service: AdminGameService = Depends(get_admin_game_service),
    admin = Depends(require_roles(['admin'], [user_collection]))
):
    
    return await service.lesson_games(lesson_id)