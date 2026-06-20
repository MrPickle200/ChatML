from motor.motor_asyncio import AsyncIOMotorCollection


class MongoDocumentRepository:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def insert_document(self, metadata: dict):
        await self.collection.insert_one(metadata)

    async def find_document_by_id(self, document_id: str) -> dict | None:
        return await self.collection.find_one({"_id": document_id, "is_dataset" : 0})

    async def update_document(self, document_id: str, data: dict):
        await self.collection.update_one({"_id": document_id, "is_dataset" : 0}, {"$set": data})

    async def delete_document(self, document_id: str):
        await self.collection.delete_one({"_id": document_id, "is_dataset" : 0})

    async def list_all_document(self, projection: dict = None) -> list:
        projection = projection or {"_id": 1, "filename": 1, "status": 1, "version": 1}
        cursor = self.collection.find({"is_dataset" : 0}, projection)
        return await cursor.to_list()
    
    async def create_dataset(self, metadata: dict):
        await self.collection.insert_one(metadata)

    async def delete_dataset(self, dataset_id: str):
        await self.collection.delete_one({"_id" : dataset_id, "is_dataset" : 1})

    async def update_dataset(self, dataset_id: str, update_metadata: dict):
        await self.collection.update_one({"_id" : dataset_id}, {"$set": update_metadata})

    async def list_all_dataset(self, projection: dict = None) -> list:
        projection = projection or {"_id" : 1, "name" : 1}
        cursor = self.collection.find({"is_dataset" : 1}, projection)
        return await cursor.to_list()
    
    async def find_document_by_dataset_id(self, dataset_id: str) -> list:
        cursor = self.collection.find(
            {
                "dataset_id" : dataset_id,
                "is_dataset" : 0
            },
            {
                "_id" : 1,
                "filename" : 1,
            }  
        )
        return await cursor.to_list()

    
    