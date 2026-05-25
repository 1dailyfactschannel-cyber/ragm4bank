import pytest
from app.config import settings


class TestConfig:
    def test_similarity_threshold(self):
        assert settings.SIMILARITY_THRESHOLD == 0.65
    
    def test_chunk_size(self):
        assert settings.CHUNK_SIZE == 1000
    
    def test_chunk_overlap(self):
        assert settings.CHUNK_OVERLAP == 200
    
    def test_top_k(self):
        assert settings.TOP_K == 5
    
    def test_embedding_dimension(self):
        assert settings.EMBEDDING_DIMENSION == 768
    
    def test_ollama_urls(self):
        assert "ollama" in settings.OLLAMA_URL
        assert settings.OLLAMA_URL.endswith("11434")
