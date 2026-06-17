from app.prompts.base import BasePrompt

class SimplePrompt(BasePrompt):
    def __init__(self):
        super().__init__()
    
    def generate_prompt(self, question: str, context: str, history_context: str | None = None) -> str:
        prompt = f"""
            You are an AI Learning Assistant.

            Use the provided context to answer.

            Conversation history:
            {history_context}

            Context:
            {context}

            Question:
            {question}
        """
        return prompt
        