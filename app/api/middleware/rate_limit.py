import time
from fastapi import Request, HTTPException
from collections import defaultdict
from typing import Dict, Tuple

# In-memory rate limit storage: {key: [(timestamp, count), ...]}
_rate_limits: Dict[str, list] = defaultdict(list)


class RateLimiter:
    """Simple in-memory rate limiter. For production, replace with Redis."""

    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.window = 60  # seconds

    async def __call__(self, request: Request):
        key = self._get_key(request)
        now = time.time()

        # Clean old entries
        window_start = now - self.window
        _rate_limits[key] = [t for t in _rate_limits[key] if t > window_start]

        if len(_rate_limits[key]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Пожалуйста, подождите перед следующим сообщением."
            )

        _rate_limits[key].append(now)

    def _get_key(self, request: Request) -> str:
        client_ip = request.client.host if request.client else "unknown"
        return f"{client_ip}:{request.url.path}"


class UserRateLimiter(RateLimiter):
    """Rate limiter per user (based on tg_user_id in body or IP fallback)."""

    def _get_key(self, request: Request) -> str:
        client_ip = request.client.host if request.client else "unknown"
        # For chat endpoint, try to extract tg_user_id from body (best effort)
        return f"user:{client_ip}"
