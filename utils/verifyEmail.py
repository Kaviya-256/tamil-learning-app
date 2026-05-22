# verifyEmail.py
from typing import List
from pydantic import EmailStr
from fastapi import HTTPException, status
from fastapi_mail import MessageSchema
from jinja2 import Environment, select_autoescape, FileSystemLoader

import os

from schema import ContactAdminSchema
from utils.mail_config import fm


env = Environment(
    loader= FileSystemLoader('templates'),
    autoescape= select_autoescape(['html'])

)

class VerifyEmail:
    def __init__(self, name: str, code: str, email: List[EmailStr]):
        self.name=name
        self.code=code
        self.email=email

    async def sendMail(self, subject, template):
        try:
            template = env.get_template(f'{template}.html')
            html = template.render(code=self.code, first_name=self.name, subject=subject)
            message = MessageSchema(
                subject=subject, recipients=self.email, body=html, subtype='html'
            )
            
            await fm.send_message(message)

        except Exception as e:
            print('Email error: ',e)
            raise HTTPException(
                status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
        
    async def sendVerificationCode(self):
        await self.sendMail('Welcome to Paignthamizh app! Please Verify Your Email','verification')

class ForgetPassword:
    def __init__(self, name:str, code: str, email: List[EmailStr]):
        self.name=name
        self.code=code
        self.email=email

    async def sendEmail(self, subject, template):
        try:
            template = env.get_template(f'{template}.html')
            html = template.render(code=self.code, first_name=self.name, subject=subject)

            message = MessageSchema(
                subject=subject, recipients=self.email, body=html, subtype='html'
            )

            await fm.send_message(message)

        except Exception as e:
            print('Email error: ',e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send forget password email"
            )
    async def sendVerificationCode(self):
        await self.sendEmail("Welcome to Paignthamizh app, verify your email",'forgotPass')

# Contact Admin
class ContactAdminMail:

    def __init__(self, data: ContactAdminSchema):
        self.name = data.name
        self.user_email = data.email
        self.subject = data.subject
        self.message = data.message

        self.admin_email = os.getenv("ADMIN_EMAIL")

    async def sendMail(self, template):
        try:
            template = env.get_template(f'{template}.html')

            html = template.render(
                name=self.name,
                email=self.user_email,
                subject=self.subject,
                message=self.message,
            )

            message = MessageSchema(
                subject=self.subject, recipients=[self.admin_email], body=html, subtype='html'
            )

            await fm.send_message(message)

        except Exception as e:
            print('Email error: ',e)
            raise HTTPException(
                status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
        
    async def sendMailtoAdmin(self):
        await self.sendMail('contact_admin')