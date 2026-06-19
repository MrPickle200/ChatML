from fastapi import APIRouter, Depends
from app.services.chat_service import ChatService
from app.services.embedding_service import EmbeddingService
from app.llm.llm_router import LLMRouter
from app.services.retrieval_service import RetrievalService
from app.services.conversation_service import ConversationService
from app.prompts.simple import SimplePrompt
from app.database.qdrant import client as qdrant_client
from app.database.mongodb import conversation_collection as conversation_client
from app.repositories.qdrant_repository import QdrantRepository
from app.repositories.conversation_repository import ConversationRepository
from app.services.context_builder_service import ContextBuilderService

router = APIRouter(prefix="/chat")
embedding_service = EmbeddingService()
conversation_repo = ConversationRepository(conversation_client)
conversation_service = ConversationService(conversation_repo)
context_builder_service = ContextBuilderService(conversation_repo)

async def get_chat_service() -> ChatService:
    qdrant_repo =  QdrantRepository(qdrant_client)
    await qdrant_repo.create_collection()
    retrieval_service = RetrievalService(
        embedding_service,
        qdrant_repo
    )

    return ChatService(
        retrieval_service= retrieval_service,
        conversation_service= conversation_service,
        llm_service = LLMRouter(),
        prompt = SimplePrompt(),
        context_builder_service= context_builder_service
    )

@router.post("/chat")
async def chat(
    question: str, 
    dataset_ids: list[str] | None = None, 
    conversation_id: str | None = None,
    chat_service: ChatService = Depends(get_chat_service)
):
    return await chat_service.generate(question, dataset_ids, conversation_id)

@router.post("/create-conversation")
async def create_conversation(chat_service: ChatService = Depends(get_chat_service)):
    return await chat_service.create_conversation()

@router.get("/list-conversation")
async def list_conversation(chat_service: ChatService = Depends(get_chat_service)):
    return await chat_service.list_conversation()

@router.get("/get_conversation/{conversation_id}")
async def get_history_message(conversation_id : str, chat_service : ChatService = Depends(get_chat_service)):
    return await chat_service.get_history_message(conversation_id)

@router.delete("/delete_conversation/{conversation_id}")
async def delete_conversation(conversation_id : str, chat_service : ChatService = Depends(get_chat_service)):
    return await chat_service.delete_conversation(conversation_id)