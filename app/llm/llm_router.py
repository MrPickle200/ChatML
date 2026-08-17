import asyncio
import logging
import os
from collections.abc import Sequence

from dotenv import load_dotenv

from app.llm.base import LLMService
from app.llm.nvidia import NvidiaLLM
from app.core.exceptions import RateLimitException

logger = logging.getLogger(__name__)

DEFAULT_NVIDIA_MODELS = (
    "meta/llama-3.1-8b-instruct",
    "nvidia/nemotron-mini-4b-instruct",
)


class LLMRouter(LLMService):
    name = "nvidia-router"

    def __init__(
        self,
        models: Sequence[LLMService] | None = None,
        max_attempts: int = 3,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        if models is None:
            load_dotenv()
            configured_models = os.getenv("NVIDIA_MODELS")
            model_names = (
                tuple(
                    name.strip()
                    for name in configured_models.split(",")
                    if name.strip()
                )
                if configured_models
                else DEFAULT_NVIDIA_MODELS
            )
            self.models = [NvidiaLLM(model=name) for name in model_names]
        else:
            self.models = list(models)

        if not self.models:
            raise ValueError("At least one NVIDIA model must be configured")

        self.max_attempts = max_attempts

    async def generate(self, prompt: str) -> str:
        last_error: Exception | None = None

        for model in self.models:
            logger.info(
                "Trying model %s",
                model.name,
            )

            for attempt in range(1, self.max_attempts + 1):
                try:
                    return await model.generate(prompt)

                except RateLimitException as exc:
                    last_error = exc

                    logger.warning(
                        "Rate limit on model=%s attempt=%d/%d",
                        model.name,
                        attempt,
                        self.max_attempts,
                    )

                    if attempt < self.max_attempts:
                        await asyncio.sleep(2 ** (attempt - 1))

                except Exception as exc:
                    last_error = exc

                    logger.error(
                        "Non-retryable error on model=%s error_type=%s",
                        model.name,
                        type(exc).__name__,
                    )

                    break

            logger.warning(
                "Falling back from model=%s",
                model.name,
            )

        logger.error("All configured NVIDIA models failed")

        raise RuntimeError("All NVIDIA LLM models are unavailable.") from last_error
