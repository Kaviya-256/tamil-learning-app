# from fastapi import APIRouter, Depends, HTTPException, status
# from bson import ObjectId

# from utils.role_auth import get_current_learner
# from database.mongo import lesson_collection, profile_collection
# from utils.progress import calculate_progress

# router= APIRouter()

# @router.get('/api/learner')
# async def learner_dashboard(learner: dict = Depends(get_current_learner)):
    
#     learner = await profile_collection.find_one({'_id': ObjectId(learner['learner_id'])})
#     if learner is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Learner not found"
#         )

#     lessons=[]
#     async for doc in lesson_collection.find():
#         lessons.append({
#             'lesson_id': str(doc['_id']),
#             'lessons': doc.get('lesson_name'),
#             # 'modules_count': doc.get('modules_count'),
#         })
#     return {
#         'name': learner.get('name'),
#         'progress': learner.get('progress'),
#         'lessons': lessons
#     }


# @router.get('/api/learner/{lesson_id}')
# async def get_lesson(lesson_id: str, learner: dict = Depends(get_current_learner)):
#     lesson = await lesson_collection.find_one({'_id': ObjectId(lesson_id)})

#     result = await profile_collection.find_one_and_update(
#         {'_id': ObjectId(learner['learner_id'])},
#         {
#             '$addToSet': {'lessons_attended': lesson['lesson_name']}
#         }
#     )
#     print(str(result['_id']))
#     progress = await calculate_progress(len(result['lessons_attended'])-1)

#     await profile_collection.update_one(
#         {'_id': ObjectId(learner['learner_id'])},
#         {
#             '$set': {'progress': progress}
#         }
#     )
#     print('hello')

#     return {
#         'lessons': lesson['lesson_name'],
#         # 'attended by the user': learner.get('lessons_attended')
#     }