from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.db.models.models import Document
from app.rag.pipeline import DocumentProcessor
from app.api.middleware.auth import get_current_user
from app.api.middleware.rate_limit import RateLimiter
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import os
from app.utils.logging import setup_logger
from app.utils.cache import cache
from app.utils.audit import log_audit
from app.utils.security import sanitize_input
from fastapi import Request

router = APIRouter()
logger = setup_logger()

admin_rate_limit = RateLimiter(requests_per_minute=100)

UPLOAD_DIR = "/app/data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class DocumentResponse(BaseModel):
    id: str
    title: str
    upload_date: datetime
    is_active: bool
    version: int
    chunks_count: Optional[int] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int


class UpdateStatusRequest(BaseModel):
    is_active: bool


@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
    _: None = Depends(admin_rate_limit)
):
    """
    Загрузка документа и его обработка
    """
    try:
        # Валидация файла
        allowed_extensions = ['.pdf', '.docx', '.txt', '.md']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Сохраняем файл
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_ext}")
        
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(status_code=400, detail="File too large (max 50MB)")
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Обрабатываем документ
        processor = DocumentProcessor()
        result = await processor.process_document(
            db,
            file_path,
            title,
            uploaded_by="admin"
        )
        
        logger.info(f"Document uploaded and processed: {title}")
        await cache.clear_pattern("chat:*")
        await cache.delete("analytics:dashboard")

        await log_audit(
            db=db,
            action="DOCUMENT_UPLOAD",
            user_id=current_user,
            resource_type="document",
            resource_id=str(result["document_id"]),
            details={"title": sanitize_input(title), "filename": file.filename},
            ip_address=request.client.host if request.client else None
        )

        return {
            "document_id": result["document_id"],
            "chunks_count": result["chunks_count"],
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    per_page: int = 20,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
    _: None = Depends(admin_rate_limit)
):
    """
    Список всех документов
    """
    try:
        query = select(Document)
        
        if is_active is not None:
            query = query.where(Document.is_active == is_active)
        
        query = query.order_by(Document.upload_date.desc())
        
        # Total count
        count_query = select(Document)
        if is_active is not None:
            count_query = count_query.where(Document.is_active == is_active)
        total_result = await db.execute(count_query)
        total = len(total_result.scalars().all())
        
        # Pagination
        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(query)
        documents = result.scalars().all()
        
        return {
            "documents": [
                DocumentResponse(
                    id=str(doc.id),
                    title=doc.title,
                    upload_date=doc.upload_date,
                    is_active=doc.is_active,
                    version=doc.version,
                    chunks_count=len(doc.chunks)
                )
                for doc in documents
            ],
            "total": total
        }
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{doc_id}")
async def update_document_status(
    request: Request,
    doc_id: str,
    req: UpdateStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
    _: None = Depends(admin_rate_limit)
):
    """
    Обновление статуса документа (soft delete)
    """
    try:
        result = await db.execute(select(Document).where(Document.id == doc_id))
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        document.is_active = req.is_active
        await db.commit()

        await log_audit(
            db=db,
            action="DOCUMENT_PATCH",
            user_id=current_user,
            resource_type="document",
            resource_id=doc_id,
            details={"is_active": req.is_active},
            ip_address=request.client.host if request.client else None
        )

        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{doc_id}")
async def delete_document(
    request: Request,
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
    _: None = Depends(admin_rate_limit)
):
    """
    Удаление документа и его чанков
    """
    try:
        result = await db.execute(select(Document).where(Document.id == doc_id))
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Удаляем файл
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Удаляем из БД (cascade удалит чанки)
        await db.delete(document)
        await db.commit()
        
        logger.info(f"Document deleted: {document.title}")
        await cache.clear_pattern("chat:*")
        await cache.delete("analytics:dashboard")

        await log_audit(
            db=db,
            action="DOCUMENT_DELETE",
            user_id=current_user,
            resource_type="document",
            resource_id=doc_id,
            details={"title": document.title},
            ip_address=request.client.host if request.client else None
        )

        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
