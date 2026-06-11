from pydantic import BaseModel

class Chunk(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    chunk_text: str