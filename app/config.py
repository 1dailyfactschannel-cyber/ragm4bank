from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "rag_ecommerce"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/rag_ecommerce"
    
    # Ollama
    OLLAMA_URL: str = "http://ollama:11434"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_LLM_MODEL: str = "qwen2.5:7b"
    
    # JWT
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # RAG Configuration
    SIMILARITY_THRESHOLD: float = 0.65
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K: int = 5
    EMBEDDING_DIMENSION: int = 768
    
    # Bot
    BOT_TOKEN: str = ""
    BACKEND_URL: str = "http://backend:8000"
    ADMIN_CHAT_IDS: Optional[str] = None

    # Redis (optional)
    REDIS_URL: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # CORS
    CORS_ORIGINS: str = "*"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
