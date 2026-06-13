import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.services.ingestion_service import IngestionService
from app.models.document import Document
from app.models.chunk import Chunk
from app.models.parse_element import ParsedElement

def test_ingest_document():
    # Setup mocks
    mock_parsing = MagicMock()
    mock_parsing.parse.return_value = [
        ParsedElement(text="Line 1", page_number=1, source="doc.pdf"),
        ParsedElement(text="Line 2", page_number=2, source="doc.pdf")
    ]
    
    mock_chunking = MagicMock()
    mock_chunking.chunk_text.return_value = [
        Chunk(chunk_id="chunk1", document_id="doc1", chunk_index=0, chunk_text="Line 1"),
        Chunk(chunk_id="chunk2", document_id="doc1", chunk_index=1, chunk_text="Line 2")
    ]
    
    mock_embedding = MagicMock()
    mock_embedding.embed_texts.return_value = [
        [0.1, 0.2],
        [0.3, 0.4]
    ]
    
    mock_qdrant = MagicMock()
    mock_qdrant.upsert_points = AsyncMock()

    service = IngestionService(
        parsing_service=mock_parsing,
        chunking_service=mock_chunking,
        embedding_service=mock_embedding,
        qdrant_repo=mock_qdrant
    )
    
    document = Document(
        dataset_id="dataset123",
        document_id="doc1",
        file_path="dummy_path/doc.pdf",
        filename="doc.pdf",
        version=1
    )

    async def run_test():
        res = await service.ingest_document(document)
        assert res["document_id"] == "doc1"
        assert res["chunks_created"] == 2
        assert res["points_created"] == 2
        
        # Verify dependencies were called correctly
        mock_parsing.parse.assert_called_once_with("dummy_path/doc.pdf")
        mock_chunking.chunk_text.assert_called_once_with("Line 1\nLine 2", "doc1")
        mock_embedding.embed_texts.assert_called_once_with(["Line 1", "Line 2"])
        
        # Verify upsert was called
        mock_qdrant.upsert_points.assert_called_once()
        points_arg = mock_qdrant.upsert_points.call_args[0][0]
        assert len(points_arg) == 2
        assert points_arg[0].id == "chunk1"
        assert points_arg[0].vector == [0.1, 0.2]
        assert points_arg[0].payload["dataset_id"] == "dataset123"
        assert points_arg[0].payload["document_id"] == "doc1"
        assert points_arg[0].payload["chunk_text"] == "Line 1"
        
    asyncio.run(run_test())

def test_delete_document():
    mock_parsing = MagicMock()
    mock_chunking = MagicMock()
    mock_embedding = MagicMock()
    mock_qdrant = MagicMock()
    mock_qdrant.delete_by_document_id = AsyncMock()

    service = IngestionService(
        parsing_service=mock_parsing,
        chunking_service=mock_chunking,
        embedding_service=mock_embedding,
        qdrant_repo=mock_qdrant
    )

    async def run_test():
        await service.delete_document("doc1")
        mock_qdrant.delete_by_document_id.assert_called_once_with("doc1")

    asyncio.run(run_test())

def test_update_document():
    mock_parsing = MagicMock()
    mock_parsing.parse.return_value = []
    mock_chunking = MagicMock()
    mock_chunking.chunk_text.return_value = []
    mock_embedding = MagicMock()
    mock_embedding.embed_texts.return_value = []
    
    mock_qdrant = MagicMock()
    mock_qdrant.delete_by_document_id = AsyncMock()
    mock_qdrant.upsert_points = AsyncMock()

    service = IngestionService(
        parsing_service=mock_parsing,
        chunking_service=mock_chunking,
        embedding_service=mock_embedding,
        qdrant_repo=mock_qdrant
    )

    document = Document(
        dataset_id="dataset123",
        document_id="doc1",
        file_path="dummy_path/doc.pdf",
        filename="doc.pdf",
        version=2
    )

    async def run_test():
        await service.update_document(document)
        mock_qdrant.delete_by_document_id.assert_called_once_with("doc1")
        mock_qdrant.upsert_points.assert_called_once_with([])

    asyncio.run(run_test())

if __name__ == "__main__":
    test_ingest_document()
    test_delete_document()
    test_update_document()
    print("IngestionService tests passed successfully!")
