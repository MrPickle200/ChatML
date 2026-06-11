from app.models.chunk import Chunk
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings
import uuid

class ChunkingService:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size = settings.chunk_size,
            chunk_overlap = settings.chunk_overlap
        )

    def chunk_text(self, text: str, document_id: str):
        texts = self.splitter.split_text(text)
        chunks = []
        for chunk_idx, text_chunk in enumerate(texts):
            chunks.append(
                Chunk(
                    chunk_id= str(uuid.uuid4()),
                    chunk_index= chunk_idx,
                    document_id= document_id,
                    chunk_text= text_chunk
                )
            )
        return chunks
    
