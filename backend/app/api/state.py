"""Application container built once at startup and shared by the routers."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings
from app.core.knowledge_base import KnowledgeBase
from app.db.database import Database
from app.db.repositories import DocumentRepository, QueryRepository, UserRepository
from app.embeddings.factory import build_embedder
from app.generation.answer import AnswerEngine
from app.generation.factory import build_llm
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
    engine: AnswerEngine


def build_state(settings: Settings, in_memory: bool = False) -> AppState:
    embedder = build_embedder(settings)
    if in_memory:
        db = Database(":memory:")
        store = InMemoryVectorStore(embedder.dim)
    else:
        db = Database(settings.data_dir / "ragforge.db")
        store = PersistentVectorStore(embedder.dim, settings.data_dir / "index")
    kb = KnowledgeBase(embedder, store)
    return AppState(
        settings=settings,
        db=db,
        documents=DocumentRepository(db),
        users=UserRepository(db),
        queries=QueryRepository(db),
        kb=kb,
        engine=AnswerEngine(kb, build_llm(settings)),
    )
