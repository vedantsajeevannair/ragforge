"""Consistent JSON error bodies."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

log = logging.getLogger("ragforge")


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "internal server error"})
