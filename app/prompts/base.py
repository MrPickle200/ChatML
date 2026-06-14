from abc import ABC, abstractmethod

class BasePrompt(ABC):
    @abstractmethod
    def generate_prompt(self, question: str, context: str) -> str:
        pass