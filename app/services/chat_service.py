from app.services.retrieval_service import RetrievalService
from app.services.llm_service import LLMService 
from app.prompts.base import BasePrompt
from app.prompts.blank import BlankPrompt
from app.models.chat import Source, ChatResponse
from app.models.retrieved_chunk import RetrievedChunk
from app.services.conversation_service import ConversationService
from app.services.context_builder_service import ContextBuilderService
from datetime import datetime, timezone
from uuid import uuid4

class ChatService:
    def __init__(
        self,
        retrieval_service : RetrievalService,
        conversation_service : ConversationService,
        llm_service : LLMService,
        context_builder_service : ContextBuilderService, 
        prompt : BasePrompt
    ):
        self.retrieval_service = retrieval_service
        self.conversation_service = conversation_service
        self.llm_service = llm_service
        self.context_builder_service = context_builder_service
        self.prompt = prompt

    def _build_source(self, retrieval_results: list[RetrievedChunk], save_into_db = False) -> list[Source] | list[dict]:
        if save_into_db:
            return [
                {
                    "dataset_id" : chunk.dataset_id, 
                    "document_id" : chunk.document_id,
                    "chunk_id" : chunk.chunk_id,
                } for chunk in retrieval_results
            ]

        return [
            Source(
                dataset_id= chunk.dataset_id, 
                document_id= chunk.document_id,
                chunk_id= chunk.chunk_id,
            ) for chunk in retrieval_results
        ]
    
    def _build_message_metadata(
            self, 
            conversation_id : str, 
            role : str, 
            content : str, 
            sources : None | list[Source] = None
        ):
        metadata = {
            "_id" : str(uuid4()),
            "conversation_id" : conversation_id,
            "role" : role,
            "content" : content,
            "sources" : sources,
            "created_at" : datetime.now(timezone.utc),
            "is_conversation" : 0
        }
        return metadata

    
    async def create_conversation(self, conversation_id : str | None = None, title : str | None = None):
        if not conversation_id:
            conversation_id = str(uuid4())

        conversation_metadata = {
            "_id" : conversation_id,
            "title" : title,
            "created_at" : str(datetime.now(timezone.utc)),
            "updated_at" : str(datetime.now(timezone.utc)),
            "is_conversation" : 1
        }
        await self.conversation_service.create_conversation(conversation_metadata)
        return {"status" : "ok", "message" : "Conversation created"}
    
    async def list_conversation(self):
        return await self.conversation_service.list_conversation()
    
    async def get_history_message(self, conversation_id : str):
        return await self.conversation_service.get_history_message(conversation_id)

    async def generate(
            self, question: str, 
            dataset_ids: list[str] | None = None, 
            conversation_id : str | None = None
        ) -> str:

        retrieval_results = await self.retrieval_service.search(query= question, dataset_ids= dataset_ids)
        if len(retrieval_results) == 0:
            self.prompt = BlankPrompt()
        sources = self._build_source(retrieval_results)
        context, history_context = await self.context_builder_service.build_context(conversation_id, retrieval_results)
        prompt = self.prompt.generate_prompt(question, context, history_context)
        answer = await self.llm_service.generate(prompt)

        if not conversation_id:
            conversation_id = str(uuid4())
            title = await self.llm_service.generate(f"Create ONE 4-words title for this question {question}. Do not wrap them in ** **.")
            await self.create_conversation(conversation_id, title)

        user_message_metadata = self._build_message_metadata(conversation_id, "user", question)
        sources_to_save = self._build_source(retrieval_results, save_into_db= True)
        bot_message_metadata = self._build_message_metadata(conversation_id, "bot", answer, sources_to_save)
        await self.conversation_service.add_message(user_message_metadata)
        await self.conversation_service.add_message(bot_message_metadata)

        return ChatResponse(
            answer= answer,
            sources= sources,
            conversation_id= conversation_id
        ) 
    
    async def delete_conversation(self, conversation_id: str):
        return await self.conversation_service.delete_conversation(conversation_id)
    

        