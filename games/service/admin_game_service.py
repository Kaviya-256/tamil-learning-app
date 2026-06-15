from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection
from fastapi import HTTPException
from pymongo.errors import PyMongoError

from utils.game_utils import validate_object_id

class AdminGameService:
    def __init__(
            self,
            game_col: AsyncIOMotorCollection,
            lesson_col: AsyncIOMotorCollection,
            module_game_map_col: AsyncIOMotorCollection,
            module_col: AsyncIOMotorCollection
        ):
        self.game_col = game_col
        self.lesson_col = lesson_col
        self.module_game_map_col = module_game_map_col
        self.module_col = module_col


    # 1. List all games to admin
    async def get_games(self):
        result = self.game_col.find()
        games=[]

        async for doc in result:
            games.append({
                'game_id': str(doc['_id']),
                'game_name': doc.get('game_name'),
                'total_rounds': doc.get('total_rounds')
            })
    
        return games
    
    # 2. Add game to lesson and each modules
    async def add_game_to_lesson(self, lesson_id: str, game_id: str):
        try:
            lesson_id = ObjectId(lesson_id)
            game_id = ObjectId(game_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid ID format")
    
        lesson = await self.lesson_col.find_one({'_id': lesson_id})

        if lesson is None:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        game = await self.game_col.find_one({'_id': game_id})

        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        
        result = await self.lesson_col.update_one(
            {
                '_id': lesson_id,
                'games': {'$ne': game_id}
            },
            {
                '$addToSet': {'games': game_id},
                '$inc': {'games_count': 1}
            }
        )
        print('1')

        if result.matched_count == 0:
            raise HTTPException(status_code=409, detail="Game already added for this lesson")
        
        try:

            result = self.module_col.find({'lesson_id': lesson_id})
            if result is None:
                raise HTTPException(status_code=404, detail="No module exist for this lesson")

            async for module in result:
                data = await self.module_game_map_col.insert_one({
                    'lesson_id': lesson_id,
                    'module_id': module['_id'],
                    'game_id': game_id
                })
                print(module['module_name'])

        except PyMongoError as e:
            raise HTTPException(status_code=500, detail="Failed to add game to each module")

        return {'message': 'Game added to this lesson'}
    
    # 3. Get list of games for the lesson
    async def lesson_games(self, lesson_id: str):        
        lesson_id = validate_object_id(lesson_id)

        pipeline = [
            {
                '$match': {'_id': lesson_id}
            },
            {
                '$lookup': {
                    'from': 'game_definitions',
                    'localField': 'games',
                    'foreignField': '_id',
                    'as': 'games'
                }
            }
        ]

        lesson = await self.lesson_col.aggregate(pipeline).to_list(1)
        if not lesson:
            return []

        games = []
        for game in lesson[0].get('games',[]):
            games.append({
                'game_id': str(game['_id']),
                'game_code': game.get('game_code'),
                'game_name': game.get('game_name')
            })
        print(games)

        return games


