"""Application container built once at startup and shared by the routers."""

from __future__ import annotations

from dataclasses import dataclass

from app.auth.secret import resolve_jwt_secret
from app.config import Settings
from app.core.files import FileStore
from app.core.jobs import JobQueue
from app.core.knowledge_base import KnowledgeBase
from app.db.database import Database
from app.db.repositories import DocumentRepository, QueryRepository, UserRepository
from app.embeddings.factory import build_embedder
from app.generation.answer import AnswerEngine
from app.generation.factory import build_llm
from app.retrieval.query import load_synonyms
from app.vectorstore.memory import InMemoryVectorStore
from app.vectorstore.persistent import PersistentVectorStore


@dataclass
class AppState:
    settings: Settings
    db: Database
    documents: DocumentRepository
    users: UserRepository
    queries: QueryRepository
    kb: KnowledgeBase
    files: FileStore
    jobs: JobQueue
    engine: AnswerEngine


def build_state(settings: Settings, in_memory: bool = False) -> AppState:
    if not in_memory or not settings.jwt_secret:
        settings = settings.model_copy(update={
            "jwt_secret": resolve_jwt_secret(settings.jwt_secret, settings.data_dir)})
    embedder = build_embedder(settings)
    if in_memory:
        db = Database(":memory:")
        store = InMemoryVectorStore(embedder.dim)
        files = FileStore(None)
    else:
        db = Database(settings.data_dir / "ragforge.db")
        store = PersistentVectorStore(embedder.dim, settings.data_dir / "index")
        files = FileStore(settings.data_dir / "files")
    kb = KnowledgeBase(embedder, store, settings.contextual_headers,
                       settings.effective_dense_weight, load_synonyms(settings.synonyms_file))
    return AppState(
        settings=settings,
        db=db,
        documents=DocumentRepository(db),
        users=UserRepository(db),
        queries=QueryRepository(db),
        kb=kb,
        files=files,
        jobs=JobQueue(),
        engine=AnswerEngine(kb, build_llm(settings), settings.min_score,
                            settings.max_context_chars, settings.system_prompt),
    )
