from motor.motor_asyncio import AsyncIOMotorCollection


class MongoDocumentRepository:

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def insert(self, metadata: dict):
        await self.collection.insert_one(metadata)

    async def find_by_id(self, document_id: str) -> dict | None:
        return await self.collection.find_one({"_id": document_id})

    async def update(self, document_id: str, data: dict):
        await self.collection.update_one({"_id": document_id}, {"$set": data})

    async def delete(self, document_id: str):
        await self.collection.delete_one({"_id": document_id})

    async def list_all(self, projection: dict = None) -> list:
        projection = projection or {"_id": 1, "filename": 1, "status": 1, "version": 1}
        cursor = self.collection.find({}, projection)
        return await cursor.to_list(length=None)