# main.py
from fastapi import FastAPI
from api.auth import router as auth_router
from api.admin import router as admin_router
from api.user import router as user_router
from api.lesson import router as lesson_router

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

origins= os.getenv("CORS_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get('/')
async def hello():
    return {'message': "Tamil learning app!"}

app.auth_router = auth_router
app.admin_router = admin_router
app.user_router = user_router
app.lesson_router = lesson_router


app.include_router(auth_router, tags=["Authentication"])
app.include_router(admin_router, tags=['Admin interface'])
app.include_router(user_router, tags=['User interface'])
app.include_router(lesson_router, tags=['Lessons Interface'])