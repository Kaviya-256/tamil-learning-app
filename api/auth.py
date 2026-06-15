# auth.py
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timedelta, timezone
from random import randint
import os
from bson import ObjectId
from bson.errors import InvalidId

from database.mongo import user_collection, profile_collection, otp_collection, feedback_collection
from schema import SignupSchema, LoginSchema, EmailSchema, VerifyOTPSchema, ResetPasswordSchema, ChangePasswordSchema, ContactAdminSchema
from utils.auth_utils import hash_password, verify_password
from jwt_auth import create_access_token, create_refresh_token
from utils.role_auth import refresh_access_token
from utils.verifyEmail import VerifyEmail, ForgetPassword, ContactAdminMail
from utils.role_auth import require_roles
from database.db_dependency import get_country_collection

router = APIRouter()

#signup or user registration
@router.post('/api/signup')
async def signup_user(user: SignupSchema):
   
    existing_user = await user_collection.find_one({'email': user.email})
    if existing_user:
        if existing_user.get('disabled'):
            raise HTTPException(status_code=403, detail="User not allowed")
        
        elif existing_user.get('deleted'):
            user_info = user.model_dump()
            del user_info['passwordConfirm']

            user_info.update({
                "verified": False,
                "updated_at": datetime.now(timezone.utc),
                "password": hash_password(user.password),
                'deleted': False
            })
            result = await user_collection.update_one(
                {'email': user.email},
                {'$set': user_info}
            )
            await profile_collection.update_many(
                {'owner_id': str(existing_user['_id'])},
                {'$set': {'deleted': False}}
            )
            return {'status': 'Success!'}
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail = "Email is already registered"
            )
        
    if user.age < 18:
        raise HTTPException(status_code=403, detail="Registration is not available for users under 18 years of age.")
    
    if user.password != user.passwordConfirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password doesn't match"
        )
    
    
    user_info = user.model_dump()
    del user_info['passwordConfirm']

    user_info.update({
        "role": "user",
        "verified": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "password": hash_password(user.password),
        'disabled': False,
        'deleted': False
    })
    result = await user_collection.insert_one(user_info)

    profile_data = {
        'owner_id': str(result.inserted_id),
        'name': user.name,
        'email': user.email,
        'role': 'user',
        'progress': 0,
        'lessons_attended': [],
        'disabled': False,
        'deleted': False
    }
    await profile_collection.insert_one(profile_data)
    return {'status': 'Success!'}


# user login
@router.post('/api/login')
async def login_user(user: LoginSchema):
    db_user = None
    
    if user.email:
        db_user = await user_collection.find_one({'email': user.email})
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        if db_user['verified'] == False:
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail="Verify email first"
            )
    elif user.username:
        db_user = await profile_collection.find_one({'username': user.username})
        if db_user is None:
            raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Learner not found"
                )
    
    if db_user.get('disabled'):
            raise HTTPException(status_code=403, detail="User not allowed")
    
    if db_user.get('deleted'):
        raise HTTPException(status_code=404, detail="User not found. Please signup")

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
        'role': db_user.get('role'),
        'name': db_user.get('name')
    }

@router.post('/api/send-otp-signup')
async def verify_email(otp_data: EmailSchema):

    existing_user = await user_collection.find_one({'email': otp_data.email})

    if not existing_user:        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "User not registered"
        )
    if existing_user.get('verified') is True:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
    
    code = str(randint(100000,999999))
    
    result = await otp_collection.update_one(
        {'email': otp_data.email},
        {
            '$set': {
                'otp': code,
                'expires_at': datetime.now(timezone.utc) + timedelta(minutes=int(os.getenv('OTP_EXPIRE_TIME') or 5)),
                'otp_verified': False
            }
        },
        upsert=True
    )

    #send email
    email_service = VerifyEmail(name=existing_user.get('name'), code=code, email=[otp_data.email])
    
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
            status_code=status.HTTP_404_NOT_FOUND,
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
    
    if record.get('disabled'):
            raise HTTPException(status_code=403, detail="User not allowed")
    
    if record.get('deleted'):
        raise HTTPException(status_code=404, detail="User not found. Please signup")
    
    code = str(randint(100000,999999))
    result = await otp_collection.update_one(
        {'email': otp_data.email},
        {
            '$set': {
                'otp': code,
                'expires_at': datetime.now(timezone.utc)+timedelta(minutes=int(os.getenv('OTP_EXPIRE_TIME') or 5)),
                'otp_verified': False
            }
        },
        upsert=True
    )

    #send email
    email_service = ForgetPassword(name=record.get('name'), code=code, email=[otp_data.email])
    await email_service.sendVerificationCode()

    return {'message': "OTP sent successfully"}


@router.post('/api/reset-password')
async def reset_password(pwd: ResetPasswordSchema):

    user = await user_collection.find_one({'email': pwd.email})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if user.get('disabled'):
            raise HTTPException(status_code=403, detail="User not allowed")
    
    if user.get('deleted'):
        raise HTTPException(status_code=404, detail="User not found. Please signup")
    
    otp = await otp_collection.find_one({'email': pwd.email})
    if otp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="otp not found"
        )
    
    if otp['otp_verified'] is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP not verified"
        )

    if pwd.password != pwd.passwordConfirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not match"
        )
    if verify_password(pwd.password, user['password']):
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
    
# Public Feedback
@router.get('/api/feedback/public')
async def verified_feedback():

    feedback = await feedback_collection.find({'admin_approved': True}, {'_id':0, 'name':1, 'rating': 1, 'comments':1}).to_list()
    return feedback


# Contact Admin
@router.post('/api/contact-admin')
async def contact_admin(contact: ContactAdminSchema):

    mail = ContactAdminMail(contact)
    await mail.sendMailtoAdmin()

    return {'message': "Message sent successfully"}


# User and admin Password Reset
@router.patch('/api/change-password')
async def change_password(pwd: ChangePasswordSchema, user = Depends(require_roles(['user', 'admin'], [user_collection]))):

    try:
        id = ObjectId(user['id'])
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    data = await user_collection.find_one({'_id': id})

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if data.get('disabled'):
            raise HTTPException(status_code=403, detail="User not allowed")
    
    if data.get('deleted'):
        raise HTTPException(status_code=404, detail="User not found. Please signup")
    
    if not verify_password(pwd.currentPassword, data['password']):
        raise HTTPException(
            status_code=400, detail="Wrong current password"
        )
    
    if pwd.newPassword != pwd.passwordConfirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not match"
        )
    
    if verify_password(pwd.newPassword, data['password']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password does not equal to old one"
        )
    result = await user_collection.update_one(
        {'_id': id},
        {
            '$set': {'password': hash_password(pwd.newPassword)}
        }
    )

    if result.matched_count ==0:
        return{'message': 'No changes made'}
    
    return {'message': 'Password updated'}

@router.get('/api/country')
async def get_countries(countries_col = Depends(get_country_collection)):
    return [
        {'country_name': doc.get('country_name')}
        async for doc in countries_col.find()
    ]


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
