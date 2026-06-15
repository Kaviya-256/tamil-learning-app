from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException

def validate_object_id(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format")