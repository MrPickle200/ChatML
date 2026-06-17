from fastapi import HTTPException
from app.repositories.conversation_repository import ConversationRepository

class ConversationService:
    def __init__(self, repo : ConversationRepository):
        self.repo = repo

    async def create_conversation(self, conversation_metadata: dict):
        try:
            await self.repo.create_conversation(conversation_metadata)
        except Exception as e:
            raise HTTPException(status_code= 500, detail= str(e))

    async def add_message(self, message_metadata: dict):
        try:
            await self.repo.add_message(message_metadata)
        except Exception as e:
            raise HTTPException(status_code= 500, detail= str(e))

    async def get_history_message(self, conversation_id: str):
        try: 
            return await self.repo.get_history_message(conversation_id)
        except Exception as e:
            raise HTTPException(status_code= 500, detail= str(e))
        
    async def list_conversation(self):
        try:
            return await self.repo.list_conversations()
        except Exception as e:
            raise HTTPException(status_code= 500, detail= str(e))

    async def delete_conversation(self, conversation_id: str):
        try:
            return await self.repo.delete_conversation(conversation_id)
        except Exception as e:
            raise HTTPException(status_code= 500, detail= str(e))