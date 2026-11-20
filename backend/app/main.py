"""FastAPI application entry point."""

from fastapi import FastAPI

from app import __version__
from app.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version=__version__)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
