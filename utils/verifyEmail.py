# verifyEmail.py
from typing import List
from pydantic import EmailStr
from fastapi import HTTPException, status
from fastapi_mail import ConnectionConfig, MessageSchema, FastMail
from jinja2 import Environment, PackageLoader, select_autoescape

from dotenv import load_dotenv
import os

load_dotenv()

env = Environment(
    loader= PackageLoader('templates',''),
    autoescape= select_autoescape(['html'])

)

class VerifyEmail:
    def __init__(self, name: str, code: str, email: List[EmailStr]):
        self.name=name
        self.code=code
        self.email=email

    async def sendMail(self, subject, template):
        try:
            print("Enter verify email")
            conf = ConnectionConfig(
                MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
                MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
                MAIL_FROM=os.getenv('MAIL_FROM'),
                MAIL_PORT=os.getenv('MAIL_PORT'),
                MAIL_SERVER=os.getenv('MAIL_SERVER'),
                MAIL_FROM_NAME=os.getenv('MAIL_FROM_NAME'),
                MAIL_STARTTLS=True,
                MAIL_SSL_TLS=False,
            )
            print('configured')
            template = env.get_template(f'{template}.html')
            html = template.render(code=self.code, first_name=self.name, subject=subject)
            print('sending msg')
            message = MessageSchema(
                subject=subject, recipients=self.email, body=html, subtype='html'
            )
            print('message schema')
            fm = FastMail(conf)
            print('fastmail configured')
            await fm.send_message(message)
            print("Email sent successfully")

        except Exception as e:
            print(f"Failed to send email: {e}")
            raise HTTPException(
                status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
        
    async def sendVerificationCode(self):
        print("Enter verify email")
        await self.sendMail('Welcome to tamil app! Please Verify Your Email','verification')

class ForgetPassword:
    def __init__(self, name:str, code: str, email: List[EmailStr]):
        self.name=name
        self.code=code
        self.email=email

    async def sendEmail(self, subject, template):
        try:
            conf = ConnectionConfig(
                MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
                MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
                MAIL_FROM=os.getenv('MAIL_FROM'),
                MAIL_PORT=os.getenv('MAIL_PORT'),
                MAIL_SERVER=os.getenv('MAIL_SERVER'),
                MAIL_FROM_NAME=os.getenv('MAIL_FROM_NAME'),
                MAIL_STARTTLS=True,
                MAIL_SSL_TLS=False,
            )
            print('forgetpass configured')

            template = env.get_template(f'{template}.html')
            html = template.render(code=self.code, first_name=self.name, subject=subject)
            print('template rendered')

            message = MessageSchema(
                subject=subject, recipients=self.email, body=html, subtype='html'
            )
            print('message schema created')

            fm = FastMail(conf)
            print('fastmail configured')

            await fm.send_message(message)
            print("Forget password email sent successfully")

        except Exception as e:
            print(f'Failed to send email: {e}')
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send forget password email"
            )
    async def sendVerificationCode(self):
        print("Enter verify email for forget password")
        await self.sendEmail("Welcome to tamil app, verify your email",'forgotPass')