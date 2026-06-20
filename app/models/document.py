from pydantic import BaseModel

class Document(BaseModel):
    dataset_id: str
    document_id: str
    file_path: str
    filename: str
    version: int