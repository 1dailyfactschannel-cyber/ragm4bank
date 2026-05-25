import httpx
from typing import List
from app.config import settings
from app.utils.logging import setup_logger
from app.utils.retry import async_retry

logger = setup_logger()


class OllamaEmbeddings:
    def __init__(self):
        self.ollama_url = f"{settings.OLLAMA_URL}/api/embeddings"
        self.model = settings.OLLAMA_EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION

    @async_retry(max_retries=3, backoff_base=1.0, exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def embed_text(self, text: str) -> List[float]:
        """
        Создает эмбеддинг для одного текста с retry logic.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": text
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]

    async def embed_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """
        Создает эмбеддинги для батча текстов
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = []

            for text in batch:
                try:
                    embedding = await self.embed_text(text)
                    batch_embeddings.append(embedding)
                except Exception as e:
                    logger.error(f"Error embedding text at index {i}: {str(e)}")
                    batch_embeddings.append([0.0] * self.dimension)

            embeddings.extend(batch_embeddings)

            logger.info(f"Embedded batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")

        return embeddings
