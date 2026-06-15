from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException
from datetime import datetime, timezone

from utils.game_utils import validate_object_id


class GamesService:
    def __init__(
        self,
        profile_col: AsyncIOMotorCollection,
        game_session_col: AsyncIOMotorCollection,
        game_col: AsyncIOMotorCollection,
        user_game_attempt_col: AsyncIOMotorCollection
    ):
        self.profile_col = profile_col
        self.game_session_col = game_session_col
        self.game_col = game_col
        self.user_game_attempt_col = user_game_attempt_col


    # 1. creating session for user game at start
    async def create_game_user_session(self, profile_id: str, module_id: str, game_id: str):
        

        profile_id = validate_object_id(profile_id)
        module_id = validate_object_id(module_id)
        game_id = validate_object_id(game_id)
        
        game = await self.game_col.find_one({'_id': game_id})
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        
        session_data = {
            'profile_id': profile_id,
            'lesson_id': 5,
            'module_id': module_id,
            'game_id': game_id,
            'started_at': datetime.now(timezone.utc),
            'status_completed': False,
            'total_rounds': game.get('total_rounds'),
            'completed_rounds': 0,
            'earned_score': 0,
            'total_score': game.get('total_score')
        }
        
        result = await self.game_session_col.insert_one(session_data)

        return {'message': 'Session created'}
    
    # 2. Game round details
    async def game_round_detail(self, profile_id: str, module_id: str, game_id: str, game_round: dict):

        profile_id = validate_object_id(profile_id)
        module_id = validate_object_id(module_id)
        game_id = validate_object_id(game_id)
        
        game = await self.game_col.find_one({'_id': game_id})
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        
        attempt = game_round.get('attempt_no')
        max_score = score = game.get('each_round_score')

        if attempt == 1:
            score = max_score
        elif attempt == 2:
            score = max_score - 5
        elif attempt == 3:
            score = max_score - 10
        else:
            score = max_score - 15
        

        round_data = {
            'profile_id': profile_id,
            'session_id': ObjectId(game_round.get('session_id')),
            'module_id': module_id,
            'game_id': game_id,
            'round_no': game_round.get('round_no'),
            'attempt_no': game_round.get('attempt_no'),
            'is_correct': True,
            'maximun_score': max_score,
            'achieved_score': score,
            'response_time_ms': game_round.get('response_time_ms'),
            'created_at': datetime.now(timezone.utc)
        }

        result = await self.user_game_attempt_col.insert_one(round_data)

        await self.game_session_col.find_one_and_update(
            {'_id': ObjectId(game_round.get('session_id'))},
            {
                '$inc': {'completed_rounds': 1, 'earned_score': score}
            }
        )

        if game_round.get('round_no') == game.get('total_rounds'):
            await self.game_session_col.find_one_and_update(
                {'_id': ObjectId(game_round.get('session_id'))},
                {
                    '$set': {'status_completed': True, 'completed_at': datetime.now(timezone.utc)}
                }
            )

        return {'message': "Round data stored"}
    
    # 3. Game results
    async def game_result(self, profile_id: str, module_id: str, game_id: str):
        try:
            profile_id = ObjectId(profile_id)
            module_id = ObjectId(module_id)
            game_id = ObjectId(game_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid ID format")
        
        game = await self.game_col.find_one({'_id': game_id})
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        
        data = await self.game_session_col.find_one(
            {
                'profile_id': profile_id,
                'module_id': module_id,
                'game_id': game_id,
                'status_completed': True
            },
            {'_id':0, 'earned_score':1}
        )
        if data is None:
            raise HTTPException(status_code=404, detail="Not found")
        
        return data