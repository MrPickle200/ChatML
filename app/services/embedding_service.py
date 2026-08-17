import hashlib
import math
import os
import re

from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from qdrant_client.models import SparseVector

from app.core.config import settings


class EmbeddingService:
    def __init__(
        self,
        model: str | None = None,
        vector_size: int | None = None,
    ) -> None:
        load_dotenv()
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise ValueError("Missing NVIDIA_API_KEY in environment variables")

        self.model_name = model or settings.embedding_model
        self._vector_size = vector_size or settings.qdrant_vector_size

        try:
            self.client = NVIDIAEmbeddings(
                model=self.model_name,
                api_key=api_key,
            )
        except Exception:
            raise RuntimeError(
                f"Failed to initialize NVIDIA embedding model '{self.model_name}'."
            ) from None

    @property
    def vector_size(self) -> int:
        return self._vector_size

    async def embed_text(self, text: str) -> list[float]:
        try:
            return await self.client.aembed_query(text)
        except Exception:
            raise RuntimeError("NVIDIA query embedding request failed.") from None

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        try:
            return await self.client.aembed_documents(texts)
        except Exception:
            raise RuntimeError("NVIDIA document embedding request failed.") from None


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

