"""Thin sqlite3 wrapper with schema migrations."""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

MIGRATIONS: list[str] = [
    """
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE documents (
        doc_id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        collection TEXT NOT NULL DEFAULT 'default',
        doc_type TEXT,
        size_bytes INTEGER NOT NULL,
        chunk_count INTEGER NOT NULL,
        title TEXT,
        owner_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX idx_documents_collection ON documents(collection);
    """,
    """
    CREATE TABLE queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        grounded INTEGER NOT NULL,
        mode TEXT NOT NULL,
        citations_json TEXT NOT NULL DEFAULT '[]',
        retrieval_ms REAL,
        generation_ms REAL,
        feedback INTEGER,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX idx_queries_user ON queries(user_id, created_at);
    """,
]


class Database:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._lock = threading.Lock()
        self.migrate()

    @property
    def version(self) -> int:
        return self._conn.execute("PRAGMA user_version").fetchone()[0]

    def migrate(self) -> None:
        for i in range(self.version, len(MIGRATIONS)):
            with self._lock:
                self._conn.executescript(MIGRATIONS[i])
                self._conn.execute(f"PRAGMA user_version = {i + 1}")
                self._conn.commit()

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            try:
                yield self._conn
                self._conn.commit()
            except BaseException:
                self._conn.rollback()
                raise

    def query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    def close(self) -> None:
        self._conn.close()
