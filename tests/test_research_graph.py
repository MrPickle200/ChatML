import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.graph.node import ContextNode, GenerateNode, RetrieveNode, RewriteNode
from app.graph.research_graph import ResearchGraph
from app.models.retrieved_chunk import RetrievedChunk


def make_state(**overrides):
    state = {
        "query": "What does it do?",
        "dataset_id": "dataset-1",
        "conversation_id": "conversation-1",
        "rewritten_query": None,
        "retrieved_chunks": [],
        "context": None,
        "history_context": None,
        "answer": None,
    }
    state.update(overrides)
    return state


def make_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="chunk-1",
        document_id="document-1",
        dataset_id="dataset-1",
        chunk_text="Relevant context",
        score=0.9,
    )


def test_rewrite_node_updates_rewritten_query():
    query_rewriter = MagicMock()
    query_rewriter.rewrite = AsyncMock(return_value="What does ChatML do?")

    result = asyncio.run(RewriteNode(query_rewriter)(make_state()))

    assert result == {"rewritten_query": "What does ChatML do?"}
    query_rewriter.rewrite.assert_awaited_once_with(
        query="What does it do?",
        conversation_id="conversation-1",
    )


def test_retrieve_node_uses_rewritten_query():
    chunk = make_chunk()
    retrieval_service = MagicMock()
    retrieval_service.search = AsyncMock(return_value=[chunk])

    result = asyncio.run(
        RetrieveNode(retrieval_service)(
            make_state(rewritten_query="What does ChatML do?")
        )
    )

    assert result == {"retrieved_chunks": [chunk]}
    retrieval_service.search.assert_awaited_once_with(
        query="What does ChatML do?",
        dataset_id="dataset-1",
    )


def test_context_node_receives_retrieved_chunks():
    chunk = make_chunk()
    context_builder = MagicMock()
    context_builder.build_context = AsyncMock(
        return_value=("Relevant context", [{"USER": "Earlier question"}])
    )

    result = asyncio.run(
        ContextNode(context_builder)(make_state(retrieved_chunks=[chunk]))
    )

    assert result == {
        "context": "Relevant context",
        "history_context": [{"USER": "Earlier question"}],
    }
    context_builder.build_context.assert_awaited_once_with(
        "conversation-1",
        [chunk],
    )


def test_generate_node_writes_answer():
    chunk = make_chunk()
    llm_service = MagicMock()
    llm_service.generate = AsyncMock(return_value="Final answer")
    prompt = MagicMock()
    prompt.generate_prompt.return_value = "Generated prompt"

    result = asyncio.run(
        GenerateNode(llm_service, prompt)(
            make_state(
                rewritten_query="What does ChatML do?",
                retrieved_chunks=[chunk],
                context="Relevant context",
                history_context=[{"USER": "Earlier question"}],
            )
        )
    )

    assert result == {"answer": "Final answer"}
    prompt.generate_prompt.assert_called_once_with(
        "What does ChatML do?",
        "Relevant context",
        [{"USER": "Earlier question"}],
    )
    llm_service.generate.assert_awaited_once_with("Generated prompt")


def test_graph_runs_services_in_expected_sequence():
    events = []
    chunk = make_chunk()

    query_rewriter = MagicMock()
    query_rewriter.rewrite = AsyncMock(
        side_effect=lambda **kwargs: events.append("rewrite") or "Standalone question"
    )
    retrieval_service = MagicMock()
    retrieval_service.search = AsyncMock(
        side_effect=lambda **kwargs: events.append("retrieve") or [chunk]
    )
    context_builder = MagicMock()
    context_builder.build_context = AsyncMock(
        side_effect=lambda *args: events.append("context")
        or ("Relevant context", None)
    )
    prompt = MagicMock()
    prompt.generate_prompt.side_effect = (
        lambda *args: events.append("build_prompt") or "Generated prompt"
    )
    llm_service = MagicMock()
    llm_service.generate = AsyncMock(
        side_effect=lambda prompt: events.append("generate") or "Final answer"
    )
    graph = ResearchGraph(
        query_rewrite_service=query_rewriter,
        retrieval_service=retrieval_service,
        context_builder_service=context_builder,
        llm_service=llm_service,
        prompt=prompt,
    )

    result = asyncio.run(graph.ainvoke(make_state()))

    assert events == ["rewrite", "retrieve", "context", "build_prompt", "generate"]
    assert result["rewritten_query"] == "Standalone question"
    assert result["retrieved_chunks"] == [chunk]
    assert result["context"] == "Relevant context"
    assert result["answer"] == "Final answer"


def test_graph_propagates_service_failure():
    failure = RuntimeError("retrieval unavailable")
    query_rewriter = MagicMock()
    query_rewriter.rewrite = AsyncMock(return_value="Standalone question")
    retrieval_service = MagicMock()
    retrieval_service.search = AsyncMock(side_effect=failure)
    graph = ResearchGraph(
        query_rewrite_service=query_rewriter,
        retrieval_service=retrieval_service,
        context_builder_service=MagicMock(),
        llm_service=MagicMock(),
        prompt=MagicMock(),
    )

    with pytest.raises(RuntimeError) as exc_info:
        asyncio.run(graph.ainvoke(make_state()))

    assert exc_info.value is failure


def test_compiled_graph_has_expected_edges():
    graph = ResearchGraph(*[MagicMock() for _ in range(5)])

    edges = {
        (edge.source, edge.target)
        for edge in graph.compiled.get_graph().edges
    }

    assert edges == {
        ("__start__", "rewrite"),
        ("rewrite", "retrieve"),
        ("retrieve", "context"),
        ("context", "generate"),
        ("generate", "__end__"),
    }
