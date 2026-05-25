from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownTextSplitter
from typing import List
from app.config import settings


class ChunkingStrategy:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        self.markdown_splitter = MarkdownTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
    
    def chunk_text(self, text: str, file_type: str = "txt") -> List[str]:
        """
        Разделяет текст на чанки в зависимости от типа файла
        """
        if file_type.lower() in ["md", "markdown"]:
            chunks = self.markdown_splitter.split_text(text)
        else:
            chunks = self.text_splitter.split_text(text)
        
        # Фильтруем слишком маленькие чанки
        min_chunk_size = 200
        chunks = [chunk for chunk in chunks if len(chunk.strip()) >= min_chunk_size]
        
        return chunks
    
    def chunk_with_metadata(self, text: str, file_type: str = "txt") -> List[dict]:
        """
        Разделяет текст и возвращает чанки с метаданными
        """
        chunks = self.chunk_text(text, file_type)
        
        return [
            {
                "chunk_text": chunk,
                "chunk_index": i,
                "metadata": {
                    "file_type": file_type,
                    "chunk_size": len(chunk)
                }
            }
            for i, chunk in enumerate(chunks)
        ]
