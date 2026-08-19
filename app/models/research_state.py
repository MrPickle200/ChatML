from typing import TypedDict

from app.models.retrieved_chunk import RetrievedChunk


class ResearchState(TypedDict):
    query: str
    dataset_id: str
    conversation_id: str
    rewritten_query: str | None
    retrieved_chunks: list[RetrievedChunk]
    context: str | None
    history_context: list[dict[str, str]] | None
    answer: str | None
    
