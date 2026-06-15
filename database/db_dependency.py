from motor.motor_asyncio import AsyncIOMotorCollection
from fastapi import Depends

from database.mongo import game_collection, lesson_collection, module_game_map_collection, module_collection, user_collection, profile_collection, game_session_collection, user_round_attempts_collection, country_collection
from games.service.admin_game_service import AdminGameService
from games.service.games_service import GamesService

def get_user_collection() -> AsyncIOMotorCollection:
    return user_collection

def get_profile_collection() -> AsyncIOMotorCollection:
    return profile_collection

def get_lessons_collection() -> AsyncIOMotorCollection:
    return lesson_collection

def get_module_collection() -> AsyncIOMotorCollection:
    return module_collection

def get_games_collection() -> AsyncIOMotorCollection:
    return game_collection

def get_module_game_map_collection() -> AsyncIOMotorCollection:
    return module_game_map_collection

def get_game_session_collection() -> AsyncIOMotorCollection:
    return game_session_collection

def get_user_round_attempts_col() -> AsyncIOMotorCollection:
     return user_round_attempts_collection

def get_admin_game_service(
    game_col: AsyncIOMotorCollection = Depends(get_games_collection),
    lesson_col: AsyncIOMotorCollection = Depends(get_lessons_collection),
    module_game_map_col: AsyncIOMotorCollection = Depends(get_module_game_map_collection),
    module_col: AsyncIOMotorCollection = Depends(get_module_collection)
) -> AdminGameService:
        return AdminGameService(game_col, lesson_col, module_game_map_col, module_col)


def get_game_service(
    profile_col: AsyncIOMotorCollection = Depends(get_profile_collection),
    game_session_col: AsyncIOMotorCollection = Depends(get_game_session_collection),
    game_col: AsyncIOMotorCollection = Depends(get_games_collection),
    user_round_attempt_col: AsyncIOMotorCollection = Depends(get_user_round_attempts_col)

) -> GamesService:
        return GamesService(profile_col, game_session_col, game_col, user_round_attempt_col)

def get_country_collection() -> AsyncIOMotorCollection:
     return country_collection