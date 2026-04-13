# mongo.py
from motor.motor_asyncio import AsyncIOMotorClient
import os

from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
print("Mongodb uri: ",MONGO_URI)

DATABASE_NAME = "tamil-app"
USER_COLLECTION = 'users'
OTP_COLLECTION = 'otps'
PROFILE_COLLECTION = 'profiles'
ASSET_COLLECTION = 'assets'
LESSON_COLLECTION = 'lessons'
MODULE_COLLECTION = 'modules'


client = AsyncIOMotorClient(MONGO_URI)

db = client[DATABASE_NAME]
user_collection = db[USER_COLLECTION]
otp_collection = db[OTP_COLLECTION]
profile_collection = db[PROFILE_COLLECTION]
asset_collection = db[ASSET_COLLECTION]
lesson_collection = db[LESSON_COLLECTION]
module_collection = db[MODULE_COLLECTION]