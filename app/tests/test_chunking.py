import pytest
from app.rag.chunking.strategies import ChunkingStrategy


class TestChunkingStrategy:
    def test_chunk_text_basic(self):
        strategy = ChunkingStrategy()
        text = "This is a test. " * 100  # Create long text
        
        chunks = strategy.chunk_text(text)
        
        assert len(chunks) > 0
        assert all(len(chunk) >= 200 for chunk in chunks)
    
    def test_chunk_text_short(self):
        strategy = ChunkingStrategy()
        text = "Short text"
        
        chunks = strategy.chunk_text(text)
        
        # Too short, should be filtered
        assert len(chunks) == 0
    
    def test_chunk_with_metadata(self):
        strategy = ChunkingStrategy()
        text = "Test content. " * 100
        
        chunks = strategy.chunk_with_metadata(text)
        
        assert len(chunks) > 0
        assert "chunk_text" in chunks[0]
        assert "chunk_index" in chunks[0]
        assert "metadata" in chunks[0]
    
    def test_chunk_index_sequential(self):
        strategy = ChunkingStrategy()
        text = "Test content. " * 100
        
        chunks = strategy.chunk_with_metadata(text)
        
        for i, chunk in enumerate(chunks):
            assert chunk["chunk_index"] == i
