import httpx
from app.config import settings
from app.utils.logging import setup_logger
from app.utils.retry import async_retry

logger = setup_logger()


class ResponseGenerator:
    def __init__(self):
        self.ollama_url = f"{settings.OLLAMA_URL}/api/generate"
        self.model = settings.OLLAMA_LLM_MODEL

    @async_retry(max_retries=3, backoff_base=1.0, exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def generate_response(
        self,
        system_prompt: str,
        context: str,
        question: str
    ) -> str:
        """
        Генерирует ответ используя RAG контекст с retry logic.
        """
        prompt = f"""{system_prompt}

⏺ КОНТЕКСТ ДЛЯ ОТВЕТА:
{context}

⏺ ВОПРОС КЛИЕНТА:
{question}"""

        async with httpx.AsyncClient(timeout=35.0) as client:
            response = await client.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 1024
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            answer = data.get("response", "")

            logger.info(f"Generated response of length {len(answer)}")
            return answer
