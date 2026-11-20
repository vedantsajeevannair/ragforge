"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app import __version__
from app.api import auth, documents, jobs, meta, metrics, query, users
from app.api.errors import install_error_handlers
from app.api.middleware import RequestContextMiddleware
from app.api.state import build_state
from app.config import Settings, get_settings
from app.logging_config import configure_logging


def create_app(settings: Settings | None = None, in_memory: bool = False) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.json_logs)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if not hasattr(app.state, "ragforge"):
            app.state.ragforge = build_state(settings, in_memory=in_memory)
        yield
        app.state.ragforge.jobs.join()
        app.state.ragforge.jobs.shutdown()
        app.state.ragforge.db.close()

    app = FastAPI(title=settings.app_name, version=__version__, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.metrics = metrics.Metrics()
    app.add_middleware(metrics.MetricsMiddleware, metrics=app.state.metrics)
    app.add_middleware(RequestContextMiddleware)
    install_error_handlers(app)
    app.include_router(auth.router)
    app.include_router(documents.router)
    app.include_router(query.router)
    app.include_router(meta.router)
    app.include_router(users.router)
    app.include_router(jobs.router)
    app.include_router(metrics.router)

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse("/docs")

    @app.get("/ready", tags=["meta"])
    def ready() -> dict[str, object]:
        """Readiness: the database answers and the index is loaded."""
        state = app.state.ragforge
        state.db.query("SELECT 1")
        return {"status": "ready", **state.kb.stats()}

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    return app


app = create_app()
