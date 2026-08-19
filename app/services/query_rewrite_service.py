from app.llm.base import LLMService
from app.services.conversation_service import ConversationService


class QueryRewriteService:
    def __init__(
        self,
        conversation_service: ConversationService,
        llm_service: LLMService,
    ):
        self.conversation_service = conversation_service
        self.llm_service = llm_service

    async def rewrite(self, query: str, conversation_id: str) -> str:
        history_messages = await self.conversation_service.get_history_message(
            conversation_id
        )
        current_messages = [
            {message["role"].upper(): message["content"]}
            for message in history_messages[-10:]
        ]
        if not current_messages:
            return query

        prompt = f"""
            === SYSTEM ===
            Your task is to use conversation history to resolve current question into a standalone question,
            which means no ambiguous object in the sentence (like it, they, them, ...)

            === CONVERSATION HISTORY ===
            {current_messages}

            === CURRENT QUESTION ===
            {query}
        """
        return await self.llm_service.generate(prompt)
