import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.services.chat_service import ChatService
from app.models.chat import Source, ChatResponse
from app.models.retrieved_chunk import RetrievedChunk
from app.prompts.blank import BlankPrompt
from app.prompts.simple import SimplePrompt

def test_chat_service_build_source():
    # Setup service with dummy inputs (None) since _build_source doesn't use them
    service = ChatService(None, None, None)
    
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
    mock_llm_service.generate = AsyncMock(return_value="This is the generated answer.")
    
    mock_prompt = MagicMock()
    mock_prompt.generate_prompt.return_value = "Mocked full prompt text"
    
    service = ChatService(
        retrieval_service=mock_retrieval_service,
        llm_service=mock_llm_service,
        prompt=mock_prompt
    )
    
    async def run_test():
        response = await service.generate(question="What is this?", dataset_ids=["ds1"])
        
        # Verify result
        assert isinstance(response, ChatResponse)
        assert response.answer == "This is the generated answer."
        assert len(response.sources) == 2
        
        # Verify retrieval service call
        mock_retrieval_service.search.assert_called_once_with(query="What is this?", dataset_ids=["ds1"])
        
        # Verify prompt generation
        # Context should be chunk_text joined by newline
        expected_context = "hello\nworld"
        mock_prompt.generate_prompt.assert_called_once_with("What is this?", expected_context)
        
        # Verify LLM generation call
        mock_llm_service.generate.assert_called_once_with("Mocked full prompt text")
        
        # Verify original prompt was not replaced
        assert service.prompt == mock_prompt

    asyncio.run(run_test())

def test_chat_service_generate_empty_results():
    mock_retrieval_service = MagicMock()
    mock_retrieval_service.search = AsyncMock(return_value=[])
    
    mock_llm_service = MagicMock()
    mock_llm_service.generate = AsyncMock(return_value="Fallback answer.")
    
    # We start with a SimplePrompt (or any mock prompt)
    initial_prompt = SimplePrompt()
    
    service = ChatService(
        retrieval_service=mock_retrieval_service,
        llm_service=mock_llm_service,
        prompt=initial_prompt
    )
    
    async def run_test():
        response = await service.generate(question="Where is the data?", dataset_ids=None)
        
        # Verify result
        assert isinstance(response, ChatResponse)
        assert response.answer == "Fallback answer."
        assert len(response.sources) == 0
        
        # Verify retrieval service call
        mock_retrieval_service.search.assert_called_once_with(query="Where is the data?", dataset_ids=None)
        
        # Verify prompt became BlankPrompt
        assert isinstance(service.prompt, BlankPrompt)
        
        # Verify LLM generation call
        expected_blank_prompt = service.prompt.generate_prompt("Where is the data?", "")
        mock_llm_service.generate.assert_called_once_with(expected_blank_prompt)

    asyncio.run(run_test())

if __name__ == "__main__":
    test_chat_service_build_source()
    test_chat_service_generate_success_with_results()
    test_chat_service_generate_empty_results()
    print("ChatService tests passed successfully!")
