"""Prometheus-style metrics in the text exposition format, without extra dependencies."""

from __future__ import annotations

import threading
import time
from collections import defaultdict

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.api.deps import get_state
from app.api.state import AppState

BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.requests: dict[tuple[str, str, int], int] = defaultdict(int)
        self.latency_buckets: dict[str, list[int]] = defaultdict(lambda: [0] * len(BUCKETS))
        self.latency_sum: dict[str, float] = defaultdict(float)
        self.latency_count: dict[str, int] = defaultdict(int)

    def observe(self, method: str, route: str, status: int, seconds: float) -> None:
        with self._lock:
            self.requests[(method, route, status)] += 1
            for i, bound in enumerate(BUCKETS):
                if seconds <= bound:
                    self.latency_buckets[route][i] += 1
            self.latency_sum[route] += seconds
            self.latency_count[route] += 1

    def render(self, gauges: dict[str, float]) -> str:
        lines = ["# TYPE ragforge_http_requests_total counter"]
        with self._lock:
            for (method, route, status), n in sorted(self.requests.items()):
                lines.append(f'ragforge_http_requests_total{{method="{method}",'
                             f'route="{route}",status="{status}"}} {n}')
            lines.append("# TYPE ragforge_http_request_seconds histogram")
            for route in sorted(self.latency_count):
                for bound, n in zip(BUCKETS, self.latency_buckets[route], strict=True):
                    lines.append(f'ragforge_http_request_seconds_bucket{{route="{route}",'
                                 f'le="{bound}"}} {n}')
                count = self.latency_count[route]
                lines.append(f'ragforge_http_request_seconds_bucket{{route="{route}",'
                             f'le="+Inf"}} {count}')
                lines.append(f'ragforge_http_request_seconds_sum{{route="{route}"}} '
                             f'{self.latency_sum[route]:.6f}')
                lines.append(f'ragforge_http_request_seconds_count{{route="{route}"}} {count}')
        for name, value in gauges.items():
            lines += [f"# TYPE ragforge_{name} gauge", f"ragforge_{name} {value}"]
        return "\n".join(lines) + "\n"


class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, metrics: Metrics) -> None:
        super().__init__(app)
        self.metrics = metrics

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        # Use the route template (/documents/{doc_id}) so ids do not explode cardinality.
        path = getattr(route, "path", "unmatched")
        self.metrics.observe(request.method, path, response.status_code,
                             time.perf_counter() - start)
        return response


router = APIRouter(tags=["meta"])


@router.get("/metrics", response_class=PlainTextResponse)
def metrics(request: Request, state: AppState = Depends(get_state)) -> str:
    kb = state.kb.stats()
    return request.app.state.metrics.render({
        "documents": kb["documents"], "chunks": kb["chunks"], "users": state.users.count(),
    })
