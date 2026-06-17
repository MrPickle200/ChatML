from google import genai
from google.genai import types
from dotenv import load_dotenv
from abc import ABC, abstractmethod
from fastapi import HTTPException
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
import asyncio
import torch

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
                model="gemini-3.1-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            return response.text.strip()    
        except Exception as e:
            raise HTTPException(status_code=500, detail= str(e))
        

class Qwen25SmolService(LLMService):
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(
            "Qwen/Qwen2.5-0.5B-Instruct",
            trust_remote_code=True,
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen2.5-0.5B-Instruct",
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto",
            trust_remote_code=True,
        )
        self.model.eval()

    def _sync_generate(self, prompt: str) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        with torch.inference_mode():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=False,
                temperature=None,
                top_p=None,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        generated_ids = output_ids[0][inputs["input_ids"].shape[-1]:]
        return self.tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

    async def generate(self, prompt: str) -> str:
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_generate, prompt)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))