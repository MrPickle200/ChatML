import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.embedding_service import EmbeddingService


def test_embedding_service_requires_api_key(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)

    with patch("app.services.embedding_service.load_dotenv"):
        with pytest.raises(ValueError, match="NVIDIA_API_KEY"):
            EmbeddingService()


def test_embedding_service_uses_nvidia_async_api(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    mock_client = MagicMock()
    mock_client.aembed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])
    mock_client.aembed_documents = AsyncMock(
        return_value=[[0.1, 0.2], [0.3, 0.4]]
    )

    with patch(
        "app.services.embedding_service.NVIDIAEmbeddings",
        return_value=mock_client,
    ) as nvidia_embeddings:
        service = EmbeddingService(
            model="nvidia/nv-embedqa-e5-v5",
            vector_size=1024,
        )

    nvidia_embeddings.assert_called_once_with(
        model="nvidia/nv-embedqa-e5-v5",
        api_key="test-key",
    )
    assert service.vector_size == 1024

    async def run_test():
        assert await service.embed_text("hello") == [0.1, 0.2, 0.3]
        assert await service.embed_texts(["hello", "world"]) == [
            [0.1, 0.2],
            [0.3, 0.4],
        ]

    asyncio.run(run_test())
    mock_client.aembed_query.assert_awaited_once_with("hello")
    mock_client.aembed_documents.assert_awaited_once_with(["hello", "world"])

def test_sparse_embedding_service():
    from app.services.embedding_service import SparseEmbeddingService
    from qdrant_client.models import SparseVector
    
    service = SparseEmbeddingService()
    
    # Test tokenization
    tokens = service._tokenize("Hello, World!")
    assert tokens == ["hello", "world"]
    
    # Test single text embedding
    sparse_vec = service.embed_text("Hello, World! Hello")
    assert isinstance(sparse_vec, SparseVector)
    assert len(sparse_vec.indices) == 2
    assert len(sparse_vec.values) == 2
    # Verify indices are sorted
    assert sparse_vec.indices[0] <= sparse_vec.indices[1]
    
    # Test multiple texts embedding
    sparse_vecs = service.embed_texts(["Hello", "World"])
    assert len(sparse_vecs) == 2
    assert isinstance(sparse_vecs[0], SparseVector)

if __name__ == "__main__":
    test_embedding_service()
    test_sparse_embedding_service()
    print("EmbeddingService tests passed successfully!")
