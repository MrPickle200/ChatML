from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.api.chat import get_chat_service
from app.main import app
from app.models.chat import ChatResponse


def test_chat_endpoint_preserves_public_response_contract():
    chat_service = MagicMock()
    chat_service.generate = AsyncMock(
        return_value=ChatResponse(
            answer="Generated answer",
            sources=[],
            conversation_id="conversation-1",
        )
    )

    async def override_chat_service():
        return chat_service

    app.dependency_overrides[get_chat_service] = override_chat_service
    try:
        response = TestClient(app).post(
            "/chat/chat",
            params={
                "question": "What is ChatML?",
                "dataset_id": "dataset-1",
                "conversation_id": "conversation-1",
            },
        )
    finally:
        app.dependency_overrides.pop(get_chat_service, None)

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Generated answer",
        "sources": [],
        "conversation_id": "conversation-1",
    }
    chat_service.generate.assert_awaited_once_with(
        "What is ChatML?",
        "dataset-1",
        "conversation-1",
    )
