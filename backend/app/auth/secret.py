"""Resolve the JWT signing secret."""

from __future__ import annotations

import logging
import os
import secrets
from pathlib import Path

log = logging.getLogger("ragforge")
MIN_SECRET_BYTES = 32


def resolve_jwt_secret(configured: str, data_dir: Path) -> str:
    """Use the configured secret, or create and persist a random one.

    A persisted secret keeps users signed in across restarts without anyone having
    to invent a key, and is never weaker than 32 bytes.
    """
    if configured:
        if len(configured.encode()) < MIN_SECRET_BYTES:
            raise ValueError(f"RAGFORGE_JWT_SECRET must be at least {MIN_SECRET_BYTES} bytes")
        return configured
    path = data_dir / ".jwt_secret"
    if path.exists():
        return path.read_text().strip()
    data_dir.mkdir(parents=True, exist_ok=True)
    secret = secrets.token_urlsafe(48)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(secret)
    log.info("generated a new JWT secret at %s", path)
    return secret
