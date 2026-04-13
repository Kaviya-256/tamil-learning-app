from database.mongo import lesson_collection

async def calculate_progress(count: int):
    lesson_count =await lesson_collection.count_documents({})
    print(lesson_count)
    print('count',count)

    progress =int( count / lesson_count * 100 )
    print(progress)

    return progress