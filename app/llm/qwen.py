from app.llm.base import LLMService
from transformers import AutoTokenizer, AutoModelForCausalLM
from fastapi import HTTPException
import torch
import asyncio


class Qwen25Smol(LLMService):
    def __init__(self, model : str = "Qwen/Qwen2.5-0.5B-Instruct"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(
            "Qwen/Qwen2.5-0.5B-Instruct",
            trust_remote_code=True,
        )
        self.name = model
        self.model = AutoModelForCausalLM.from_pretrained(
            model,
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