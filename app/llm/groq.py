from app.llm.base import LLMService
from dotenv import load_dotenv
from fastapi import HTTPException
from groq import AsyncGroq, RateLimitError
from app.core.exceptions import RateLimitException
import os

class GroqModel(LLMService):
    def __init__(self, model : str = "llama-3.3-70b-versatile"):
        load_dotenv()
        GROQ_API_KEY = os.getenv("GROQ")
        if not GROQ_API_KEY:
            raise ValueError("Missing GROQ API key in environment variables")

        self.model = model
        self.name = model
        self.client = AsyncGroq(api_key=GROQ_API_KEY)

    async def generate(self, prompt: str) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,  # choose Groq model
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content.strip()
        
        except RateLimitError as e:
            raise RateLimitException(str(e))
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))