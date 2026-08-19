import logging
from typing import TypedDict

from app.llm.base import LLMService
from app.models.research_state import ResearchState
from app.models.retrieved_chunk import RetrievedChunk
from app.prompts.base import BasePrompt
from app.prompts.blank import BlankPrompt
from app.services.context_builder_service import ContextBuilderService
from app.services.query_rewrite_service import QueryRewriteService
from app.services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


class RewrittenQueryUpdate(TypedDict):
    rewritten_query: str


class RetrievedChunksUpdate(TypedDict):
    retrieved_chunks: list[RetrievedChunk]


class ContextUpdate(TypedDict):
    context: str
    history_context: list[dict[str, str]] | None


class AnswerUpdate(TypedDict):
    answer: str


class RewriteNode:
    def __init__(self, query_rewrite_service: QueryRewriteService):
        self.query_rewrite_service = query_rewrite_service

    async def __call__(self, state: ResearchState) -> RewrittenQueryUpdate:
        logger.debug("Query rewrite started")
        rewritten_query = await self.query_rewrite_service.rewrite(
            query=state["query"],
            conversation_id=state["conversation_id"],
        )
        logger.debug("Query rewrite completed")
        return {"rewritten_query": rewritten_query}


class RetrieveNode:
    def __init__(self, retrieval_service: RetrievalService):
        self.retrieval_service = retrieval_service

    async def __call__(self, state: ResearchState) -> RetrievedChunksUpdate:
        rewritten_query = state["rewritten_query"]
        if rewritten_query is None:
            raise ValueError("Rewritten query is required before retrieval")

        chunks = await self.retrieval_service.search(
            query=rewritten_query,
            dataset_id=state["dataset_id"],
        )
        logger.debug("Retrieval completed with %d chunks", len(chunks))
        return {"retrieved_chunks": chunks}


class ContextNode:
    def __init__(self, context_builder_service: ContextBuilderService):
        self.context_builder_service = context_builder_service

    async def __call__(self, state: ResearchState) -> ContextUpdate:
        context, history_context = await self.context_builder_service.build_context(
            state["conversation_id"],
            state["retrieved_chunks"],
        )
        logger.debug("Context built")
        return {"context": context, "history_context": history_context}


class GenerateNode:
    def __init__(self, llm_service: LLMService, prompt: BasePrompt):
        self.llm_service = llm_service
        self.prompt = prompt

    async def __call__(self, state: ResearchState) -> AnswerUpdate:
        rewritten_query = state["rewritten_query"]
        context = state["context"]
        if rewritten_query is None or context is None:
            raise ValueError("Rewritten query and context are required before generation")

        prompt_builder = self.prompt if state["retrieved_chunks"] else BlankPrompt()
        generated_prompt = prompt_builder.generate_prompt(
            rewritten_query,
            context,
            state["history_context"],
        )
        logger.debug("Answer generation started")
        answer = await self.llm_service.generate(generated_prompt)
        logger.debug("Answer generation completed")
        return {"answer": answer}
