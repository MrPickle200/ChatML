from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.core.config import settings

class QdrantRepository:
    def __init__(self, client : QdrantClient):
        self.client = client
        self.collection_name = settings.qdrant_collection_name

    def create_collection(self):
        if not self.collection_exist():
            self.client.create_collection(
                collection_name= self.collection_name,
                vectors_config= VectorParams(size= settings.qdrant_vector_size, distance= Distance.COSINE)
            )

    def collection_exist(self):
        return self.client.collection_exists(self.collection_name)

    def upsert_points(self, points : list[PointStruct]):
        self.client.upsert(
            collection_name= self.collection_name,
            points= points,
            wait= True
        )

    def get_point(self, point_id : str):
        return self.client.retrieve(
            collection_name= self.collection_name,
            ids= [point_id]
        )

    def delete_points(self, point_ids: list[str]):
        self.client.delete(
            collection_name= self.collection_name,
            points_selector= point_ids
        )

    def search(self, query_vector: list[float], top_k: int = 5, threshold: float | None = None):
        return self.client.search(
            collection_name= self.collection_name,
            query_vector= query_vector,
            limit= top_k,
            score_threshold= threshold,
            with_payload= True
        )
