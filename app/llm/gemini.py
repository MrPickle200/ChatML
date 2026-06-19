from app.llm.base import LLMService
from google import genai
from google.genai.errors import ClientError
from fastapi import HTTPException
from app.core.exceptions import RateLimitException
from dotenv import load_dotenv
import os


class Gemini(LLMService):
    def __init__(self, model : str = "gemini-3.1-flash-lite"):
        load_dotenv()
        GEMINI_API_KEY = os.getenv("GEMINI")
        if not GEMINI_API_KEY:
            raise ValueError("Missing GEMINI API key in environment variables")
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        self.async_client = client.aio
        self.model = model
        self.name = model

    async def generate(self, prompt: str) -> str:
        try:
            response = await self.async_client.models.generate_content(
                model=self.model, 
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    thinking_config=genai.types.ThinkingConfig(thinking_budget=0)
                )
            )
            return response.text.strip()    
        
        except ClientError as e:
            if getattr(e, "code", None) == 429:
                raise RateLimitException(str(e))
            raise

        except Exception as e:
            raise HTTPException(status_code=500, detail= str(e))