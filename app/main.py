from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.api.routes import chat, documents, analytics, auth, fallback
from app.api.middleware.error_handler import validation_exception_handler, sqlalchemy_exception_handler, generic_exception_handler
from app.db.database import init_db, close_db, engine
from app.utils.logging import setup_logger
from app.utils.metrics import metrics_response
from app.utils.alerting import check_alerts
from app.config import settings
from contextlib import asynccontextmanager
import httpx

logger = setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up RAG system...")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down RAG system...")
    await close_db()


app = FastAPI(
    title="RAG E-commerce Support System",
    description="AI-powered support system for trading acquiring",
    version="2.0.0",
    lifespan=lifespan
)

# Error handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# CORS
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")] if settings.CORS_ORIGINS != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(fallback.router, prefix="/api/fallback", tags=["fallback"])

# WebSocket for fallback notifications
from fastapi import WebSocket, WebSocketDisconnect

fallback_connections: dict = {}

@app.websocket("/api/ws/fallback/{operator_id}")
async def websocket_fallback(websocket: WebSocket, operator_id: str):
    await websocket.accept()
    fallback_connections[operator_id] = websocket
    logger.info(f"Operator {operator_id} connected to fallback websocket")
    try:
        while True:
            # Keep connection alive, wait for ping or messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        fallback_connections.pop(operator_id, None)
        logger.info(f"Operator {operator_id} disconnected from fallback websocket")


async def notify_fallback_created(fallback_id: str, question: str, tg_user_id: int):
    """Notify all connected operators about new fallback"""
    message = {
        "type": "new_fallback",
        "fallback_id": fallback_id,
        "question": question,
        "tg_user_id": tg_user_id
    }
    import json
    disconnected = []
    for operator_id, ws in fallback_connections.items():
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            disconnected.append(operator_id)
    for oid in disconnected:
        fallback_connections.pop(oid, None)


@app.get("/health")
async def health_check():
    """Общий health check endpoint"""
    db_status = "ok"
    ollama_status = "ok"
    status = "healthy"

    # Check DB
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "unhealthy"
        status = "degraded"
        logger.error(f"DB health check failed: {e}")

    # Check Ollama
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            if response.status_code != 200:
                ollama_status = "unhealthy"
                status = "degraded"
    except Exception as e:
        ollama_status = "unhealthy"
        status = "degraded"
        logger.error(f"Ollama health check failed: {e}")

    return {
        "status": status,
        "services": {
            "api": "ok",
            "db": db_status,
            "ollama": ollama_status
        }
    }


@app.get("/health/db")
async def health_db():
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "db"}
    except Exception as e:
        logger.error(f"DB health check failed: {e}")
        return {"status": "unhealthy", "service": "db"}


@app.get("/health/ollama")
async def health_ollama():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                return {"status": "healthy", "service": "ollama"}
            else:
                return {"status": "unhealthy", "service": "ollama"}
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        return {"status": "unhealthy", "service": "ollama"}


@app.get("/metrics")
async def metrics():
    return metrics_response()


@app.get("/")
async def root():
    return {
        "message": "RAG E-commerce Support System API",
        "version": "2.0.0",
        "docs": "/docs"
    }
