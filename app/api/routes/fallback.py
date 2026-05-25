from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.db.models.models import FallbackQueue, ChatLog
from app.api.middleware.auth import get_current_user
from app.api.middleware.rate_limit import RateLimiter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.utils.logging import setup_logger

router = APIRouter()
logger = setup_logger()

admin_rate_limit = RateLimiter(requests_per_minute=100)


class AssignRequest(BaseModel):
    operator_id: str


class FallbackResponse(BaseModel):
    id: str
    chat_log_id: str
    tg_user_id: int
    question: str
    status: str
    assigned_to: Optional[str]
    created_at: datetime


@router.get("/", response_model=list[FallbackResponse])
async def list_fallbacks(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
    _: None = Depends(admin_rate_limit)
):
    query = select(FallbackQueue)
    if status:
        query = query.where(FallbackQueue.status == status)
    query = query.order_by(FallbackQueue.created_at.desc())
    result = await db.execute(query)
    items = result.scalars().all()
    return [
        FallbackResponse(
            id=str(item.id),
            chat_log_id=str(item.chat_log_id),
            tg_user_id=item.tg_user_id,
            question=item.question,
            status=item.status,
            assigned_to=item.assigned_to,
            created_at=item.created_at
        )
        for item in items
    ]


@router.post("/{fallback_id}/assign")
async def assign_fallback(
    fallback_id: str,
    request: AssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
    _: None = Depends(admin_rate_limit)
):
    result = await db.execute(select(FallbackQueue).where(FallbackQueue.id == fallback_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Fallback not found")

    item.status = "IN_PROGRESS"
    item.assigned_to = request.operator_id
    await db.commit()

    logger.info(f"Fallback {fallback_id} assigned to {request.operator_id}")
    return {"status": "assigned"}


@router.post("/{fallback_id}/resolve")
async def resolve_fallback(
    fallback_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
    _: None = Depends(admin_rate_limit)
):
    result = await db.execute(select(FallbackQueue).where(FallbackQueue.id == fallback_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Fallback not found")

    item.status = "RESOLVED"
    item.resolved_at = datetime.utcnow()
    await db.commit()

    logger.info(f"Fallback {fallback_id} resolved")
    return {"status": "resolved"}
