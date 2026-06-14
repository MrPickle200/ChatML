from app.prompts.base import BasePrompt

class SimplePrompt(BasePrompt):
    def __init__(self):
        super().__init__()
    
    def generate_prompt(self, question: str, context: str) -> str:
        prompt = f"""
            You are an AI Learning Assistant.

            Use the provided context to answer.

            Context:
            {context}

            Question:
            {question}
        """
        return prompt
        