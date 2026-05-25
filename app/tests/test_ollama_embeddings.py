import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.rag.embeddings.ollama_embeddings import OllamaEmbeddings


class TestOllamaEmbeddings:
    @pytest.mark.asyncio
    async def test_embed_text_success(self):
        emb = OllamaEmbeddings()
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status = lambda: None
            mock_response.json = lambda: {"embedding": [0.1, 0.2, 0.3]}
            mock_post.return_value = mock_response

            result = await emb.embed_text("test")
            assert result == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_embed_batch(self):
        emb = OllamaEmbeddings()
        with patch.object(emb, "embed_text", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1]
            results = await emb.embed_batch(["a", "b", "c"], batch_size=2)
            assert len(results) == 3
            assert all(r == [0.1] for r in results)
