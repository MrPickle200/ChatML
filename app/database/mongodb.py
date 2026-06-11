from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = AsyncIOMotorClient(
    settings.mongodb_uri
)

db = client[settings.mongodb_database]
document_collection = db["documents"]
conversation_collection = db["conversations"]
feedback_collection = db["feedback"]