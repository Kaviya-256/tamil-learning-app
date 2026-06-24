# main.py
from fastapi import FastAPI
from api.auth import router as auth_router
from api.admin import router as admin_router
from api.user import router as user_router
from api.lesson import router as lesson_router
from api.learner import router as learner_router
from api.admin_lesson import router as admin_lesson_router

from games.api.admin_games import router as admin_games_router
from games.api.games import router as games_router

from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import json

load_dotenv()
class UnicodeJSONResponse(JSONResponse):
    def render(self, content)->bytes:
        return json.dumps(content, ensure_ascii=False).encode('utf-8')

app = FastAPI(
    title="Tamil Learning App",
    description="API for tamil learning app",
    default_response_class=UnicodeJSONResponse
)

origins= os.getenv("CORS_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/', tags=['Root'])
async def root():
    return {'message': "Welcome to Tamil learning app!"}

app.include_router(auth_router, tags=["Authentication"])
app.include_router(admin_router)
app.include_router(admin_lesson_router)
app.include_router(user_router, tags=['Users'])
app.include_router(lesson_router, tags=['Lessons'])
app.include_router(learner_router, tags=['Learners'])

# app.include_router(admin_games_router)
# app.include_router(games_router)