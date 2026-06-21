from pathlib import Path
from datetime import datetime, timezone
from fastapi import HTTPException, UploadFile
from app.models.document import Document
from app.services.ingestion_service import IngestionService
from app.repositories.document_repository import MongoDocumentRepository
from app.storage.document_storage import LocalStorage
import uuid

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB


class DocumentService:

    def __init__(self, repository : MongoDocumentRepository, storage : LocalStorage, ingestion_service : IngestionService):
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


    def _build_document_metadata(self, document_id: str, dataset_id : str, file: UploadFile, path: Path) -> dict:
        now = str(datetime.now(timezone.utc))
        return {
            "_id": document_id,
            "dataset_id": dataset_id,
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
            },
            "is_dataset": 0
        }


    def _build_update_document_metadata(self, current_doc: dict, file: UploadFile, path: Path) -> dict:
        return {
            "filename": file.filename,
            "file_type": file.filename.split(".")[-1].lower(),
            "file_size_byte": path.stat().st_size,
            "version": current_doc["version"] + 1,
            "status": "updated",
            "updated_at": str(datetime.now(timezone.utc)),
            "storage": {
                "provider": "local",
                "uri": str(path)
            }
        }
    

    def _build_dataset_metadata(self, dataset_id: str):
        now = str(datetime.now(timezone.utc))
        return {
            "_id" : dataset_id,
            "name" : "blank",
            "description" : "blank",
            "created_at" : now,
            "updated_at" : now,
            "is_dataset" : 1
        }


    async def upload_document(self, file: UploadFile, dataset_id: str = "null") -> dict:
        await self._validate_file(file)

        has_dataset_id = True if dataset_id != "null" else False
        if not has_dataset_id:
            dataset_id = str(uuid.uuid4())
        document_id = str(uuid.uuid4())

        try:
            path = await self.storage.save(file, dataset_id, document_id)
            document_metadata = self._build_document_metadata(document_id, dataset_id, file, path)
            await self.repository.insert_document(document_metadata)

            document = Document(
                dataset_id= dataset_id, 
                document_id= document_id,
                file_path= document_metadata["storage"]["uri"],
                filename= document_metadata["filename"],
                version= document_metadata["version"]
            )
            response = await self.ingestion.ingest_document(document)

            if not has_dataset_id:
                dataset_metadata = self._build_dataset_metadata(dataset_id)
                await self.repository.create_dataset(dataset_metadata)
            else:
                update_metadata = {
                    "updated_at" : str(datetime.now(timezone.utc))
                }
                await self.repository.update_dataset(dataset_id, update_metadata)

        except Exception as e:
            await self.repository.delete_document(document_id)
            try:
                self.storage.delete_document(dataset_id, document_id)
            except Exception:
                pass
            raise HTTPException(status_code=500, detail=str(e))


        return {
            "status": "ok", 
            "dataset_id": dataset_id, 
            "document_id": document_id, 
            "message": "Document uploaded",
            "chunks_created": response["chunks_created"],
            "points_created": response["points_created"]
        }


    async def update_document(self, document_id: str, file: UploadFile) -> dict:
        await self._validate_file(file)

        current_doc = await self.repository.find_document_by_id(document_id)
        if not current_doc:
            raise HTTPException(status_code=404, detail="Document not found")

        old_path = Path(current_doc["storage"]["uri"])
        dataset_id = current_doc["dataset_id"]
        try:
            path = await self.storage.replace(file, old_path)
            update_metadata = self._build_update_document_metadata(current_doc, file, path)
            await self.repository.update_document(document_id, update_metadata)

            document = Document(
                dataset_id= dataset_id, 
                document_id= document_id,
                file_path= str(path),
                filename= update_metadata["filename"],
                version= update_metadata["version"]
            )
            await self.ingestion.update_document(document)
            now = str(datetime.now(timezone.utc))
            await self.repository.update_dataset(dataset_id, {"updated_at" : now})

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return {"status": "ok", "document_id": document_id, "message": "Document updated"}
    

    async def get_document_by_id(self, document_id: str) -> dict:
        doc = await self.repository.find_document_by_id(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "ok", "metadata": doc}


    async def list_documents(self) -> dict:
        docs = await self.repository.list_all_document()
        return {"status": "ok", "list_document": docs}


    async def delete_document(self, dataset_id: str, document_id: str) -> dict:
        try:
            self.storage.delete_document(dataset_id, document_id)
            await self.repository.delete_document(document_id)
            await self.ingestion.delete_document(document_id)
        except FileNotFoundError:
            # File đã bị xóa tay khỏi disk, vẫn xóa record trong DB
            await self.repository.delete_document(document_id)
            await self.ingestion.delete_document(document_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return {"status": "ok", "document_id" : document_id, "message" : "Document deleted"}
    

    async def get_document_by_dataset_id(self, dataset_id: str) -> list:
        try:
            return await self.repository.find_document_by_dataset_id(dataset_id)
        except Exception as e:
            raise HTTPException(status_code= 500, detail= str(e))


    async def create_dataset(self):
        dataset_id = str(uuid.uuid4())
        dataset_metadata = self._build_dataset_metadata(dataset_id)
        try:
            await self.repository.create_dataset(dataset_metadata)
            return {"status" : "ok", "dataset_id" : dataset_id}
        except Exception as e:
            raise HTTPException(status_code= 500, detail= str(e))


    async def list_datasets(self) -> dict:
        try:
            datasets = await self.repository.list_all_dataset()
            return {"status" : "ok", "list_dataset" : datasets}
        
        except Exception as e:
            raise HTTPException(status_code= 500, detail= str(e))
        

    async def delete_dataset(self, dataset_id: str) -> dict:
        try:
            documents = await self.repository.find_document_by_dataset_id(dataset_id)
            if documents:
                for document in documents:
                    await self.delete_document(document_id= document["_id"], dataset_id= dataset_id)
            self.storage.delete_dataset(dataset_id)
            await self.repository.delete_dataset(dataset_id)
            return {"status" : "ok"}

        except Exception as e:
            raise HTTPException(status_code= 500, detail= str(e))
        
    
    async def update_dataset(self, dataset_id: str, name: str, description: str) -> dict:
        update_metadata = dict()
        if name != "null":
            update_metadata["name"] = name
        if description != "null":
            update_metadata["description"] = description
        try:
            if len(update_metadata) > 0:
                update_metadata["updated_at"] = str(datetime.now(timezone.utc))
                await self.repository.update_dataset(dataset_id, update_metadata)
            return {"status" : "ok"}
        except Exception as e:
            raise HTTPException(status_code= 500, detail= str(e))