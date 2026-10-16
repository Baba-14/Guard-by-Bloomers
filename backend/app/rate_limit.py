"""Small per-instance rate limiter for public MVP endpoints.

This provides a safe baseline. Multi-region deployments should replace it with
a shared Redis/edge limiter while keeping the same response contract.
"""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class PublicRateLimitMiddleware(BaseHTTPMiddleware):
    LIMITS = {
        ("POST", "/v1/analyse"): (30, 60),
        ("POST", "/v1/auth/login"): (10, 60),
        ("POST", "/v1/auth/register"): (5, 3600),
        ("POST", "/v1/contributions"): (5, 3600),
        ("POST", "/v1/feedback"): (30, 60),
    }

    def __init__(self, app):
        super().__init__(app)
        self._requests: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = Lock()

    async def dispatch(self, request: Request, call_next):
        limit = self.LIMITS.get((request.method, request.url.path))
        if limit is None:
            return await call_next(request)
        maximum, window = limit
        client = request.headers.get("x-guard-client-ip") or (request.client.host if request.client else "unknown")
        key = (request.url.path, client)
        now = monotonic()
        with self._lock:
            entries = self._requests[key]
            while entries and entries[0] <= now - window:
                entries.popleft()
            if len(entries) >= maximum:
                retry_after = max(1, round(window - (now - entries[0])))
                return JSONResponse(
                    {"detail": "Too many requests. Please wait and try again."},
                    status_code=429,
                    headers={"Retry-After": str(retry_after)},
                )
            entries.append(now)
        return await call_next(request)
