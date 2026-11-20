"""FastAPI dependencies: state access and authentication."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.state import AppState
from app.auth.tokens import TokenError, decode_token
from app.db.repositories import UserRecord

_bearer = HTTPBearer(auto_error=False)


def get_state(request: Request) -> AppState:
    return request.app.state.ragforge


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    state: AppState = Depends(get_state),
) -> UserRecord:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token",
                            headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = decode_token(creds.credentials, state.settings.jwt_secret)
    except TokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc),
                            headers={"WWW-Authenticate": "Bearer"}) from exc
    user = state.users.by_id(int(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user no longer exists")
    return user


def require_admin(user: UserRecord = Depends(current_user)) -> UserRecord:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin role required")
    return user
