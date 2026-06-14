import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException
from app.services.retrieval_service import RetrievalService
from app.models.retrieved_chunk import RetrievedChunk

def test_retrieval_search_success():
    mock_embedding = MagicMock()
    mock_embedding.embed_text.return_value = [0.1, 0.2, 0.3]

    mock_qdrant = MagicMock()
    mock_qdrant.search = AsyncMock(return_value=[
        RetrievedChunk(
            chunk_id="c1",
            document_id="d1",
            dataset_id="ds1",
            chunk_text="hello",
            score=0.9
        )
    ])

    service = RetrievalService(mock_embedding, mock_qdrant)

    async def run_test():
        results = await service.search("hello query", dataset_id="ds1", top_k=3, threshold=0.6)
        
        mock_embedding.embed_text.assert_called_once_with("hello query")
        mock_qdrant.search.assert_called_once_with([0.1, 0.2, 0.3], 3, "ds1", 0.6)
        assert len(results) == 1
        assert results[0].chunk_id == "c1"
        assert results[0].document_id == "d1"
        assert results[0].dataset_id == "ds1"
        assert results[0].chunk_text == "hello"
        assert results[0].score == 0.9

    asyncio.run(run_test())

def test_retrieval_search_failure():
    mock_embedding = MagicMock()
    mock_embedding.embed_text.side_effect = Exception("Embedding failed")
    mock_qdrant = MagicMock()

    service = RetrievalService(mock_embedding, mock_qdrant)

    async def run_test():
        with pytest.raises(HTTPException) as exc_info:
            await service.search("hello query")
        assert exc_info.value.status_code == 500
        assert "Embedding failed" in exc_info.value.detail

    asyncio.run(run_test())

if __name__ == "__main__":
    test_retrieval_search_success()
    test_retrieval_search_failure()
    print("RetrievalService tests passed successfully!")
