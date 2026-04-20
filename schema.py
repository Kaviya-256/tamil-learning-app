# schema.py
from pydantic import BaseModel, EmailStr, model_validator, field_validator, Field
from typing import Optional
import re


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

class ResetPasswordSchema(EmailSchema):
    password: str
    passwordConfirm: str 


class LearnerSchema(BaseModel):
    username: str
    name: str
    age: int
    grade: str
    password: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, value):
        if not re.match(r'^[a-zA-Z0-9_]+$',value):
            raise ValueError(
                "Username only contain letters, numbers and underscore"
            )
        return value
class LessonSchema(BaseModel):
    lesson_name: str

class ModuleSchema(BaseModel):
    module_name: str

class FeedbackSchema(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = None