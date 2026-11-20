"""JWT access tokens."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt

ALGORITHM = "HS256"


class TokenError(ValueError):
    pass


def create_token(user_id: int, role: str, secret: str, expiry_minutes: int) -> str:
    now = datetime.now(UTC)
    payload = {"sub": str(user_id), "role": role, "iat": now,
               "exp": now + timedelta(minutes=expiry_minutes)}
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_token(token: str, secret: str) -> dict:
    try:
        return jwt.decode(token, secret, algorithms=[ALGORITHM], options={"require": ["exp", "sub"]})
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("invalid token") from exc
