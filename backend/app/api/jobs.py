"""Background job status."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import current_user, get_state
from app.api.state import AppState
from app.db.repositories import UserRecord

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobOut(BaseModel):
    id: int
    kind: str
    status: str
    result: Any = None
    error: str | None = None


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, user: UserRecord = Depends(current_user),
            state: AppState = Depends(get_state)) -> JobOut:
    job = state.jobs.get(job_id)
    if job is None or (user.role != "admin" and job.owner_id != user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "job not found")
    error = job.error
    if error and error[:3].isdigit() and error[3:5] == ": ":
        error = error[5:]  # "415: Unsupported..." from HTTPException -> plain message
    return JobOut(id=job.id, kind=job.kind, status=job.status, result=job.result, error=error)
