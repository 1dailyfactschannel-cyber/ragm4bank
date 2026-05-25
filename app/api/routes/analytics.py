from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.database import get_db
from app.db.models.models import ChatLog, FallbackQueue
from app.api.middleware.auth import get_current_user
from app.api.middleware.rate_limit import RateLimiter
from app.utils.cache import cache
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from app.utils.logging import setup_logger
import json

router = APIRouter()
logger = setup_logger()

admin_rate_limit = RateLimiter(requests_per_minute=100)
DASHBOARD_CACHE_KEY = "analytics:dashboard"


class DashboardResponse(BaseModel):
    total_requests: int
    answered_by_bot: int
    answered_percentage: float
    fallback_to_operator: int
    fallback_percentage: float
    avg_similarity_score: float
    avg_response_time_ms: int
    top_questions: List[dict]
    fallback_queue_size: int


class LogEntry(BaseModel):
    id: str
    tg_user_id: int
    question: str
    answer: Optional[str]
    status: str
    similarity_score: Optional[float]
    created_at: datetime


class LogsResponse(BaseModel):
    logs: List[LogEntry]
    total: int


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
    _: None = Depends(admin_rate_limit)
):
    """
    Агрегированная статистика для дашборда
    """
    cached = await cache.get(DASHBOARD_CACHE_KEY)
    if cached:
        logger.info("Returning cached dashboard")
        return DashboardResponse(**json.loads(cached))

    try:
        # Общая статистика
        total_result = await db.execute(select(func.count(ChatLog.id)))
        total_requests = total_result.scalar()
        
        # ANSWERED
        answered_result = await db.execute(
            select(func.count(ChatLog.id)).where(ChatLog.status == "ANSWERED")
        )
        answered_by_bot = answered_result.scalar()
        
        # FALLBACK
        fallback_result = await db.execute(
            select(func.count(ChatLog.id)).where(ChatLog.status == "FALLBACK_OPERATOR")
        )
        fallback_to_operator = fallback_result.scalar()
        
        # Percentages
        answered_percentage = (answered_by_bot / total_requests * 100) if total_requests > 0 else 0
        fallback_percentage = (fallback_to_operator / total_requests * 100) if total_requests > 0 else 0
        
        # Average similarity score
        avg_score_result = await db.execute(
            select(func.avg(ChatLog.similarity_score))
        )
        avg_similarity_score = avg_score_result.scalar() or 0.0
        
        # Average response time
        avg_time_result = await db.execute(
            select(func.avg(ChatLog.response_time_ms))
        )
        avg_response_time_ms = int(avg_time_result.scalar() or 0)
        
        # Top questions (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        top_questions_result = await db.execute(
            select(ChatLog.question, func.count(ChatLog.id))
            .where(ChatLog.created_at >= seven_days_ago)
            .group_by(ChatLog.question)
            .order_by(func.count(ChatLog.id).desc())
            .limit(10)
        )
        top_questions = [
            {"question": q, "count": c}
            for q, c in top_questions_result.all()
        ]
        
        # Fallback queue size
        queue_size_result = await db.execute(
            select(func.count(FallbackQueue.id)).where(FallbackQueue.status == "PENDING")
        )
        fallback_queue_size = queue_size_result.scalar()
        
        result = DashboardResponse(
            total_requests=total_requests,
            answered_by_bot=answered_by_bot,
            answered_percentage=round(answered_percentage, 2),
            fallback_to_operator=fallback_to_operator,
            fallback_percentage=round(fallback_percentage, 2),
            avg_similarity_score=round(avg_similarity_score, 3),
            avg_response_time_ms=avg_response_time_ms,
            top_questions=top_questions,
            fallback_queue_size=fallback_queue_size
        )
        await cache.set(DASHBOARD_CACHE_KEY, result.model_dump_json(), ttl=300)
        return result
        
    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs", response_model=LogsResponse)
async def get_logs(
    page: int = 1,
    per_page: int = 50,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
    _: None = Depends(admin_rate_limit)
):
    """
    Пагинированный список логов диалогов
    """
    try:
        query = select(ChatLog)
        
        if date_from:
            query = query.where(ChatLog.created_at >= date_from)
        if date_to:
            query = query.where(ChatLog.created_at <= date_to)
        if status:
            query = query.where(ChatLog.status == status)
        
        query = query.order_by(ChatLog.created_at.desc())
        
        # Total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Pagination
        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return LogsResponse(
            logs=[
                LogEntry(
                    id=str(log.id),
                    tg_user_id=log.tg_user_id,
                    question=log.question,
                    answer=log.answer,
                    status=log.status,
                    similarity_score=log.similarity_score,
                    created_at=log.created_at
                )
                for log in logs
            ],
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error getting logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
