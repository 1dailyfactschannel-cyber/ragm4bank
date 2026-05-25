import pytest
from unittest.mock import AsyncMock, MagicMock
from app.rag.retrieval.retriever import Retriever


class TestRetriever:
    @pytest.mark.asyncio
    async def test_search_similar_chunks_empty_db(self):
        retriever = Retriever()
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await retriever.search_similar_chunks(mock_db, [0.0] * 768)
        assert result == []
