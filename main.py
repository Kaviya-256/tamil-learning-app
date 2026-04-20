# main.py
from fastapi import FastAPI, Depends
from api.auth import router as auth_router
from api.admin import router as admin_router
from api.user import router as user_router
from api.lesson import router as lesson_router

app = FastAPI()

@app.get('/')
async def hello():
    return {'message': "Tamil learning app!"}

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://darkcyan-dun2.hostingersite.com","http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.auth_router = auth_router
app.admin_router = admin_router
app.user_router = user_router
app.lesson_router = lesson_router


app.include_router(auth_router, tags=["Authentication"])
app.include_router(admin_router, tags=['Admin interface'])
app.include_router(user_router, tags=['User interface'])
app.include_router(lesson_router, tags=['Lessons Interface'])