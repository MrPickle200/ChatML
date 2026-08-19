import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.services.query_rewrite_service import QueryRewriteService


def test_query_rewrite_returns_original_query_without_history():
    conversation_service = MagicMock()
    conversation_service.get_history_message = AsyncMock(return_value=[])
    llm_service = MagicMock()
    llm_service.generate = AsyncMock()
    service = QueryRewriteService(conversation_service, llm_service)

    result = asyncio.run(service.rewrite("Original question", "conversation-1"))

    assert result == "Original question"
    conversation_service.get_history_message.assert_awaited_once_with(
        "conversation-1"
    )
    llm_service.generate.assert_not_awaited()


def test_query_rewrite_uses_recent_history():
    history = [
        {"role": "user", "content": f"Question {index}"}
        for index in range(12)
    ]
    conversation_service = MagicMock()
    conversation_service.get_history_message = AsyncMock(return_value=history)
    llm_service = MagicMock()
    llm_service.generate = AsyncMock(return_value="Standalone question")
    service = QueryRewriteService(conversation_service, llm_service)

    result = asyncio.run(service.rewrite("What about it?", "conversation-1"))

    assert result == "Standalone question"
    generated_prompt = llm_service.generate.call_args.args[0]
    assert "'Question 0'" not in generated_prompt
    assert "'Question 1'" not in generated_prompt
    assert "'Question 2'" in generated_prompt
    assert "What about it?" in generated_prompt
