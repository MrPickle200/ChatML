from app.services.parsing_service import ParsingService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.repositories.qdrant_repository import QdrantRepository
from app.models.document import Document
from app.models.chunk import Chunk
from app.core.config import settings
from qdrant_client.models import PointStruct

class IngestionService:
    def __init__(
            self,
            parsing_service: ParsingService,
            chunking_service: ChunkingService,
            embedding_service: EmbeddingService,
            qdrant_repo: QdrantRepository,
            sparse_embedding_service=None
        ):
        self.parsing_service = parsing_service
        self.chunking_service = chunking_service
        self.embedding_service = embedding_service
        self.qdrant_repo = qdrant_repo
        
        # NEW: Khởi tạo/nhận SparseEmbeddingService
        if sparse_embedding_service is None:
            from app.services.embedding_service import SparseEmbeddingService
            self.sparse_embedding_service = SparseEmbeddingService()
        else:
            self.sparse_embedding_service = sparse_embedding_service

    def _build_payload(self, document: Document, chunk: Chunk):
        return {
            "dataset_id": document.dataset_id,
            "document_id": document.document_id,

            "chunk_id": chunk.chunk_id,
            "chunk_index": chunk.chunk_index,

            "chunk_text": chunk.chunk_text,

            "source": document.filename,
            "version": document.version,

            "embedding_model": settings.embedding_model
        }
    
    # --- CODE CŨ (Được comment lại) ---
    # def _build_point(self, chunk: Chunk, vector: list[float], document: Document):
    #     payload = self._build_payload(document, chunk)
    #     return PointStruct(
    #         id= chunk.chunk_id,
    #         vector= vector,
    #         payload= payload
    #     )
    # -----------------------------------

    # NEW: Hỗ trợ build point với hybrid vector (dense + sparse)
    def _build_point(self, chunk: Chunk, dense_vector: list[float], sparse_vector, document: Document):
        payload = self._build_payload(document, chunk)
        return PointStruct(
            id= chunk.chunk_id,
            vector={
                "dense": dense_vector,
                "sparse": sparse_vector
            },
            payload= payload
        )

    # --- CODE CŨ (Được comment lại) ---
    # async def ingest_document(self, document: Document):
    #     file_path = document.file_path
    #     document_id = document.document_id
    # 
    #     parsed_results = self.parsing_service.parse(file_path)
    #     texts = "\n".join([el.text for el in parsed_results])
    # 
    #     chunks = self.chunking_service.chunk_text(texts, document_id)
    #     vectors = self.embedding_service.embed_texts([chunk.chunk_text for chunk in chunks])
    # 
    #     points = []
    #     for chunk, vector in zip(chunks, vectors):
    #         point = self._build_point(chunk, vector, document)
    #         points.append(point)
    #     await self.qdrant_repo.upsert_points(points)
    # 
    #     return {
    #         "document_id" : document.document_id,
    #         "chunks_created" : len(chunks),
    #         "points_created" : len(points)
    #     }
    # -----------------------------------

    # NEW: Hàm ingest sinh cả dense và sparse vector để lưu trữ phục vụ Hybrid Search
    async def ingest_document(self, document: Document):
        file_path = document.file_path
        document_id = document.document_id

        parsed_results = self.parsing_service.parse(file_path)
        texts = "\n".join([el.text for el in parsed_results])

        chunks = self.chunking_service.chunk_text(texts, document_id)
        
        # Sinh dense vectors
        dense_vectors = await self.embedding_service.embed_texts(
            [chunk.chunk_text for chunk in chunks]
        )
        # Sinh sparse vectors
        sparse_vectors = self.sparse_embedding_service.embed_texts([chunk.chunk_text for chunk in chunks])

        points = []
        for chunk, dense_vector, sparse_vector in zip(chunks, dense_vectors, sparse_vectors):
            point = self._build_point(chunk, dense_vector, sparse_vector, document)
            points.append(point)
        await self.qdrant_repo.upsert_points(points)

        return {
            "document_id" : document.document_id,
            "chunks_created" : len(chunks),
            "points_created" : len(points)
        }
    
    async def delete_document(self, document_id: str):
        await self.qdrant_repo.delete_by_document_id(document_id)

    async def update_document(self, document: Document):
        document_id = document.document_id
        await self.delete_document(document_id)
        await self.ingest_document(document)
