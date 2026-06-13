from app.core.config import settings
from qdrant_client import AsyncQdrantClient

client = AsyncQdrantClient(
    host=settings.qdrant_host,
    port=settings.qdrant_port,
)