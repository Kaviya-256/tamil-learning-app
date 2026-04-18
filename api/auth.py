# auth.py
from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta, timezone
from random import randint

from database.mongo import user_collection, profile_collection, otp_collection
from schema import *
from utils.auth_utils import hash_password, verify_password
from jwt_auth import create_access_token, create_refresh_token
from utils.role_auth import refresh_access_token
from utils.verifyEmail import VerifyEmail, ForgetPassword

router = APIRouter()

#signup or user registration
@router.post('/api/signup')
async def signup_user(user: SignupSchema):
   
    existing_user = await user_collection.find_one({'email': user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail = "Email is already registered"
        )
    
    
    if user.password != user.passwordConfirm:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password doesn't match"
        )
    
    
    user_info = user.model_dump()
    del user_info['passwordConfirm']

    user_info.update({
        "role": "user",
        "verified": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "password": hash_password(user.password)
    })
    result = await user_collection.insert_one(user_info)

    profile_data = {
        'owner_id': str(result.inserted_id),
        'name': user.name,
        'email': user.email,
        'role': 'user',
        'progress': 0,
        'lessons_attended': []
    }
    await profile_collection.insert_one(profile_data)
    return {'status': 'Success!'}


# user login
@router.post('/api/login')
async def login_user(user: LoginSchema):
    db_user = None
    
    if user.email:
        db_user = await user_collection.find_one({'email': user.email})
    elif user.username:
        db_user = await profile_collection.find_one({'username': user.username})

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    if not verify_password(user.password, db_user['password']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    access_token = create_access_token(
        data={'user_id': str(db_user['_id']),
        'role': db_user.get('role')}
    )

    refresh_token = create_refresh_token(
        user_id = str(db_user['_id'])
    )

    return{
        'access_token': access_token,
        'refresh_token': refresh_token,
        'role': db_user.get('role')
    }

@router.post('/api/send-otp-signup')
async def verify_email(otp_data: EmailSchema):
    
    code = str(randint(100000,999999))
    
    result = await otp_collection.update_one(
        {'email': otp_data.email},
        {
            '$set': {
                'otp': code,
                'expires_at': datetime.now(timezone.utc) + timedelta(minutes=10),
                'otp_verified': False
            }
        },
        upsert=True
    )

    #send email
    email_service = VerifyEmail(name='User', code=code, email=[otp_data.email])
    
    await email_service.sendVerificationCode()

    return {'message': "OTP sent successfully"}

@router.post('/api/verify-otp')
async def verify_otp(otp_data: VerifyOTPSchema):
    record = await otp_collection.find_one({'email': otp_data.email})

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP not found"
        )
    if record['otp'] != otp_data.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    expiry_time = record['expires_at']
    if expiry_time.tzinfo is None:
        expiry_time = expiry_time.replace(tzinfo=timezone.utc)

    if expiry_time < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired"
        )
    await otp_collection.update_one(
        {'email': otp_data.email},
        {
            '$set': {'otp_verified': True}
        }
    )
    user= await user_collection.find_one({'email': otp_data.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    await user_collection.find_one_and_update(
        {'email': otp_data.email},
        {
            '$set': {'verified': True}
        }
    )
    return {'message': 'Email Verified Successfully!'}

@router.post('/api/send-otp-forgetpassword')
async def verify_email(otp_data: EmailSchema):
    record = await user_collection.find_one({'email': otp_data.email})
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not exist. Please signup"
        )
    code = str(randint(100000,999999))
    result = await otp_collection.update_one(
        {'email': otp_data.email},
        {
            '$set': {
                'otp': code,
                'expires_at': datetime.now(timezone.utc)+timedelta(minutes=5),
                'otp_verified': False
            }
        },
        upsert=True
    )

    #send email
    email_service = ForgetPassword(name='User', code=code, email=[otp_data.email])
    await email_service.sendVerificationCode()

    return {'message': "OTP sent successfully"}


@router.post('/api/reset-password')
async def reset_password(pwd: ResetPasswordSchema):

    user = await user_collection.find_one({'email': pwd.email})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found"
        )

    if pwd.password != pwd.passwordConfirm:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password does not match"
        )
    if pwd.password == user['password']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password does not equal to old one"
        )
    result = await user_collection.find_one_and_update(
        {'email': pwd.email},
        {
            '$set': {'password': hash_password(pwd.password)}
        }
    )

    #auto login
    access_token = create_access_token(
        data={'user_id': str(user['_id']),
        'role': user.get('role')}
    )

    refresh_token = create_refresh_token(
        user_id = str(user['_id'])
    )

    return{
        'access_token': access_token,
        'refresh_token': refresh_token,
        'role': user.get('role')
    }
    
# @router.post('/api/refresh')
# async def validate_refresh_token(token: str):
#     user =await refresh_access_token(token)

#     access_token = create_access_token(
#         data={'user_id': str(user['_id']), 'role': user['role']}
#     )
#     return{
#         'access_token': access_token,
#         'message': 'access token refreshed'
#     }
