"""In-memory per-IP rate limiter. Free, no external dependency (no Redis needed) —
fine for a single-process deployment. Protects the free NIM quota (~40 req/min)
from being exhausted by one misbehaving client.
"""
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings

settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int | None = None):
        super().__init__(app)
        self.limit = requests_per_minute or settings.rate_limit_per_minute
        self.window_seconds = 60
        self._hits: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        hits = self._hits[client_ip]

        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()

        if len(hits) >= self.limit:
            # Middleware sits outside FastAPI's exception-handling layer, so raising
            # HTTPException here would NOT be converted to a response — it must be
            # returned directly.
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again shortly."},
            )

        hits.append(now)
        return await call_next(request)
