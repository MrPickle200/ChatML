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


# POST APIs

@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    dataset_id: str = "null",
    service: DocumentService = Depends(get_document_service)
):
    return await service.upload_document(file, dataset_id)


@router.post("/update-document/{document_id}")
async def update_document(
    document_id: str,
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service)
):
    return await service.update_document(document_id, file)


@router.post("/retrieval")
async def retrieval(
    dataset_id: str = "null",
    query: str = "test querry", 
    top_k: int = 5, 
    threshold: float = 0.5,  
    service: RetrievalService = Depends(get_retrieval_service)
):
    return await service.search(query, dataset_id, top_k, threshold)


@router.post("/create-dataset")
async def create_dataset(service: DocumentService = Depends(get_document_service)):
    return await service.create_dataset()


@router.post("/update-dataset/{dataset_id}")
async def update_dataset(
    dataset_id: str,
    name: str = "null",
    description: str = "null",
    service: DocumentService = Depends(get_document_service)
):
    return await service.update_dataset(dataset_id, name, description)

# GET APIs

@router.get("/document/{document_id}")
async def get_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service)
):
    return await service.get_document_by_id(document_id)


@router.get("/list-document")
async def list_document(service: DocumentService = Depends(get_document_service)):
    return await service.list_documents()


@router.get("/list-dataset")
async def list_dataset(service: DocumentService = Depends(get_document_service)):
    return await service.list_datasets()


@router.get("/document-by-dataset/{dataset_id}")
async def get_document_by_dataset(dataset_id: str, service: DocumentService = Depends(get_document_service)):
    return await service.get_document_by_dataset_id(dataset_id)

# DELETE APIs

@router.delete("/document")
async def delete_document(
    document_id: str,
    dataset_id: str,
    service: DocumentService = Depends(get_document_service)
):
    return await service.delete_document(dataset_id, document_id)


@router.delete("/dataset/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    service: DocumentService = Depends(get_document_service)
):
    return await service.delete_dataset(dataset_id)
