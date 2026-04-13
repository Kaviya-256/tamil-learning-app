#role_auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import os
from dotenv import load_dotenv
from bson import ObjectId
from typing import List

from database.mongo import user_collection, profile_collection

load_dotenv()

security = HTTPBearer()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')

# async def get_current_user(token: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    
#     token=token.credentials
#     try:
#         payload= jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         if payload.get('role') != 'user':
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail='Access denied'
#             )
#         if payload.get('type') != 'access':
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Invalid Token type"
#             )
#         user_id = payload.get('sub')

#         if user_id is None:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="User not found"
#             )

#         user =await user_collection.find_one({'_id': ObjectId(user_id)})
#         if user is None:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="User is not found"
#             )
#         print('one')
#         return { 'user_id':str(user['_id']), 'role': user['role']}
    
#     except ExpiredSignatureError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token expired"
#         )
        
#     except InvalidTokenError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail='Could not validate credentials'
#     )
    

# async def get_current_admin(token: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
#     # if user.get('role') != 'admin':
#     #     raise HTTPException(
#     #         status_code=status.HTTP_403_FORBIDDEN,
#     #         detail="Admin access required"
#     #     )
#     # return user
#     token=token.credentials
#     try:
#         payload= jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         if payload.get('role') != 'admin':
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail='Access denied'
#             )
#         if payload.get('type') != 'access':
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Invalid Token type"
#             )
#         admin_id = payload.get('sub')

#         if admin_id is None:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Admin not found"
#             )

#         admin =await user_collection.find_one({'_id': ObjectId(admin_id)})
#         if admin is None:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="User is not found"
#             )
#         return { 'admin_id':str(admin['_id']), 'role': admin['role']}
    
#     except ExpiredSignatureError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token expired"
#         )
        
#     except InvalidTokenError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail='Could not validate credentials'
#     )
    

# # learner authorization
# async def get_current_learner(token: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
#     print('helloworld')
#     token=token.credentials
#     try:
#         print('hw')
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         print('one')
#         if payload.get('role') != 'learner':
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail='Access denied'
#             )
#         if payload.get('type') != 'access':
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Invalid Token type"
#             )
        
#         print('two')
#         learner_id = payload.get('sub')
#         print('3')

#         if learner_id is None:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Learner not found"
#             )
#         print('4')

#         learner =await profile_collection.find_one({'_id': ObjectId(learner_id)})
#         print('5')
#         if learner is None:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="learner is not found"
#             )
#         print('6')
#         return { 'learner_id':str(learner['_id']), 'role': learner['role']}
    
#     except ExpiredSignatureError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token expired"
#         )
        
#     except InvalidTokenError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail='Could not validate credentials'
#     )

async def refresh_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get('type') != 'refresh':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Token type"
            )
        user_id = payload.get('sub')

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        user =await get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is not found"
            )
        # user['_id'] = str(user['_id'])
        # del user['_id']
        return user
    
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token'
    )

# User authorization
async def get_current_user_with_roles(
        token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
        allowed_roles: List[str],
        collections: List
):
    token=token.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get('type') != 'access':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token type"
            )
        user_id = payload.get('sub')

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        try:
            obj_id = ObjectId(user_id)
        except:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID"
            )
        user=None
        for collection in collections:
            user = await collection.find_one({'_id': obj_id})
            if user:
                break
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if user.get('role') not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return { 'id':str(user['_id']),'name': user['name'], 'role': user['role']}
    
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token"
        )
    
def require_roles(allowed_roles: List[str], collections: List):
    async def dependency(
        token: Annotated[HTTPAuthorizationCredentials, Depends(security)]
    ):
        return await get_current_user_with_roles(token, allowed_roles, collections)
    return dependency
