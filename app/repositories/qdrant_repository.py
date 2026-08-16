from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance, 
    VectorParams, 
    PointStruct, 
    Filter, 
    FieldCondition, 
    MatchValue, 
    UpdateResult, 
    FilterSelector,
    # NEW imports for Hybrid Search
    SparseVectorParams,
    SparseVector,
    Prefetch,
    FusionQuery,
    Fusion
)
from app.core.config import settings
from app.models.retrieved_chunk import RetrievedChunk

class QdrantRepository:
    def __init__(self, client : AsyncQdrantClient):
        self.client = client
        self.collection_name = settings.qdrant_collection_name

    # --- CODE CŨ (Được comment lại) ---
    # async def create_collection(self):
    #     if not await self.collection_exist():
    #         await self.client.create_collection(
    #             collection_name= self.collection_name,
    #             vectors_config= VectorParams(size= settings.qdrant_vector_size, distance= Distance.COSINE)
    #         )
    # -----------------------------------

    # NEW: Hỗ trợ tạo collection với cấu hình hybrid (dense + sparse)
    async def create_collection(self):
        exists = await self.collection_exist()
        if exists:
            try:
                info = await self.client.get_collection(self.collection_name)
                # Nếu collection cũ chưa dùng named vectors (không có dense config), thực hiện xoá và tạo lại
                is_old_schema = not isinstance(info.config.params.vectors, dict) or "dense" not in info.config.params.vectors
                if is_old_schema:
                    await self.client.delete_collection(self.collection_name)
                    exists = False
            except Exception:
                pass

        if not exists:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "dense": VectorParams(size=settings.qdrant_vector_size, distance=Distance.COSINE)
                },
                sparse_vectors_config={
                    "sparse": SparseVectorParams()
                }
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
        
    # --- CODE CŨ (Được comment lại) ---
    # async def search(
    #         self, query_vector: list[float], 
    #         top_k: int, 
    #         dataset_id: str, 
    #         threshold: float
    # ):
    #     query_filter = None
    #     if dataset_id != "null":
    #         query_filter = Filter(
    #             must=[
    #                 FieldCondition(
    #                     key="dataset_id",
    #                     match=MatchValue(value=dataset_id)
    #                 )
    #             ]
    #         )
    # 
    #     result = await self.client.query_points(
    #         collection_name=self.collection_name,
    #         query=query_vector,
    #         limit=top_k,
    #         score_threshold=threshold,
    #         with_payload=True,
    #         query_filter=query_filter
    #     )
    # 
    #     return [
    #         RetrievedChunk(
    #             chunk_id=point.payload["chunk_id"],
    #             document_id=point.payload["document_id"],
    #             dataset_id=point.payload["dataset_id"],
    #             chunk_text=point.payload["chunk_text"],
    #             score=point.score
    #         )
    #         for point in result.points
    #     ]
    # -----------------------------------

    # NEW: Tìm kiếm Hybrid (Dense + Sparse) sử dụng cơ chế RRF (Reciprocal Rank Fusion) của Qdrant
    async def search(
            self, 
            query_vector: list[float], 
            sparse_query_vector: SparseVector,
            top_k: int, 
            dataset_id: str, 
            threshold: float
    ):
        query_filter = None
        if dataset_id != "null":
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="dataset_id",
                        match=MatchValue(value=dataset_id)
                    )
                ]
            )

        # Sử dụng API query_points hỗ trợ prefetch kết hợp dense và sparse vector
        result = await self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                Prefetch(
                    query=query_vector,
                    using="dense",
                    limit=top_k,
                    filter=query_filter,
                    score_threshold=threshold  # Áp dụng threshold riêng cho Dense
                ),
                Prefetch(
                    query=sparse_query_vector,
                    using="sparse",
                    limit=top_k,
                    filter=query_filter
                )
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=top_k,
            with_payload=True
        )

        return [
            RetrievedChunk(
                chunk_id=point.payload["chunk_id"],
                document_id=point.payload["document_id"],
                dataset_id=point.payload["dataset_id"],
                chunk_text=point.payload["chunk_text"],
                score=point.score
            )
            for point in result.points
        ]

