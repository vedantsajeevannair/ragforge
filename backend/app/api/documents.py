"""Document upload, listing and deletion."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import current_user, get_state
from app.api.schemas import DocumentOut, HitOut
from app.api.state import AppState
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
    filename = file.filename or "upload.txt"
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
    rec = DocumentRecord(
        doc_id=result.document.doc_id, filename=filename, collection=collection,
        doc_type=result.document.metadata.get("type"), size_bytes=len(data),
        chunk_count=len(result.chunks), title=result.document.metadata.get("title"),
        owner_id=user.id, created_at="",
    )
    state.documents.upsert(rec)
    return _out(state.documents.get(rec.doc_id))


@router.get("", response_model=list[DocumentOut])
def list_documents(collection: str | None = None, _: UserRecord = Depends(current_user),
                   state: AppState = Depends(get_state)) -> list[DocumentOut]:
    return [_out(r) for r in state.documents.list(collection)]


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
