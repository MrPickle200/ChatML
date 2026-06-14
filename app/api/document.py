from fastapi import APIRouter, UploadFile, File, Depends
from pathlib import Path
from app.database.mongodb import document_collection
from app.repositories.document_repository import MongoDocumentRepository 
from app.storage.document_storage import LocalStorage
from app.services.document_service import DocumentService

from app.database.qdrant import client as qdrant_client
from app.services.ingestion_service import IngestionService
from app.services.parsing_service import ParsingService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService
from app.repositories.qdrant_repository import QdrantRepository


UPLOAD_DIR = Path("data") / "test"

router = APIRouter(prefix="/document")
embedding_service = EmbeddingService()

async def get_document_service() -> DocumentService:
    repository = MongoDocumentRepository(document_collection)
    storage = LocalStorage(UPLOAD_DIR)
    
    qdrant_repo = QdrantRepository(qdrant_client)
    await qdrant_repo.create_collection()
    
    ingestion = IngestionService(
        parsing_service= ParsingService(),
        chunking_service= ChunkingService(),
        embedding_service= embedding_service,
        qdrant_repo= QdrantRepository(qdrant_client)
    )

    return DocumentService(repository, storage, ingestion)

async def get_retrieval_service() -> RetrievalService:
    qdrant_repo = QdrantRepository(qdrant_client)
    await qdrant_repo.create_collection()
    return RetrievalService(embedding_service, qdrant_repo)

@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service)
):
    return await service.upload_document(file)


@router.post("/update-document/{document_id}")
async def update_document(
    document_id: str,
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service)
):
    return await service.update_document(document_id, file)


@router.get("/get-document/{document_id}")
async def get_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service)
):
    return await service.get_by_id(document_id)


@router.get("/get-list-document")
async def list_document(service: DocumentService = Depends(get_document_service)):
    return await service.list_documents()


@router.delete("/delete-document/{document_id}")
async def delete_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service)
):
    return await service.delete(document_id)

@router.post("/retrieval")
async def retrieval(
    query: str = "test querry", 
    top_k: int = 5, 
    threshold: float = 0.5, 
    dataset_ids: list[str] | None = None, 
    service: RetrievalService = Depends(get_retrieval_service)
):
    return await service.search(query, dataset_ids, top_k, threshold)