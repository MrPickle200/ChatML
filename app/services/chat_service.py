import asyncio
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from app.graph.research_graph import ResearchGraph
from app.llm.base import LLMService
from app.models.chat import ChatResponse, Source
from app.models.research_state import ResearchState
from app.models.retrieved_chunk import RetrievedChunk
from app.prompts.base import BasePrompt
from app.services.context_builder_service import ContextBuilderService
from app.services.conversation_service import ConversationService
from app.services.query_rewrite_service import QueryRewriteService
from app.services.retrieval_service import RetrievalService


class GraphRunner(Protocol):
    async def ainvoke(self, state: ResearchState) -> ResearchState: ...


class ChatService:
    def __init__(
        self,
        retrieval_service: RetrievalService,
        conversation_service: ConversationService,
        llm_service: LLMService,
        context_builder_service: ContextBuilderService,
        prompt: BasePrompt,
        graph: GraphRunner | None = None,
        query_rewrite_service: QueryRewriteService | None = None,
    ):
        self.retrieval_service = retrieval_service
        self.conversation_service = conversation_service
        self.llm_service = llm_service
        self.context_builder_service = context_builder_service
        self.prompt = prompt
        query_rewrite_service = query_rewrite_service or QueryRewriteService(
            conversation_service=conversation_service,
            llm_service=llm_service,
        )
        self.graph = graph or ResearchGraph(
            query_rewrite_service=query_rewrite_service,
            retrieval_service=retrieval_service,
            context_builder_service=context_builder_service,
            llm_service=llm_service,
            prompt=prompt,
        )

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

    @staticmethod
    def _build_conversation_title(question: str) -> str:
        words = question.strip().split()
        return " ".join(words[:4]) or "New conversation"
    
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
        self,
        question: str,
        dataset_id: str,
        conversation_id: str,
    ) -> ChatResponse:
        result = await self.graph.ainvoke(
            {
                "query": question,
                "dataset_id": dataset_id,
                "conversation_id": conversation_id,
                "rewritten_query": None,
                "retrieved_chunks": [],
                "context": None,
                "history_context": None,
                "answer": None,
            }
        )
        retrieval_results = result["retrieved_chunks"]
        answer = result["answer"]
        if answer is None:
            raise RuntimeError("Research graph completed without an answer")

        sources = self._build_source(retrieval_results)

        if conversation_id == "null":
            conversation_id = str(uuid4())
            title = self._build_conversation_title(question)
            db_tasks = [self.create_conversation(conversation_id, title)]
        else:
            db_tasks = []

        user_message_metadata = self._build_message_metadata(conversation_id, "user", question)
        sources_to_save = self._build_source(retrieval_results, save_into_db= True)
        bot_message_metadata = self._build_message_metadata(conversation_id, "bot", answer, sources_to_save)
        
        db_tasks.append(self.conversation_service.add_message(user_message_metadata))
        db_tasks.append(self.conversation_service.add_message(bot_message_metadata))

        await asyncio.gather(*db_tasks)

        return ChatResponse(
            answer= answer,
            sources= sources,
            conversation_id= conversation_id
        ) 
    
    async def delete_conversation(self, conversation_id: str):
        return await self.conversation_service.delete_conversation(conversation_id)
    

