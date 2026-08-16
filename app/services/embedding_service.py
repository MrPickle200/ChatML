from app.core.config import settings
from sentence_transformers import SentenceTransformer
import re
import math
import hashlib
from qdrant_client.models import SparseVector

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


# NEW: SparseEmbeddingService for generating sparse vectors to support Hybrid Search
class SparseEmbeddingService:
    def __init__(self, max_features: int = 1000000):
        self.max_features = max_features

    def _tokenize(self, text: str) -> list[str]:
        # Lowercase and extract alphanumeric tokens of length >= 2
        return re.findall(r'\b\w{2,}\b', text.lower())

    def embed_text(self, text: str) -> SparseVector:
        tokens = self._tokenize(text)
        if not tokens:
            return SparseVector(indices=[], values=[])
        
        # Calculate term frequencies (TF)
        tf = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
            
        # Map tokens to indices using stable md5 hashing
        indices = []
        values = []
        for token, count in tf.items():
            # Stable hash to map to indices
            h = hashlib.md5(token.encode('utf-8')).hexdigest()
            idx = int(h, 16) % self.max_features
            
            # Sub-linear term frequency scaling: 1 + log(tf)
            weight = float(math.log1p(count))
            
            indices.append(idx)
            values.append(weight)
            
        # Qdrant requires sorted indices
        sorted_pairs = sorted(zip(indices, values))
        indices = [p[0] for p in sorted_pairs]
        values = [p[1] for p in sorted_pairs]
        
        return SparseVector(indices=indices, values=values)
        
    def embed_texts(self, texts: list[str]) -> list[SparseVector]:
        return [self.embed_text(text) for text in texts]

