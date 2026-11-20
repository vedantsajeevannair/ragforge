"""Collections, stats and configuration endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app import __version__
from app.api.deps import current_user, get_state, require_admin
from app.api.state import AppState
from app.db.repositories import UserRecord
from app.ingestion.chunking import CHUNKERS
from app.ingestion.loaders import supported_extensions

router = APIRouter(tags=["meta"])


class CollectionOut(BaseModel):
    name: str
    documents: int


class StatsOut(BaseModel):
    documents: int
    chunks: int
    collections: int
    users: int
    queries: int
    grounded_rate: float
    avg_retrieval_ms: float
    avg_generation_ms: float
    thumbs_up: int
    thumbs_down: int


class ConfigOut(BaseModel):
    version: str
    llm_provider: str
    embedding_provider: str
    embedding_dim: int
    chunk_size: int
    chunk_overlap: int
    supported_extensions: list[str]
    chunkers: list[str]


@router.get("/collections", response_model=list[CollectionOut])
def collections(_: UserRecord = Depends(current_user),
                state: AppState = Depends(get_state)) -> list[CollectionOut]:
    return [CollectionOut(name=n, documents=c) for n, c in state.documents.collections()]


@router.get("/stats", response_model=StatsOut)
def stats(_: UserRecord = Depends(require_admin),
          state: AppState = Depends(get_state)) -> StatsOut:
    kb = state.kb.stats()
    q = state.queries.summary()
    return StatsOut(documents=kb["documents"], chunks=kb["chunks"],
                    collections=len(state.documents.collections()),
                    users=state.users.count(), queries=int(q["total"]),
                    grounded_rate=round(float(q["grounded_rate"]), 3),
                    avg_retrieval_ms=round(float(q["retrieval_ms"]), 2),
                    avg_generation_ms=round(float(q["generation_ms"]), 2),
                    thumbs_up=int(q["up"]), thumbs_down=int(q["down"]))


@router.get("/config", response_model=ConfigOut)
def config(_: UserRecord = Depends(current_user),
           state: AppState = Depends(get_state)) -> ConfigOut:
    s = state.settings
    return ConfigOut(version=__version__, llm_provider=s.llm_provider,
                     embedding_provider=s.embedding_provider, embedding_dim=s.embedding_dim,
                     chunk_size=s.chunk_size, chunk_overlap=s.chunk_overlap,
                     supported_extensions=supported_extensions(), chunkers=sorted(CHUNKERS))
