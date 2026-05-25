from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.models import AuditLog
import uuid
from datetime import datetime
from app.utils.logging import setup_logger

logger = setup_logger()


async def log_audit(
    db: AsyncSession,
    action: str,
    user_id: str = None,
    resource_type: str = None,
    resource_id: str = None,
    details: dict = None,
    ip_address: str = None
):
    """
    Создает запись в audit_logs.
    """
    try:
        audit = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            created_at=datetime.utcnow()
        )
        db.add(audit)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")
        await db.rollback()
