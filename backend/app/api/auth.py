"""Register and login endpoints."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import current_user, get_state
from app.api.schemas import RegisterRequest, TokenResponse, UserOut
from app.api.state import AppState
from app.auth.passwords import hash_password, verify_password
from app.auth.tokens import create_token
from app.db.repositories import UserRecord

router = APIRouter(prefix="/auth", tags=["auth"])


def _token(state: AppState, user: UserRecord) -> TokenResponse:
    token = create_token(user.id, user.role, state.settings.jwt_secret,
                         state.settings.jwt_expiry_minutes)
    return TokenResponse(access_token=token, role=user.role)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, state: AppState = Depends(get_state)) -> TokenResponse:
    # The first account becomes admin so a fresh install can be managed.
    role = "admin" if state.users.count() == 0 else "user"
    try:
        user = state.users.create(body.username, hash_password(body.password), role)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "username already taken") from exc
    return _token(state, user)


@router.post("/login", response_model=TokenResponse)
def login(body: RegisterRequest, state: AppState = Depends(get_state)) -> TokenResponse:
    user = state.users.by_username(body.username)
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid username or password")
    return _token(state, user)


@router.get("/me", response_model=UserOut)
def me(user: UserRecord = Depends(current_user)) -> UserOut:
    return UserOut(id=user.id, username=user.username, role=user.role)
