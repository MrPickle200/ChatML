from app.prompts.base import BasePrompt

class BlankPrompt(BasePrompt):
    def __init__(self):
        super().__init__()
    
    def generate_prompt(self, question: str, context: str, history_context: str | None = None) -> str:
        prompt = f"""
            Return: The provided documents do not contain any information about your question.
        """
        return prompt
        