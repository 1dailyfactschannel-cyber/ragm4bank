import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, Float, BigInteger, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import Base
from pgvector.sqlalchemy import Vector


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    uploaded_by = Column(String(100))

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(768))
    chunk_metadata = Column(JSON, default=dict)

    document = relationship("Document", back_populates="chunks")


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tg_user_id = Column(BigInteger, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    status = Column(String(20), default="ANSWERED")  # ANSWERED / FALLBACK_OPERATOR
    similarity_score = Column(Float)
    response_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    fallback = relationship("FallbackQueue", back_populates="chat_log", uselist=False)


class FallbackQueue(Base):
    __tablename__ = "fallback_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_log_id = Column(UUID(as_uuid=True), ForeignKey("chat_logs.id"), nullable=False)
    tg_user_id = Column(BigInteger, nullable=False)
    question = Column(Text, nullable=False)
    status = Column(String(20), default="PENDING")  # PENDING / IN_PROGRESS / RESOLVED
    assigned_to = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

    chat_log = relationship("ChatLog", back_populates="fallback")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100))
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    details = Column(JSON, default=dict)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)
