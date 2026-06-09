# schema.py
from pydantic import BaseModel, EmailStr, model_validator, field_validator, Field
from typing import Optional
import re
from enum import Enum


class LoginSchema(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str

    @model_validator(mode='after')
    def check_one_field(cls, values):
        if not values.email and not values.username:
            raise ValueError("Either email or username must be provided")
        if values.email and values.username:
            raise ValueError("Provide only email OR username, not both")
        return values

class EmailSchema(BaseModel):
    email: EmailStr

class VerifyOTPSchema(EmailSchema):
    otp: str

class SignupSchema(BaseModel):
    name: str
    email: EmailStr
    password: str
    passwordConfirm: str
    country: str
    age: int = Field(..., ge=1, le=100)

    @field_validator('password')
    @classmethod
    def validate_password(cls, pwd):
        if len(pwd) < 6:
            raise ValueError("Password must be atleast 6 characters long")
        if not re.search(r'\d', pwd):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', pwd):
            raise ValueError('Password must contain at least one special symbol')
        if not re.search(r'[a-z]', pwd):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'[A-Z]', pwd):
            raise ValueError('Password must contain at least one uppercase letter')
        return pwd
    
    @field_validator('passwordConfirm')
    @classmethod
    def password_match(cls, v, values):
        if 'password' in values.data and v != values.data['password']:
            raise ValueError('Passwords do not match')
        return v
    

class ResetPasswordSchema(EmailSchema):
    password: str
    passwordConfirm: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, pwd):
        if len(pwd) < 6:
            raise ValueError("Password must be atleast 6 characters long")
        if not re.search(r'\d', pwd):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', pwd):
            raise ValueError('Password must contain at least one special symbol')
        if not re.search(r'[a-z]', pwd):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'[A-Z]', pwd):
            raise ValueError('Password must contain at least one uppercase letter')
        return pwd
    
    @field_validator('passwordConfirm')
    @classmethod
    def password_match(cls, v, values):
        if 'password' in values.data and v != values.data['password']:
            raise ValueError('Passwords do not match')
        return v


class ThemeColorEnum(str, Enum):
    pink_rose = "from-pink-400 to-rose-500"
    violet_purple = "from-violet-400 to-purple-500"
    emerald_teal = "from-emerald-400 to-teal-500"
    amber_orange = "from-amber-400 to-orange-500"
    sky_blue = "from-sky-400 to-blue-500"
    fuchsia_pink = "from-fuchsia-400 to-pink-500"

class LearnerSchema(BaseModel):
    username: str
    name: str
    age: int = Field(..., ge=1, le=100)
    grade: str
    password: str
    theme_color: ThemeColorEnum

    @field_validator('username')
    @classmethod
    def validate_username(cls, value):
        if not re.match(r'^[a-zA-Z0-9_]+$',value):
            raise ValueError(
                "Username only contain letters, numbers and underscore"
            )
        return value
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, pwd):
        if len(pwd) < 6:
            raise ValueError("Password must be atleast 6 characters long")
        if not re.search(r'\d', pwd):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', pwd):
            raise ValueError('Password must contain at least one special symbol')
        if not re.search(r'[a-z]', pwd):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'[A-Z]', pwd):
            raise ValueError('Password must contain at least one uppercase letter')
        return pwd
    
    
class LearnerUpdateSchema(BaseModel):
    name: str
    age: int = Field(..., ge=1, le=100)
    grade: str
    password: Optional[str] = None
    theme_color: ThemeColorEnum

    @field_validator('password')
    @classmethod
    def validate_password(cls, pwd):
        if pwd is None:
            return pwd
        if len(pwd) < 6:
            raise ValueError("Password must be atleast 6 characters long")
        if not re.search(r'\d', pwd):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', pwd):
            raise ValueError('Password must contain at least one special symbol')
        if not re.search(r'[a-z]', pwd):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'[A-Z]', pwd):
            raise ValueError('Password must contain at least one uppercase letter')
        return pwd


class LessonSchema(BaseModel):
    lesson_name: str

class ModuleSchema(BaseModel):
    module_name: str

class FeedbackSchema(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = None

class ProfileSchema(BaseModel):
    name: str
    city: str
    state: str
    country: str
    age: int = Field(..., ge=18, le=100)

class ChangePasswordSchema(BaseModel):
    currentPassword: str
    newPassword: str
    passwordConfirm: str

    @field_validator('newPassword')
    @classmethod
    def validate_password(cls, pwd):
        if len(pwd) < 6:
            raise ValueError("Password must be atleast 6 characters long")
        if not re.search(r'\d', pwd):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', pwd):
            raise ValueError('Password must contain at least one special symbol')
        if not re.search(r'[a-z]', pwd):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'[A-Z]', pwd):
            raise ValueError('Password must contain at least one uppercase letter')
        return pwd
    
    @field_validator('passwordConfirm')
    @classmethod
    def password_match(cls, v, values):
        if 'newPassword' in values.data and v != values.data['newPassword']:
            raise ValueError('Passwords do not match')
        return v
    
class ContactAdminSchema(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str