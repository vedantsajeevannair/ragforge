"""Request and response models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UserOut(BaseModel):
    id: int
    username: str
    role: str


class DocumentOut(BaseModel):
    doc_id: str
    filename: str
    collection: str
    doc_type: str | None
    size_bytes: int
    chunk_count: int
    title: str | None
    created_at: str


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    k: int = Field(default=5, ge=1, le=50)
    mode: Literal["dense", "bm25", "hybrid"] = "hybrid"
    collection: str | None = None
    use_mmr: bool = False
    use_rerank: bool = True
    previous_questions: list[str] = Field(default_factory=list, max_length=10)


class HitOut(BaseModel):
    chunk_id: str
    doc_id: str
    text: str
    score: float
    metadata: dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    hits: list[HitOut]


class CitationOut(BaseModel):
    number: int
    chunk_id: str
    doc_id: str
    source: str
    snippet: str


class AskResponse(BaseModel):
    query_id: int
    question: str
    answer: str
    grounded: bool
    citations: list[CitationOut]
    hits: list[HitOut]
    timings_ms: dict[str, float]


class HistoryItem(BaseModel):
    id: int
    question: str
    answer: str
    grounded: bool
    mode: str
    citations: list[CitationOut]
    feedback: int | None
    created_at: str


class FeedbackRequest(BaseModel):
    value: Literal[-1, 1]
