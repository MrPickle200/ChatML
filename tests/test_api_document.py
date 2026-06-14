from unittest.mock import patch, MagicMock, AsyncMock

# Patch SentenceTransformer immediately before any app imports to prevent downloading model
patcher_st = patch("sentence_transformers.SentenceTransformer")
mock_st_class = patcher_st.start()

# Also patch AsyncQdrantClient and AsyncIOMotorClient just in case they attempt connections during setup
patcher_qdrant = patch("qdrant_client.AsyncQdrantClient")
mock_qdrant_class = patcher_qdrant.start()

from fastapi.testclient import TestClient
from app.main import app
from app.api.document import get_document_service, get_retrieval_service
from app.models.retrieved_chunk import RetrievedChunk

# Setup mock services
mock_doc_service = MagicMock()
mock_ret_service = MagicMock()

async def override_get_document_service():
    return mock_doc_service

async def override_get_retrieval_service():
    return mock_ret_service

# Override the dependencies in FastAPI
app.dependency_overrides[get_document_service] = override_get_document_service
app.dependency_overrides[get_retrieval_service] = override_get_retrieval_service

client = TestClient(app)

def test_api_upload_document():
    mock_doc_service.upload_document = AsyncMock(return_value={"status": "ok", "document_id": "123"})
    
    response = client.post(
        "/document/upload-document",
        files={"file": ("test.pdf", b"pdf content", "application/pdf")}
    )
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "document_id": "123"}
    mock_doc_service.upload_document.assert_called_once()

def test_api_update_document():
    mock_doc_service.update_document = AsyncMock(return_value={"status": "ok"})
    
    response = client.post(
        "/document/update-document/123",
        files={"file": ("test.pdf", b"pdf content", "application/pdf")}
    )
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    mock_doc_service.update_document.assert_called_once()

def test_api_get_document():
    mock_doc_service.get_by_id = AsyncMock(return_value={"status": "ok", "metadata": {}})
    
    response = client.get("/document/get-document/123")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "metadata": {}}
    mock_doc_service.get_by_id.assert_called_once_with("123")

def test_api_list_document():
    mock_doc_service.list_documents = AsyncMock(return_value={"status": "ok", "list_document": []})
    
    response = client.get("/document/get-list-document")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "list_document": []}
    mock_doc_service.list_documents.assert_called_once()

def test_api_delete_document():
    mock_doc_service.delete = AsyncMock(return_value={"status": "ok", "document_id": "123"})
    
    response = client.delete("/document/delete-document/123")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "document_id": "123"}
    mock_doc_service.delete.assert_called_once_with("123")

def test_api_retrieval():
    mock_ret_service.search = AsyncMock(return_value=[
        RetrievedChunk(
            chunk_id="c1",
            document_id="d1",
            dataset_id="ds1",
            chunk_text="hello",
            score=0.9
        )
    ])
    
    response = client.get("/document/retrieval?query=test")
    
    assert response.status_code == 200
    assert response.json() == [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "dataset_id": "ds1",
            "chunk_text": "hello",
            "score": 0.9
        }
    ]
    mock_ret_service.search.assert_called_once_with("test", threshold=0)

# Stop patchers when the module finishes (not strictly necessary but clean)
patcher_st.stop()
patcher_qdrant.stop()

if __name__ == "__main__":
    test_api_upload_document()
    test_api_update_document()
    test_api_get_document()
    test_api_list_document()
    test_api_delete_document()
    test_api_retrieval()
    print("API router tests passed successfully!")
