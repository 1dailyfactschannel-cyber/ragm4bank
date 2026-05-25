from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from pydantic import BaseModel
from typing import Optional
from app.utils.logging import setup_logger
from app.utils.cache import cache, make_key
from app.utils.security import sanitize_input, detect_prompt_injection
from app.utils.metrics import rag_requests_total, rag_fallback_total, rag_response_time_seconds, rag_similarity_score
from app.api.middleware.rate_limit import RateLimiter
import time
import json

router = APIRouter()
logger = setup_logger()

chat_rate_limit = RateLimiter(requests_per_minute=10)


class ChatRequest(BaseModel):
    tg_user_id: int
    question: str


class ChatResponse(BaseModel):
    answer: str
    status: str  # ANSWERED / FALLBACK_OPERATOR
    similarity_score: Optional[float] = None
    response_time_ms: Optional[int] = None


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(chat_rate_limit)
):
    """
    Основной эндпоинт для чата с ботом
    """
    start_time = time.time()

    # Sanitize input
    question = sanitize_input(request.question)
    if not question:
        raise HTTPException(status_code=400, detail="Question is empty")

    # Prompt injection check
    if detect_prompt_injection(question):
        raise HTTPException(status_code=400, detail="Invalid input detected")

    # Check cache
    cache_key = make_key("chat", question.lower().strip())
    cached = await cache.get(cache_key)
    if cached:
        logger.info("Returning cached response")
        data = json.loads(cached)
        rag_requests_total.labels(status="cached").inc()
        return ChatResponse(**data)

    try:
        from app.rag.embeddings.ollama_embeddings import OllamaEmbeddings
        from app.rag.retrieval.retriever import Retriever
        from app.rag.generation.generator import ResponseGenerator
        from app.prompts.system_prompt import SYSTEM_PROMPT
        from app.db.models.models import ChatLog, FallbackQueue
        import uuid
        from datetime import datetime
        
        # 1. Создаем эмбеддинг вопроса
        embeddings = OllamaEmbeddings()
        question_embedding = await embeddings.embed_text(request.question)
        
        # 2. Ищем похожие чанки
        retriever = Retriever()
        chunks_with_scores = await retriever.search_similar_chunks(
            db, 
            question_embedding
        )
        
        # 3. Проверяем similarity threshold
        if not chunks_with_scores or chunks_with_scores[0][1] < 0.65:
            # Fallback на оператора
            chat_log = ChatLog(
                id=uuid.uuid4(),
                tg_user_id=request.tg_user_id,
                question=request.question,
                answer="Я не нашел точной информации по вашему вопросу в актуальной базе знаний. Ваш запрос передан оператору, который свяжется с вами в ближайшее время. [ПЕРЕДАТЬ_ОПЕРАТОРУ]",
                status="FALLBACK_OPERATOR",
                similarity_score=chunks_with_scores[0][1] if chunks_with_scores else 0.0,
                response_time_ms=int((time.time() - start_time) * 1000),
                created_at=datetime.utcnow()
            )
            db.add(chat_log)
            await db.flush()
            
            fallback = FallbackQueue(
                id=uuid.uuid4(),
                chat_log_id=chat_log.id,
                tg_user_id=request.tg_user_id,
                question=request.question,
                status="PENDING",
                created_at=datetime.utcnow()
            )
            db.add(fallback)
            await db.commit()

            # Notify operators via WebSocket
            from app.main import notify_fallback_created
            await notify_fallback_created(str(fallback.id), request.question, request.tg_user_id)

            response_data = ChatResponse(
                answer=chat_log.answer,
                status="FALLBACK_OPERATOR",
                similarity_score=chat_log.similarity_score,
                response_time_ms=chat_log.response_time_ms
            )
            await cache.set(cache_key, response_data.model_dump_json(), ttl=86400)
            rag_fallback_total.inc()
            rag_requests_total.labels(status="fallback").inc()
            rag_response_time_seconds.observe(time.time() - start_time)
            if chat_log.similarity_score is not None:
                rag_similarity_score.observe(chat_log.similarity_score)
            return response_data
        
        # 4. Формируем контекст
        context = await retriever.get_context_from_chunks(chunks_with_scores)
        
        # 5. Генерируем ответ
        generator = ResponseGenerator()
        answer = await generator.generate_response(
            SYSTEM_PROMPT,
            context,
            request.question
        )
        
        # 6. Логируем
        response_time_ms = int((time.time() - start_time) * 1000)
        chat_log = ChatLog(
            id=uuid.uuid4(),
            tg_user_id=request.tg_user_id,
            question=request.question,
            answer=answer,
            status="ANSWERED",
            similarity_score=chunks_with_scores[0][1],
            response_time_ms=response_time_ms,
            created_at=datetime.utcnow()
        )
        db.add(chat_log)
        await db.commit()
        
        response_data = ChatResponse(
            answer=answer,
            status="ANSWERED",
            similarity_score=chunks_with_scores[0][1],
            response_time_ms=response_time_ms
        )
        await cache.set(cache_key, response_data.model_dump_json(), ttl=86400)
        rag_requests_total.labels(status="answered").inc()
        rag_response_time_seconds.observe(time.time() - start_time)
        rag_similarity_score.observe(chunks_with_scores[0][1])
        return response_data
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
