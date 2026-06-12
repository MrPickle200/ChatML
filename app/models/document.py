from pydantic import BaseModel

class Document(BaseModel):
    dataset_id: str | None = None
    document_id: str
    file_path: str
    filename: str
    version: int