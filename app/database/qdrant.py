from app.core.config import settings
from qdrant_client import QdrantClient

client = QdrantClient(
    host=settings.qdrant_host,
    port=settings.qdrant_port,
)