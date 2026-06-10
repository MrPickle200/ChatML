class DocumentRepository:

    def __init__(self, collection):
        self.collection = collection

    async def create(self, document):
        return await self.collection.insert_one(document)

    async def get_by_id(self, document_id):
        return await self.collection.find_one(
            {"_id": document_id}
        )

    async def list_documents(self):
        return await self.collection.find().to_list(length=100)

    async def delete(self, document_id):
        return await self.collection.delete_one(
            {"_id": document_id}
        )

    async def update(self, document_id, update_data):
        return await self.collection.update_one(
            {"_id": document_id},
            {"$set": update_data}
        )
    
    #TODO: viết lại repository