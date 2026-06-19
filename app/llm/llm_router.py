import asyncio
import logging

from app.llm.base import LLMService
from app.llm.gemini import Gemini
from app.llm.groq import GroqModel
from app.core.exceptions import RateLimitException

logger = logging.getLogger(__name__)


class LLMRouter(LLMService):
    def __init__(self):
        self.models: list[LLMService] = [
            GroqModel(model="llama-3.3-70b-versatile"),
            GroqModel(model="llama-3.1-8b-instant"),
            Gemini(),
        ]

    async def generate(self, prompt: str):
        last_error: Exception | None = None

        for model in self.models:
            logger.info(
                "Trying model %s",
                model.name,
            )

            for attempt in range(1, 4):
                try:
                    return await model.generate(prompt)

                except RateLimitException as e:
                    last_error = e

                    logger.warning(
                        "Rate limit on model=%s attempt=%d/3 error=%s",
                        model.name,
                        attempt,
                        str(e),
                    )

                    if attempt < 3:
                        await asyncio.sleep(2 ** (attempt - 1))

                except Exception as e:
                    last_error = e

                    logger.exception(
                        "Non-retryable error on model=%s: %s",
                        model.name,
                        str(e),
                    )

                    break

            logger.warning(
                "Falling back from model=%s",
                model.name,
            )

        logger.error(
            "All models failed. Last error: %s",
            str(last_error),
        )

        raise RuntimeError(
            "All LLM providers are unavailable."
        ) from last_error