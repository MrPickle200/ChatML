from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, UpdateResult, FilterSelector
from app.core.config import settings

class QdrantRepository:
    def __init__(self, client : AsyncQdrantClient):
        self.client = client
        self.collection_name = settings.qdrant_collection_name

    async def create_collection(self):
        if not await self.collection_exist():
            await self.client.create_collection(
                collection_name= self.collection_name,
                vectors_config= VectorParams(size= settings.qdrant_vector_size, distance= Distance.COSINE)
            )

    async def collection_exist(self):
        return await self.client.collection_exists(self.collection_name)

    async def upsert_points(self, points : list[PointStruct]):
        await self.client.upsert(
            collection_name= self.collection_name,
            points= points,
            wait= True
        )

    async def delete_by_document_id(self, document_id: str) -> UpdateResult:
        filter = Filter(
            must=[
                FieldCondition(key="document_id", match=MatchValue(value=document_id))
            ]
        )
        return await self.client.delete(
            collection_name=settings.qdrant_collection_name,
            points_selector=FilterSelector(filter=filter),
            wait=True,
        )
        

    async def search(
            self, query_vector: list[float], 
            top_k: int, 
            dataset_id: str | None = None, 
            threshold: float | None = None
    ):
        
        if dataset_id:
            filter = Filter(
                must=[
                    FieldCondition(key="dataset_id", match=MatchValue(value=dataset_id))
                ]
            )
            result = await self.client.query_points(
                collection_name= self.collection_name,
                query= query_vector,
                limit= top_k,
                score_threshold= threshold,
                with_payload= True,
                query_filter= FilterSelector(filter= filter)
            )
        else:
            result = await self.client.query_points(
                collection_name= self.collection_name,
                query= query_vector,
                limit= top_k,
                score_threshold= threshold,
                with_payload= True,
                query_filter= None
            )

        return [
            {
                "id": point.id,
                "score": point.score,
                "payload": point.payload,
            }
            for point in result.points
        ]
