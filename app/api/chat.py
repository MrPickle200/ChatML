from fastapi import APIRouter, Depends
from app.services.chat_service import ChatService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import GeminiService
from app.services.retrieval_service import RetrievalService
from app.prompts.simple import SimplePrompt
from app.database.qdrant import client as qdrant_client
from app.repositories.qdrant_repository import QdrantRepository

router = APIRouter(prefix="/chat")
embedding_service = EmbeddingService()
gemini_service = GeminiService()

async def get_chat_service() -> ChatService:
    qdrant_repo =  QdrantRepository(qdrant_client)
    await qdrant_repo.create_collection()
    retrieval_service = RetrievalService(
        embedding_service,
        qdrant_repo
    )

    return ChatService(
        retrieval_service,
        gemini_service,
        SimplePrompt()
    )

@router.post("/chat")
async def chat(question: str, dataset_ids: list[str] | None = None, chat_service: ChatService = Depends(get_chat_service)):
    return await chat_service.generate(question, dataset_ids)