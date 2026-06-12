from pathlib import Path
from datetime import datetime, timezone
from fastapi import HTTPException, UploadFile
from app.models.document import Document
from app.services.ingestion_service import IngestionService
import uuid

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB


class DocumentService:

    def __init__(self, repository, storage, ingestion_service : IngestionService):
        self.repository = repository
        self.storage = storage
        self.ingestion = ingestion_service


    async def _validate_file(self, file: UploadFile):
        ext = file.filename.split(".")[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{ext}' not allowed. Allowed: {ALLOWED_EXTENSIONS}"
            )

        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max: {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB"
            )
        await file.seek(0)


    def _build_metadata(self, document_id: str, file: UploadFile, path: Path) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "_id": document_id,
            "dataset_id": None,
            "filename": file.filename,
            "file_type": file.filename.split(".")[-1].lower(),
            "file_size_byte": path.stat().st_size,
            "version": 1,
            "status": "uploaded",
            "created_at": now,
            "updated_at": now,
            "storage": {
                "provider": "local",
                "uri": str(path)
            }
        }


    def _build_update_metadata(self, current_doc: dict, file: UploadFile, path: Path) -> dict:
        return {
            "filename": file.filename,
            "file_type": file.filename.split(".")[-1].lower(),
            "file_size_byte": path.stat().st_size,
            "version": current_doc["version"] + 1,
            "status": "updated",
            "updated_at": datetime.now(timezone.utc),
            "storage": {
                "provider": "local",
                "uri": str(path)
            }
        }


    async def upload_document(self, file: UploadFile) -> dict:
        await self._validate_file(file)

        document_id = str(uuid.uuid4())
        try:
            path = await self.storage.save(file, document_id)
            metadata = self._build_metadata(document_id, file, path)
            await self.repository.insert(metadata)

            document = Document(
                document_id= document_id,
                file_path= metadata["storage"]["uri"],
                filename= metadata["filename"],
                version= metadata["version"]
            )
            response = self.ingestion.ingest_document(document)

        except Exception as e:
            self.storage.delete(document_id)
            raise HTTPException(status_code=500, detail=str(e))

        return {
            "status": "ok", 
            "document_id": document_id, 
            "message": "Document uploaded",
            "chunks_created": response["chunks_created"],
            "points_created": response["points_created"]
        }


    async def update_document(self, document_id: str, file: UploadFile) -> dict:
        await self._validate_file(file)

        current_doc = await self.repository.find_by_id(document_id)
        if not current_doc:
            raise HTTPException(status_code=404, detail="Document not found")

        old_path = Path(current_doc["storage"]["uri"])
        try:
            path = await self.storage.replace(file, old_path)
            update_metadata = self._build_update_metadata(current_doc, file, path)
            await self.repository.update(document_id, update_metadata)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return {"status": "ok", "document_id": document_id, "message": "Document updated"}

        #TODO: re-embed sau update

    async def get_by_id(self, document_id: str) -> dict:
        doc = await self.repository.find_by_id(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "ok", "metadata": doc}


    async def list_documents(self) -> dict:
        docs = await self.repository.list_all()
        return {"status": "ok", "list_document": docs}


    async def delete(self, document_id: str) -> dict:
        doc = await self.repository.find_by_id(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        try:
            self.storage.delete(document_id)
            await self.repository.delete(document_id)
        except FileNotFoundError:
            # File đã bị xóa tay khỏi disk, vẫn xóa record trong DB
            await self.repository.delete(document_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return {"status": "ok"}