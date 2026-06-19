from app.repositories.conversation_repository import ConversationRepository
from app.models.retrieved_chunk import RetrievedChunk

class ContextBuilderService:
    def __init__(self, conversation_repo: ConversationRepository):
        self.conversation_repo = conversation_repo

    async def build_context(self, conversation_id: str, retrieval_results: list[RetrievedChunk], top_k_messages = 10):
        if conversation_id:
            history_messages = await self.conversation_repo.get_history_message(conversation_id)
            currently_messages = [
                {msg["role"].upper() : msg["content"]} for msg in history_messages[-top_k_messages : ]
            ]
        else:
            currently_messages = None
        
        currently_context = "\n".join([chunk.chunk_text for chunk in retrieval_results])
        return currently_context, currently_messages
        
        