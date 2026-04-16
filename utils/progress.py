from database.mongo import module_collection

async def calculate_progress(count: int):
    module_count =await module_collection.count_documents({})

    if module_count==0:
        return 0

    return int( count / module_count * 100 )