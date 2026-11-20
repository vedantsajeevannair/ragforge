"""Request ID and timing middleware."""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

log = logging.getLogger("ragforge.http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        response.headers["x-request-id"] = request_id
        response.headers["server-timing"] = f"app;dur={elapsed:.1f}"
        log.info("%s %s %s %.1fms id=%s", request.method, request.url.path,
                 response.status_code, elapsed, request_id)
        return response
