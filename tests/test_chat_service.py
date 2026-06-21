import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.services.chat_service import ChatService
from app.models.chat import Source, ChatResponse
from app.models.retrieved_chunk import RetrievedChunk
from app.prompts.blank import BlankPrompt
from app.prompts.simple import SimplePrompt

def test_chat_service_build_source():
    service = ChatService(None, None, None, None, None)
    
    retrieval_results = [
        RetrievedChunk(
            chunk_id="c1",
            document_id="d1",
            dataset_id="ds1",
            chunk_text="hello",
            score=0.9
        ),
        RetrievedChunk(
            chunk_id="c2",
            document_id="d2",
            dataset_id=None,
            chunk_text="world",
            score=0.8
        )
    ]
    
    sources = service._build_source(retrieval_results)
    
    assert len(sources) == 2
    
    assert sources[0].chunk_id == "c1"
    assert sources[0].document_id == "d1"
    assert sources[0].dataset_id == "ds1"
    
    assert sources[1].chunk_id == "c2"
    assert sources[1].document_id == "d2"
    assert sources[1].dataset_id is None

def test_chat_service_generate_success_with_results():
    mock_retrieval_service = MagicMock()
    mock_retrieval_service.search = AsyncMock(return_value=[
        RetrievedChunk(
            chunk_id="c1",
            document_id="d1",
            dataset_id="ds1",
            chunk_text="hello",
            score=0.9
        ),
        RetrievedChunk(
            chunk_id="c2",
            document_id="d2",
            dataset_id="ds1",
            chunk_text="world",
            score=0.85
        )
    ])
    
    mock_llm_service = MagicMock()
    mock_llm_service.generate = AsyncMock(side_effect=[
        "standalone: What is this?",
        "This is the generated answer."
    ])
    
    mock_prompt = MagicMock()
    mock_prompt.generate_prompt.return_value = "Mocked full prompt text"
    
    mock_conversation_service = MagicMock()
    mock_conversation_service.get_history_message = AsyncMock(return_value=[])
    mock_conversation_service.add_message = AsyncMock()
    mock_conversation_service.create_conversation = AsyncMock()
    
    mock_context_builder = MagicMock()
    mock_context_builder.build_context = AsyncMock(return_value=("hello\nworld", "history context"))

    service = ChatService(
        retrieval_service=mock_retrieval_service,
        conversation_service=mock_conversation_service,
        llm_service=mock_llm_service,
        context_builder_service=mock_context_builder,
        prompt=mock_prompt
    )
    
    async def run_test():
        response = await service.generate(question="What is this?", dataset_id="ds1", conversation_id="conv1")
        
        # Verify result
        assert isinstance(response, ChatResponse)
        assert response.answer == "This is the generated answer."
        assert len(response.sources) == 2
        
        # Verify retrieval service call
        mock_retrieval_service.search.assert_called_once_with(query="standalone: What is this?", dataset_id="ds1")
        
        # Verify prompt generation
        mock_prompt.generate_prompt.assert_called_once_with("standalone: What is this?", "hello\nworld", "history context")
        
        # Verify LLM generation calls
        assert mock_llm_service.generate.call_count == 2
        
        # Verify original prompt was not replaced
        assert service.prompt == mock_prompt

    asyncio.run(run_test())

def test_chat_service_generate_empty_results():
    mock_retrieval_service = MagicMock()
    mock_retrieval_service.search = AsyncMock(return_value=[])
    
    mock_llm_service = MagicMock()
    mock_llm_service.generate = AsyncMock(side_effect=[
        "standalone: Where is the data?",
        "Fallback answer."
    ])
    
    # We start with a SimplePrompt (or any mock prompt)
    initial_prompt = SimplePrompt()
    
    mock_conversation_service = MagicMock()
    mock_conversation_service.get_history_message = AsyncMock(return_value=[])
    mock_conversation_service.add_message = AsyncMock()
    mock_conversation_service.create_conversation = AsyncMock()
    
    mock_context_builder = MagicMock()
    mock_context_builder.build_context = AsyncMock(return_value=("", "history context"))

    service = ChatService(
        retrieval_service=mock_retrieval_service,
        conversation_service=mock_conversation_service,
        llm_service=mock_llm_service,
        context_builder_service=mock_context_builder,
        prompt=initial_prompt
    )
    
    async def run_test():
        response = await service.generate(question="Where is the data?", dataset_id="ds1", conversation_id="conv1")
        
        # Verify result
        assert isinstance(response, ChatResponse)
        assert response.answer == "Fallback answer."
        assert len(response.sources) == 0
        
        # Verify retrieval service call
        mock_retrieval_service.search.assert_called_once_with(query="standalone: Where is the data?", dataset_id="ds1")
        
        # Verify prompt became BlankPrompt
        assert isinstance(service.prompt, BlankPrompt)
        
        # Verify LLM generation call
        expected_blank_prompt = service.prompt.generate_prompt("standalone: Where is the data?", "", "history context")
        mock_llm_service.generate.assert_any_call(expected_blank_prompt)

    asyncio.run(run_test())

if __name__ == "__main__":
    test_chat_service_build_source()
    test_chat_service_generate_success_with_results()
    test_chat_service_generate_empty_results()
    print("ChatService tests passed successfully!")
