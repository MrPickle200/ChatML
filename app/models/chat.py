from pydantic import BaseModel

class Source(BaseModel):
    dataset_id: str | None = None
    document_id: str
    chunk_id: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[Source] | None = None
