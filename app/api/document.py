from fastapi import APIRouter, UploadFile, File, Depends
from pathlib import Path
from app.database.mongodb import document_collection
from app.repositories.document_repository import MongoDocumentRepository 
from app.storage.document_storage import LocalStorage
from app.services.document_service import DocumentService

UPLOAD_DIR = Path("data") / "test"

router = APIRouter(prefix="/document")


def get_service() -> DocumentService:
    repository = MongoDocumentRepository(document_collection)
    storage = LocalStorage(UPLOAD_DIR)
    return DocumentService(repository, storage)


@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_service)
):
    return await service.upload_document(file)


@router.post("/update-document/{document_id}")
async def update_document(
    document_id: str,
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_service)
):
    return await service.update_document(document_id, file)


@router.get("/get-document/{document_id}")
async def get_document(
    document_id: str,
    service: DocumentService = Depends(get_service)
):
    return await service.get_by_id(document_id)


@router.get("/get-list-document")
async def list_document(service: DocumentService = Depends(get_service)):
    return await service.list_documents()


@router.delete("/delete-document/{document_id}")
async def delete_document(
    document_id: str,
    service: DocumentService = Depends(get_service)
):
    return await service.delete(document_id)