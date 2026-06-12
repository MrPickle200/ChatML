from pydantic import BaseModel

class ParsedElement(BaseModel):
    text: str
    page_number: int | None = None
    source: str | None = None