"""Document upload, listing and deletion."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel

from app.api.deps import current_user, get_state, require_admin
from app.api.schemas import DocumentOut, HitOut
from app.api.state import AppState
from app.core.files import safe_filename
from app.db.repositories import DocumentRecord, UserRecord
from app.ingestion.loaders import UnsupportedFileType, supported_extensions
from app.ingestion.pipeline import ingest_bytes

router = APIRouter(prefix="/documents", tags=["documents"])


def _out(rec: DocumentRecord) -> DocumentOut:
    return DocumentOut(**{k: getattr(rec, k) for k in DocumentOut.model_fields})


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload(
    file: UploadFile = File(...),
    collection: str = Form("default", min_length=1, max_length=60, pattern=r"^[\w.-]+$"),
    strategy: str | None = Form(None),
    user: UserRecord = Depends(current_user),
    state: AppState = Depends(get_state),
) -> DocumentOut:
    limit = state.settings.max_upload_mb * 1024 * 1024
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            f"file exceeds {state.settings.max_upload_mb} MB")
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "file is empty")
    filename = safe_filename(file.filename or "upload.txt")
    try:
        result = ingest_bytes(data, filename, state.settings.chunk_size,
                              state.settings.chunk_overlap, strategy)
    except UnsupportedFileType as exc:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            f"{exc}. Supported: {', '.join(supported_extensions())}") from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    if not result.chunks:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "no extractable text found")
    state.kb.add(result, collection=collection)
    state.files.save(result.document.doc_id, data)
    rec = DocumentRecord(
        doc_id=result.document.doc_id, filename=filename, collection=collection,
        doc_type=result.document.metadata.get("type"), size_bytes=len(data),
        chunk_count=len(result.chunks), title=result.document.metadata.get("title"),
        owner_id=user.id, created_at="",
    )
    state.documents.upsert(rec)
    return _out(state.documents.get(rec.doc_id))


@router.get("", response_model=list[DocumentOut])
def list_documents(response: Response, collection: str | None = None,
                   limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0),
                   _: UserRecord = Depends(current_user),
                   state: AppState = Depends(get_state)) -> list[DocumentOut]:
    response.headers["X-Total-Count"] = str(state.documents.count(collection))
    return [_out(r) for r in state.documents.list(collection, limit, offset)]


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: str, _: UserRecord = Depends(current_user),
                 state: AppState = Depends(get_state)) -> DocumentOut:
    rec = state.documents.get(doc_id)
    if rec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "document not found")
    return _out(rec)


@router.get("/{doc_id}/chunks", response_model=list[HitOut])
def get_chunks(doc_id: str, _: UserRecord = Depends(current_user),
               state: AppState = Depends(get_state)) -> list[HitOut]:
    if state.documents.get(doc_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "document not found")
    chunks = [c for c in state.kb.store.all_chunks() if c.doc_id == doc_id]
    chunks.sort(key=lambda c: c.metadata.get("start", 0))
    return [HitOut(chunk_id=c.chunk_id, doc_id=c.doc_id, text=c.text, score=0.0,
                   metadata=c.metadata) for c in chunks]


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(doc_id: str, user: UserRecord = Depends(current_user),
                    state: AppState = Depends(get_state)) -> None:
    rec = state.documents.get(doc_id)
    if rec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "document not found")
    if user.role != "admin" and rec.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "only the owner or an admin can delete")
    state.kb.delete(doc_id)
    state.documents.delete(doc_id)
    state.files.delete(doc_id)


@router.get("/{doc_id}/download")
def download(doc_id: str, _: UserRecord = Depends(current_user),
             state: AppState = Depends(get_state)) -> Response:
    rec = state.documents.get(doc_id)
    data = state.files.load(doc_id) if rec else None
    if rec is None or data is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "original file not available")
    return Response(data, media_type="application/octet-stream",
                    headers={"Content-Disposition": f'attachment; filename="{rec.filename}"'})


class ReindexResult(BaseModel):
    reindexed: int
    skipped: list[str]


@router.post("/reindex", response_model=ReindexResult, tags=["admin"])
def reindex(_: UserRecord = Depends(require_admin),
            state: AppState = Depends(get_state)) -> ReindexResult:
    """Re-chunk and re-embed every stored original with the current settings."""
    done, skipped = 0, []
    for rec in state.documents.list():
        data = state.files.load(rec.doc_id)
        if data is None:
            skipped.append(rec.filename)
            continue
        result = ingest_bytes(data, rec.filename, state.settings.chunk_size,
                              state.settings.chunk_overlap)
        state.kb.add(result, collection=rec.collection)
        rec.chunk_count = len(result.chunks)
        state.documents.upsert(rec)
        done += 1
    return ReindexResult(reindexed=done, skipped=skipped)
