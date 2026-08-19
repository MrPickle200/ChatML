import logging
from typing import cast

from langgraph.graph import END, START, StateGraph

from app.graph.node import ContextNode, GenerateNode, RetrieveNode, RewriteNode
from app.llm.base import LLMService
from app.models.research_state import ResearchState
from app.prompts.base import BasePrompt
from app.services.context_builder_service import ContextBuilderService
from app.services.query_rewrite_service import QueryRewriteService
from app.services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


class ResearchGraph:
    def __init__(
        self,
        query_rewrite_service: QueryRewriteService,
        retrieval_service: RetrievalService,
        context_builder_service: ContextBuilderService,
        llm_service: LLMService,
        prompt: BasePrompt,
    ):
        builder = StateGraph(ResearchState)
        builder.add_node("rewrite", RewriteNode(query_rewrite_service))
        builder.add_node("retrieve", RetrieveNode(retrieval_service))
        builder.add_node("context", ContextNode(context_builder_service))
        builder.add_node("generate", GenerateNode(llm_service, prompt))

        builder.add_edge(START, "rewrite")
        builder.add_edge("rewrite", "retrieve")
        builder.add_edge("retrieve", "context")
        builder.add_edge("context", "generate")
        builder.add_edge("generate", END)

        self.compiled = builder.compile()

    async def ainvoke(self, state: ResearchState) -> ResearchState:
        try:
            return cast(ResearchState, await self.compiled.ainvoke(state))
        except Exception:
            logger.exception("Research graph execution failed")
            raise
