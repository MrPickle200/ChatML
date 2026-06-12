from app.core.config import settings
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        self.model: SentenceTransformer = SentenceTransformer(settings.embedding_model)

    @property
    def vector_size(self) -> int:
        return self.model.get_embedding_dimension()

    def embed_text(self, text: str) -> list[float]:
        return self.model.encode(text, normalize_embeddings= True).tolist()
    
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings= True).tolist()
