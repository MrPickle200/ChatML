class DocumentService:

    def __init__(self, repository):
        self.repository = repository

    async def create_document(
        self,
        file,
        path_to_save,
        metadata
    ):
        await self.repository.create(metadata)

        return metadata

    async def get_document(
        self,
        document_id
    ):
        return await self.repository.get_by_id(
            document_id
        )
    
    # TODO: viết lại service