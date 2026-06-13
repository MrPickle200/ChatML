import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException
from app.services.document_service import DocumentService

def test_upload_document_success():
    # Setup mocks
    mock_repo = MagicMock()
    mock_repo.insert = AsyncMock()
    
    mock_storage = MagicMock()
    mock_storage.save = AsyncMock(return_value=Path("data/test/doc1/test.pdf"))
    # In upload_document, lines 92 and 149 do calls. Let's use AsyncMock to satisfy any awaits
    mock_storage.delete = AsyncMock()
    
    mock_ingestion = MagicMock()
    mock_ingestion.ingest_document = AsyncMock(return_value={"chunks_created": 5, "points_created": 5})

    service = DocumentService(mock_repo, mock_storage, mock_ingestion)

    # Mock UploadFile
    mock_file = AsyncMock()
    mock_file.filename = "test.pdf"
    mock_file.read.return_value = b"dummy content"

    async def run_test():
        # Mock Path.stat to return size
        with patch("app.services.document_service.Path.stat") as mock_stat:
            mock_stat.return_value.st_size = 100
            
            res = await service.upload_document(mock_file)
            
            assert res["status"] == "ok"
            assert res["chunks_created"] == 5
            assert res["points_created"] == 5
            
            mock_storage.save.assert_called_once()
            mock_repo.insert.assert_called_once()
            mock_ingestion.ingest_document.assert_called_once()

    asyncio.run(run_test())

def test_upload_document_invalid_extension():
    mock_repo = MagicMock()
    mock_storage = MagicMock()
    mock_ingestion = MagicMock()
    service = DocumentService(mock_repo, mock_storage, mock_ingestion)

    mock_file = AsyncMock()
    mock_file.filename = "test.exe"

    async def run_test():
        with pytest.raises(HTTPException) as exc_info:
            await service.upload_document(mock_file)
        assert exc_info.value.status_code == 400
        assert "not allowed" in exc_info.value.detail

    asyncio.run(run_test())

def test_upload_document_too_large():
    mock_repo = MagicMock()
    mock_storage = MagicMock()
    mock_ingestion = MagicMock()
    service = DocumentService(mock_repo, mock_storage, mock_ingestion)

    mock_file = AsyncMock()
    mock_file.filename = "test.pdf"
    mock_file.read.return_value = b"a" * (51 * 1024 * 1024) # 51MB

    async def run_test():
        with pytest.raises(HTTPException) as exc_info:
            await service.upload_document(mock_file)
        assert exc_info.value.status_code == 400
        assert "too large" in exc_info.value.detail

    asyncio.run(run_test())

def test_upload_document_exception_cleanup():
    mock_repo = MagicMock()
    mock_repo.insert = AsyncMock(side_effect=Exception("DB Error"))
    mock_repo.delete = AsyncMock()
    
    mock_storage = MagicMock()
    mock_storage.save = AsyncMock(return_value=Path("data/test/doc1/test.pdf"))
    mock_storage.delete = AsyncMock()
    
    mock_ingestion = MagicMock()

    service = DocumentService(mock_repo, mock_storage, mock_ingestion)

    mock_file = AsyncMock()
    mock_file.filename = "test.pdf"
    mock_file.read.return_value = b"dummy content"

    async def run_test():
        with patch("app.services.document_service.Path.stat") as mock_stat:
            mock_stat.return_value.st_size = 100
            
            with pytest.raises(HTTPException) as exc_info:
                await service.upload_document(mock_file)
            
            assert exc_info.value.status_code == 500
            mock_repo.delete.assert_called_once()
            mock_storage.delete.assert_called_once()

    asyncio.run(run_test())

def test_update_document_success():
    mock_repo = MagicMock()
    mock_repo.find_by_id = AsyncMock(return_value={
        "_id": "doc1",
        "version": 1,
        "storage": {"uri": "data/test/doc1/old.pdf"},
        "filename": "old.pdf"
    })
    mock_repo.update = AsyncMock()

    mock_storage = MagicMock()
    mock_storage.replace = AsyncMock(return_value=Path("data/test/doc1/new.pdf"))

    mock_ingestion = MagicMock()
    mock_ingestion.update_document = AsyncMock()

    service = DocumentService(mock_repo, mock_storage, mock_ingestion)

    mock_file = AsyncMock()
    mock_file.filename = "new.pdf"
    mock_file.read.return_value = b"content"

    async def run_test():
        with patch("app.services.document_service.Path.stat") as mock_stat:
            mock_stat.return_value.st_size = 200
            
            res = await service.update_document("doc1", mock_file)
            assert res["status"] == "ok"
            assert res["document_id"] == "doc1"
            
            mock_repo.update.assert_called_once()
            mock_ingestion.update_document.assert_called_once()

    asyncio.run(run_test())

