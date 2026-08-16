from unittest.mock import patch, MagicMock
import numpy as np
from app.services.embedding_service import EmbeddingService

def test_embedding_service():
    # Mock SentenceTransformer
    mock_model = MagicMock()
    mock_model.get_embedding_dimension.return_value = 384
    
    # mock encode for single text return a numpy array
    dummy_vector = np.array([0.1, 0.2, 0.3])
    dummy_vectors = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    
    def mock_encode(texts, normalize_embeddings=True):
        if isinstance(texts, str):
            return dummy_vector
        return dummy_vectors

    mock_model.encode.side_effect = mock_encode

    with patch("app.services.embedding_service.SentenceTransformer", return_value=mock_model):
        service = EmbeddingService()
        
        # Verify vector size
        assert service.vector_size == 384
        
        # Verify single text embedding
        emb = service.embed_text("hello")
        assert emb == [0.1, 0.2, 0.3]
        mock_model.encode.assert_called_with("hello", normalize_embeddings=True)
        
        # Verify multiple texts embedding
        embs = service.embed_texts(["hello", "world"])
        assert embs == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_model.encode.assert_called_with(["hello", "world"], normalize_embeddings=True)

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
