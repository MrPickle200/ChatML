from app.services.retrieval_service import RetrievalService
from app.services.llm_service import LLMService 
from app.prompts.base import BasePrompt
from app.prompts.blank import BlankPrompt
from app.models.chat import Source, ChatResponse
from app.models.retrieved_chunk import RetrievedChunk

class ChatService:
    def __init__(
        self,
        retrieval_service : RetrievalService,
        llm_service : LLMService,
        prompt : BasePrompt
    ):
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service
        self.prompt = prompt

    def _build_source(self, retrieval_results: list[RetrievedChunk]) -> list[Source]:
        return [
            Source(
                dataset_id= chunk.dataset_id, 
                document_id= chunk.document_id,
                chunk_id= chunk.chunk_id
            ) for chunk in retrieval_results
        ]

    async def generate(self, question: str, dataset_ids: list[str] | None = None) -> str:
        retrieval_results = await self.retrieval_service.search(query= question, dataset_ids= dataset_ids)
        if len(retrieval_results) == 0:
            self.prompt = BlankPrompt()
        sources = self._build_source(retrieval_results)

        context = "\n".join([chunk.chunk_text for chunk in retrieval_results])
        prompt = self.prompt.generate_prompt(question, context)
        answer = await self.llm_service.generate(prompt)
        return ChatResponse(
            answer= answer,
            sources= sources
        ) 
    

        