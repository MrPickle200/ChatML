from app.prompts.base import BasePrompt

class SimplePrompt(BasePrompt):
    def __init__(self):
        super().__init__()
    
    def generate_prompt(self, question: str, context: str, history_context: str | None = None) -> str:
        prompt = f"""
            === SYSTEM ===
            You are an AI Learning Assistant.

            Use the provided context to answer.

            === CONVERSATION HISTORY ===
            Conversation history:
            {history_context}

            === CURRENT QUESTION ===
            Question:
            {question}

            === RETRIEVED KNOWLEDGE ===
            Context:
            {context}

            Instruction:
            - Use the conversation history to understand references
            - If the user's question refers to something mentioned earlier, answer using that referenced entity.
            - Prefer conversation history over retrieved documents when resolving references.
        """
        return prompt
        