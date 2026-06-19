from fastapi import APIRouter
from app.database.qdrant import client as qdrant_client
from app.core.config import settings

router = APIRouter(prefix="/benchmark")

@router.get("/chunks")
async def get_chunks():
    collection_name = settings.qdrant_collection_name
    
    # Check if collection exists
    collection_exists = await qdrant_client.collection_exists(collection_name)
    if not collection_exists:
        return []
        
    chunks = []
    next_offset = None
    while True:
        # scroll returns (points, next_page_offset)
        response = await qdrant_client.scroll(
            collection_name=collection_name,
            limit=100,
            with_payload=True,
            with_vectors=False,
            offset=next_offset
        )
        points, next_offset = response
        for point in points:
            payload = point.payload or {}
            chunks.append({
                "chunk_id": payload.get("chunk_id"),
                "document_id": payload.get("document_id"),
                "text": payload.get("chunk_text", "")
            })
        if next_offset is None:
            break
            
    return chunks
