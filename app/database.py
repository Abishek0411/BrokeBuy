from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client["brokebuy"]

try:
    client.admin.command('ping')
    print("MongoDB connection successful")

except Exception as e:
    print(f"MongoDB connection failed: {e}")
