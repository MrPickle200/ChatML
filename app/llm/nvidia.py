import asyncio
import os
from typing import Any

from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from app.core.exceptions import RateLimitException
from app.llm.base import LLMService


class NvidiaLLM(LLMService):
    """LangChain adapter for a chat model hosted by NVIDIA AI Endpoints."""

    def __init__(self, model: str, timeout_seconds: float = 15.0) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")

        load_dotenv()
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise ValueError("Missing NVIDIA_API_KEY in environment variables")

        self.model = model
        self.name = model
        self.timeout_seconds = timeout_seconds

        try:
            self.client = ChatNVIDIA(model=model, api_key=api_key)
        except Exception:
            raise RuntimeError(
                f"Failed to initialize NVIDIA model '{model}'."
            ) from None

    async def generate(self, prompt: str) -> str:
        try:
            async with asyncio.timeout(self.timeout_seconds):
                response = await self.client.ainvoke(prompt)
        except Exception as exc:
            if self._is_rate_limit_error(exc):
                raise RateLimitException(
                    f"NVIDIA model '{self.name}' is rate limited."
                ) from None
            raise RuntimeError(
                f"NVIDIA model '{self.name}' request failed."
            ) from None

        return self._response_text(response)

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        status_code = getattr(exc, "status_code", None)
        if status_code is None:
            status_code = getattr(exc, "status", None)
        if status_code is None:
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None)
            if status_code is None:
                status_code = getattr(response, "status", None)

        return (
            status_code == 429
            or exc.__class__.__name__ == "RateLimitError"
            or str(exc).lstrip().startswith("[429]")
        )

    @staticmethod
    def _response_text(response: Any) -> str:
        content = getattr(response, "content", response)
        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            text_parts: list[str] = []
            for block in content:
                if isinstance(block, str):
                    text_parts.append(block)
                elif isinstance(block, dict):
                    text = block.get("text")
                    if isinstance(text, str):
                        text_parts.append(text)
            return "".join(text_parts).strip()

        return str(content).strip()
