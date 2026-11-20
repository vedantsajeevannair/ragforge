"""Search and question-answering endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import current_user, get_state
from app.api.schemas import AskResponse, CitationOut, HitOut, SearchRequest, SearchResponse
from app.api.state import AppState
from app.core.knowledge_base import SearchOptions
from app.db.repositories import UserRecord
from app.generation.providers import LLMError
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


@router.post("/search", response_model=SearchResponse)
def search(body: SearchRequest, _: UserRecord = Depends(current_user),
           state: AppState = Depends(get_state)) -> SearchResponse:
    hits = state.kb.search(body.query, _options(body))
    return SearchResponse(query=body.query, hits=[_hit(h) for h in hits])


@router.post("/ask", response_model=AskResponse)
def ask(body: SearchRequest, _: UserRecord = Depends(current_user),
        state: AppState = Depends(get_state)) -> AskResponse:
    try:
        ans = state.engine.answer(body.query, _options(body))
    except LLMError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
    return AskResponse(
        question=ans.question,
        answer=ans.answer,
        grounded=ans.grounded,
        citations=[CitationOut(**vars(c)) for c in ans.citations],
        hits=[_hit(h) for h in ans.hits],
        timings_ms={k: round(v, 2) for k, v in ans.timings_ms.items()},
    )
