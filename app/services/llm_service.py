from google import genai
from google.genai import types
from dotenv import load_dotenv
from abc import ABC, abstractmethod
from fastapi import HTTPException
import os

class LLMService(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        pass

class GeminiService(LLMService):
    def __init__(self):
        load_dotenv()
        GEMINI_API_KEY = os.getenv("GEMINI")
        client = genai.Client(api_key=GEMINI_API_KEY)
        self.async_client = client.aio

    async def generate(self, prompt: str) -> str:
        try:
            response = await self.async_client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            return response.text.strip()    
        except Exception as e:
            raise HTTPException(status_code=500, detail= str(e))