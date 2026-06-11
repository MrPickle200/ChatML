from app.services.chunking_service import ChunkingService

def test_chunk_text():
    service = ChunkingService()

    chunks = service.chunk_text(
        text="hello world " * 1000,
        document_id="doc1"
    )

    assert len(chunks) > 1
    assert chunks[0].document_id == "doc1"

test_chunk_text()