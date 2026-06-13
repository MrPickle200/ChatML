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

if __name__ == "__main__":
    test_embedding_service()
    print("EmbeddingService tests passed successfully!")
