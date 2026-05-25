import json
import hashlib
from typing import Optional
from app.config import settings
from app.utils.logging import setup_logger

logger = setup_logger()

# Try to import redis, fallback to in-memory if not available
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class Cache:
    def __init__(self):
        self._memory = {}
        self._redis = None
        if REDIS_AVAILABLE and settings.REDIS_URL:
            try:
                self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            except Exception as e:
                logger.warning(f"Redis not available, using in-memory cache: {e}")

    async def get(self, key: str) -> Optional[str]:
        if self._redis:
            try:
                return await self._redis.get(key)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
        return self._memory.get(key)

    async def set(self, key: str, value: str, ttl: int = 3600):
        if self._redis:
            try:
                await self._redis.setex(key, ttl, value)
                return
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
        self._memory[key] = value

    async def delete(self, key: str):
        if self._redis:
            try:
                await self._redis.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
        self._memory.pop(key, None)

    async def clear_pattern(self, pattern: str):
        if self._redis:
            try:
                keys = await self._redis.keys(pattern)
                if keys:
                    await self._redis.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis clear_pattern error: {e}")
        # In-memory: simple substring match
        keys_to_remove = [k for k in self._memory if pattern.replace("*", "") in k]
        for k in keys_to_remove:
            self._memory.pop(k, None)


cache = Cache()


def make_key(prefix: str, *parts) -> str:
    content = "|".join(str(p) for p in parts)
    hash_part = hashlib.md5(content.encode()).hexdigest()
    return f"{prefix}:{hash_part}"
