from app.repositories.conversation_repository import ConversationRepository
from app.models.retrieved_chunk import RetrievedChunk
from app.services.llm_service import LLMService
from fastapi import HTTPException

class ContextBuilderService:
    def __init__(self, conversation_repo: ConversationRepository, llm_service: LLMService):
        self.conversation_repo = conversation_repo
        self.llm_service = llm_service

    async def build_context(self, conversation_id: str, retrieval_results: list[RetrievedChunk], top_k_messages = 10):
        if conversation_id:
            try:
                history_messages = await self.conversation_repo.get_history_message(conversation_id)
                currently_messages = [
                    {msg["role"] : msg["content"]} for msg in history_messages[-top_k_messages : ]
                ]

                prompt = f"""
                    Your task is to shorten below paragraph into a context of 50%
                    length of the paragraph, but still maintains the key idea

                    Paragraph
                    {currently_messages}

                    Return only the shortened version
                """
                history_context = await self.llm_service.generate(prompt)
                print(f"History context: {history_context}")
            except Exception as e: 
                raise HTTPException(status_code= 500, detail= str(e))
        else:
            history_context = None
        
        current_context = "\n".join([chunk.chunk_text for chunk in retrieval_results])
        return current_context, history_context
        
        