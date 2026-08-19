import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import RateLimitException
from app.llm.llm_router import LLMRouter
from app.llm.nvidia import NvidiaLLM


class StubLLM:
    def __init__(self, name: str, side_effect=None, result: str | None = None) -> None:
        self.name = name
        self.generate = AsyncMock(side_effect=side_effect, return_value=result)


def test_nvidia_llm_requires_api_key(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)

    with patch("app.llm.nvidia.load_dotenv"):
        with pytest.raises(ValueError, match="NVIDIA_API_KEY"):
            NvidiaLLM("meta/llama-3.1-8b-instruct")


def test_nvidia_llm_initializes_langchain_client(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    client = MagicMock()

    with patch("app.llm.nvidia.ChatNVIDIA", return_value=client) as chat_nvidia:
        model = NvidiaLLM("meta/llama-3.1-8b-instruct")

    chat_nvidia.assert_called_once_with(
        model="meta/llama-3.1-8b-instruct",
        api_key="test-key",
    )
    assert model.client is client
    assert model.name == "meta/llama-3.1-8b-instruct"


def test_nvidia_llm_generates_plain_string(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    client = MagicMock()
    client.ainvoke = AsyncMock(return_value=SimpleNamespace(content="  answer  "))

    with patch("app.llm.nvidia.ChatNVIDIA", return_value=client):
        model = NvidiaLLM("meta/llama-3.1-8b-instruct")

    result = asyncio.run(model.generate("question"))

    assert result == "answer"
    client.ainvoke.assert_awaited_once_with("question")


def test_nvidia_llm_converts_structured_content_to_string(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    client = MagicMock()
    client.ainvoke = AsyncMock(
        return_value=SimpleNamespace(
            content=[{"type": "text", "text": "first "}, "second"]
        )
    )

    with patch("app.llm.nvidia.ChatNVIDIA", return_value=client):
        model = NvidiaLLM("meta/llama-3.1-8b-instruct")

    assert asyncio.run(model.generate("question")) == "first second"


def test_nvidia_llm_translates_rate_limit(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    provider_error = RuntimeError("provider details")
    provider_error.status_code = 429
    client = MagicMock()
    client.ainvoke = AsyncMock(side_effect=provider_error)

    with patch("app.llm.nvidia.ChatNVIDIA", return_value=client):
        model = NvidiaLLM("meta/llama-3.1-8b-instruct")

    with pytest.raises(RateLimitException, match="rate limited"):
        asyncio.run(model.generate("question"))


def test_nvidia_llm_bounds_slow_provider_call(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    client = MagicMock()

    async def never_respond(_prompt):
        await asyncio.Event().wait()

    client.ainvoke = AsyncMock(side_effect=never_respond)

    with patch("app.llm.nvidia.ChatNVIDIA", return_value=client):
        model = NvidiaLLM(
            "meta/llama-3.1-8b-instruct",
            timeout_seconds=0.01,
        )

    with pytest.raises(RuntimeError, match="request failed"):
        asyncio.run(model.generate("question"))


def test_router_retries_then_falls_back():
    first = StubLLM(
        "first",
        side_effect=RateLimitException("rate limited"),
    )
    second = StubLLM("second", result="fallback answer")
    router = LLMRouter(models=[first, second], max_attempts=2)

    with patch("app.llm.llm_router.asyncio.sleep", new=AsyncMock()) as sleep:
        result = asyncio.run(router.generate("question"))

    assert result == "fallback answer"
    assert first.generate.await_count == 2
    second.generate.assert_awaited_once_with("question")
    sleep.assert_awaited_once_with(1)


def test_router_raises_when_all_models_fail():
    first = StubLLM("first", side_effect=RateLimitException("rate limited"))
    second = StubLLM("second", side_effect=RuntimeError("provider failed"))
    router = LLMRouter(models=[first, second], max_attempts=1)

    with pytest.raises(RuntimeError, match="All NVIDIA LLM models"):
        asyncio.run(router.generate("question"))

    first.generate.assert_awaited_once_with("question")
    second.generate.assert_awaited_once_with("question")
