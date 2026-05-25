import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.rag.generation.generator import ResponseGenerator


class TestGenerator:
    @pytest.mark.asyncio
    async def test_generate_response_success(self):
        gen = ResponseGenerator()
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status = lambda: None
            mock_response.json = lambda: {"response": "Test answer"}
            mock_post.return_value = mock_response

            answer = await gen.generate_response("system", "context", "question")
            assert answer == "Test answer"
