from motor.motor_asyncio import AsyncIOMotorCollection


class ConversationRepository:

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create_conversation(self, conversation_metadata: dict):
        await self.collection.insert_one(conversation_metadata)

    async def get_conversation(self, conversation_id: str):
        projection = {"_id": 1, "title": 1, "created_at": 1, "updated_at": 1}
        cursor = self.collection.find({"conversation_id" : conversation_id}, projection)
        return await cursor.to_list(length=None)        

    async def list_conversations(self):
        projection = {"_id": 1, "title": 1, "created_at": 1, "updated_at": 1}
        cursor = self.collection.find({}, projection)
        return await cursor.to_list(length=None)        

    async def add_message(self, message_metadata: dict):
        await self.collection.insert_one(message_metadata)
        # TODO: update conversation after add message

    async def delete_conversation(self, conversation_id: str):
        await self.collection.delete_many({"conversation_id" : conversation_id})