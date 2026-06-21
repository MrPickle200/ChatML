from app.services.embedding_service import EmbeddingService
from app.repositories.qdrant_repository import QdrantRepository
from fastapi.exceptions import HTTPException

class RetrievalService:
    def __init__(self, embedding_service: EmbeddingService, qdrant_repo: QdrantRepository):
        self.embedding_service = embedding_service
        self.qdrant_repo = qdrant_repo

    async def search(
            self,
            query: str,
            dataset_id: str = "null",
            top_k: int = 5, 
            threshold: float = 0.5
    ):
        try:
            query_vector = self.embedding_service.embed_text(query)
            return await self.qdrant_repo.search(query_vector, top_k, dataset_id, threshold)
        except Exception as e:
            raise HTTPException(status_code= 500, detail= str(e))
    