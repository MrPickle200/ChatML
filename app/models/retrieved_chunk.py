from pydantic import BaseModel

class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    dataset_id: str | None = None
    chunk_text: str
    score: float