def test_update_document_not_found():
    mock_repo = MagicMock()
    mock_repo.find_by_id = AsyncMock(return_value=None)
    mock_storage = MagicMock()
    mock_ingestion = MagicMock()
    service = DocumentService(mock_repo, mock_storage, mock_ingestion)

    mock_file = AsyncMock()
    mock_file.filename = "new.pdf"
    mock_file.read.return_value = b"content"

    async def run_test():
        with patch("app.services.document_service.Path.stat") as mock_stat:
            mock_stat.return_value.st_size = 200
            with pytest.raises(HTTPException) as exc_info:
                await service.update_document("doc1", mock_file)
            assert exc_info.value.status_code == 404

    asyncio.run(run_test())

def test_get_by_id_success():
    mock_repo = MagicMock()
    mock_repo.find_by_id = AsyncMock(return_value={"_id": "doc1", "filename": "test.pdf"})
    mock_storage = MagicMock()
    mock_ingestion = MagicMock()
    service = DocumentService(mock_repo, mock_storage, mock_ingestion)

    async def run_test():
        res = await service.get_by_id("doc1")
        assert res["status"] == "ok"
        assert res["metadata"]["_id"] == "doc1"

    asyncio.run(run_test())

def test_get_by_id_not_found():
    mock_repo = MagicMock()
    mock_repo.find_by_id = AsyncMock(return_value=None)
    mock_storage = MagicMock()
    mock_ingestion = MagicMock()
    service = DocumentService(mock_repo, mock_storage, mock_ingestion)

    async def run_test():
        with pytest.raises(HTTPException) as exc_info:
            await service.get_by_id("doc1")
        assert exc_info.value.status_code == 404

    asyncio.run(run_test())

def test_list_documents():
    mock_repo = MagicMock()
    mock_repo.list_all = AsyncMock(return_value=[{"_id": "doc1"}])
    mock_storage = MagicMock()
    mock_ingestion = MagicMock()
    service = DocumentService(mock_repo, mock_storage, mock_ingestion)

    async def run_test():
        res = await service.list_documents()
        assert res["status"] == "ok"
        assert len(res["list_document"]) == 1

    asyncio.run(run_test())

def test_delete_success():
    mock_repo = MagicMock()
    mock_repo.find_by_id = AsyncMock(return_value={
        "_id": "doc1",
        "storage": {"uri": "data/test/doc1/test.pdf"}
    })
    mock_repo.delete = AsyncMock()

    # In delete, self.storage.delete(document_id) is synchronous.
    # To mock a synchronous function, we define a normal function/mock.
    mock_storage = MagicMock()
    mock_storage.delete = MagicMock()

    mock_ingestion = MagicMock()
    mock_ingestion.delete_document = AsyncMock()

    service = DocumentService(mock_repo, mock_storage, mock_ingestion)

    async def run_test():
        res = await service.delete("doc1")
        assert res["status"] == "ok"
        mock_storage.delete.assert_called_once_with("doc1")
        mock_repo.delete.assert_called_once_with("doc1")
        mock_ingestion.delete_document.assert_called_once_with("doc1")

    asyncio.run(run_test())

def test_delete_file_not_found():
    mock_repo = MagicMock()
    mock_repo.find_by_id = AsyncMock(return_value={
        "_id": "doc1",
        "storage": {"uri": "data/test/doc1/test.pdf"}
    })
    mock_repo.delete = AsyncMock()

    mock_storage = MagicMock()
    mock_storage.delete = MagicMock(side_effect=FileNotFoundError("Not found"))

    mock_ingestion = MagicMock()
    mock_ingestion.delete_document = AsyncMock()

    service = DocumentService(mock_repo, mock_storage, mock_ingestion)

    async def run_test():
        res = await service.delete("doc1")
        assert res["status"] == "ok"
        mock_repo.delete.assert_called_once_with("doc1")
        mock_ingestion.delete_document.assert_called_once_with("doc1")

    asyncio.run(run_test())

if __name__ == "__main__":
    test_upload_document_success()
    test_upload_document_invalid_extension()
    test_upload_document_too_large()
    test_upload_document_exception_cleanup()
    test_update_document_success()
    test_update_document_not_found()
    test_get_by_id_success()
    test_get_by_id_not_found()
    test_list_documents()
    test_delete_success()
    test_delete_file_not_found()
    print("DocumentService tests passed successfully!")
