"""Search and question-answering endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.api.deps import current_user, get_state
from app.api.ratelimit import TokenBucket
from app.api.schemas import (
    AskResponse,
    CitationOut,
    FeedbackRequest,
    HistoryItem,
    HitOut,
    SearchRequest,
    SearchResponse,
)
from app.api.state import AppState
from app.core.knowledge_base import SearchOptions
from app.db.repositories import UserRecord
from app.generation.providers import LLMError
from app.retrieval.followup import condense_question
from app.vectorstore.base import SearchHit

router = APIRouter(tags=["query"])


def _options(body: SearchRequest) -> SearchOptions:
    return SearchOptions(
        k=body.k, mode=body.mode, use_mmr=body.use_mmr, use_rerank=body.use_rerank,
        flt={"collection": body.collection} if body.collection else None,
    )


def _hit(h: SearchHit) -> HitOut:
    return HitOut(chunk_id=h.chunk.chunk_id, doc_id=h.chunk.doc_id, text=h.chunk.text,
                  score=round(h.score, 6), metadata=h.chunk.metadata)


def _standalone(body: SearchRequest) -> str:
    return condense_question(body.query, body.previous_questions)


@router.post("/search", response_model=SearchResponse)
def search(body: SearchRequest, _: UserRecord = Depends(current_user),
           state: AppState = Depends(get_state)) -> SearchResponse:
    hits = state.kb.search(_standalone(body), _options(body))
    return SearchResponse(query=body.query, hits=[_hit(h) for h in hits])


def _ask_limit(request: Request, user: UserRecord = Depends(current_user),
               state: AppState = Depends(get_state)) -> UserRecord:
    bucket = getattr(request.app.state, "ask_bucket", None)
    if bucket is None:
        bucket = request.app.state.ask_bucket = TokenBucket(state.settings.ask_rate_per_minute)
    if not bucket.allow(str(user.id)):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "rate limit exceeded",
                            headers={"Retry-After": "5"})
    return user


@router.post("/ask", response_model=AskResponse)
def ask(body: SearchRequest, user: UserRecord = Depends(_ask_limit),
        state: AppState = Depends(get_state)) -> AskResponse:
    try:
        ans = state.engine.answer(_standalone(body), _options(body))
    except LLMError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
    citations = [CitationOut(**vars(c)) for c in ans.citations]
    query_id = state.queries.log(
        user.id, ans.question, ans.answer, ans.grounded, body.mode,
        json.dumps([c.model_dump() for c in citations]),
        ans.timings_ms.get("retrieval", 0.0), ans.timings_ms.get("generation", 0.0),
    )
    return AskResponse(
        query_id=query_id,
        question=ans.question,
        answer=ans.answer,
        grounded=ans.grounded,
        citations=citations,
        hits=[_hit(h) for h in ans.hits],
        timings_ms={k: round(v, 2) for k, v in ans.timings_ms.items()},
    )


@router.get("/history", response_model=list[HistoryItem])
def history(limit: int = 50, user: UserRecord = Depends(current_user),
            state: AppState = Depends(get_state)) -> list[HistoryItem]:
    limit = max(1, min(limit, 200))
    return [
        HistoryItem(id=r.id, question=r.question, answer=r.answer, grounded=r.grounded,
                    mode=r.mode, citations=json.loads(r.citations_json), feedback=r.feedback,
                    created_at=r.created_at)
        for r in state.queries.for_user(user.id, limit)
    ]


@router.post("/history/{query_id}/feedback", status_code=status.HTTP_204_NO_CONTENT)
def feedback(query_id: int, body: FeedbackRequest, user: UserRecord = Depends(current_user),
             state: AppState = Depends(get_state)) -> None:
    if not state.queries.set_feedback(query_id, user.id, body.value):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "query not found")


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/ask/stream")
def ask_stream(body: SearchRequest, user: UserRecord = Depends(_ask_limit),
               state: AppState = Depends(get_state)) -> StreamingResponse:
    """Server-sent events: `sources`, then `token`s, then `done` (or `error`)."""

    def events():
        try:
            for ev in state.engine.stream(_standalone(body), _options(body)):
                if ev["type"] == "sources":
                    yield _sse("sources", {"hits": [_hit(h).model_dump() for h in ev["hits"]]})
                elif ev["type"] == "token":
                    yield _sse("token", {"text": ev["text"]})
                else:
                    citations = [CitationOut(**vars(c)) for c in ev["citations"]]
                    timings = {k: round(v, 2) for k, v in ev["timings_ms"].items()}
                    qid = state.queries.log(
                        user.id, body.query, ev["answer"], ev["grounded"], body.mode,
                        json.dumps([c.model_dump() for c in citations]),
                        timings["retrieval"], timings["generation"],
                    )
                    yield _sse("done", {"query_id": qid, "answer": ev["answer"],
                                        "grounded": ev["grounded"], "timings_ms": timings,
                                        "citations": [c.model_dump() for c in citations]})
        except LLMError as exc:
            yield _sse("error", {"detail": str(exc)})

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
