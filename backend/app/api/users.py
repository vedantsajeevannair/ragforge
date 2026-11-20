"""Admin user management and self-service password change."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import current_user, get_state, require_admin
from app.api.schemas import UserOut
from app.api.state import AppState
from app.auth.passwords import hash_password, verify_password
from app.db.repositories import UserRecord

router = APIRouter(tags=["users"])


class RoleUpdate(BaseModel):
    role: Literal["admin", "user"]


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


@router.get("/users", response_model=list[UserOut])
def list_users(_: UserRecord = Depends(require_admin),
               state: AppState = Depends(get_state)) -> list[UserOut]:
    return [UserOut(id=u.id, username=u.username, role=u.role) for u in state.users.list()]


def _guard_last_admin(state: AppState, target: UserRecord) -> None:
    if target.role == "admin" and state.users.admin_count() == 1:
        raise HTTPException(status.HTTP_409_CONFLICT, "cannot remove the last admin")


@router.patch("/users/{user_id}", response_model=UserOut)
def update_role(user_id: int, body: RoleUpdate, _: UserRecord = Depends(require_admin),
                state: AppState = Depends(get_state)) -> UserOut:
    target = state.users.by_id(user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    if body.role != "admin":
        _guard_last_admin(state, target)
    state.users.set_role(user_id, body.role)
    return UserOut(id=target.id, username=target.username, role=body.role)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, _: UserRecord = Depends(require_admin),
                state: AppState = Depends(get_state)) -> None:
    target = state.users.by_id(user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    _guard_last_admin(state, target)
    state.users.delete(user_id)


@router.post("/auth/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(body: PasswordChange, user: UserRecord = Depends(current_user),
                    state: AppState = Depends(get_state)) -> None:
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "current password is incorrect")
    state.users.set_password(user.id, hash_password(body.new_password))
