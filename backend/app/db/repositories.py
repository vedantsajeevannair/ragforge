"""Data-access helpers for documents and users."""

from __future__ import annotations

from dataclasses import dataclass

from app.db.database import Database


@dataclass
class DocumentRecord:
    doc_id: str
    filename: str
    collection: str
    doc_type: str | None
    size_bytes: int
    chunk_count: int
    title: str | None
    owner_id: int | None
    created_at: str


@dataclass
class UserRecord:
    id: int
    username: str
    password_hash: str
    role: str


class DocumentRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def upsert(self, rec: DocumentRecord) -> None:
        with self.db.tx() as conn:
            conn.execute(
                """INSERT INTO documents(doc_id, filename, collection, doc_type, size_bytes,
                       chunk_count, title, owner_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(doc_id) DO UPDATE SET filename=excluded.filename,
                       collection=excluded.collection, chunk_count=excluded.chunk_count,
                       title=excluded.title""",
                (rec.doc_id, rec.filename, rec.collection, rec.doc_type, rec.size_bytes,
                 rec.chunk_count, rec.title, rec.owner_id),
            )

    def get(self, doc_id: str) -> DocumentRecord | None:
        rows = self.db.query("SELECT * FROM documents WHERE doc_id = ?", (doc_id,))
        return DocumentRecord(**dict(rows[0])) if rows else None

    def list(self, collection: str | None = None) -> list[DocumentRecord]:
        if collection:
            rows = self.db.query("SELECT * FROM documents WHERE collection = ? "
                                 "ORDER BY created_at DESC, filename", (collection,))
        else:
            rows = self.db.query("SELECT * FROM documents ORDER BY created_at DESC, filename")
        return [DocumentRecord(**dict(r)) for r in rows]

    def delete(self, doc_id: str) -> bool:
        with self.db.tx() as conn:
            return conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,)).rowcount > 0

    def collections(self) -> list[tuple[str, int]]:
        rows = self.db.query("SELECT collection, COUNT(*) AS n FROM documents "
                             "GROUP BY collection ORDER BY collection")
        return [(r["collection"], r["n"]) for r in rows]


class UserRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create(self, username: str, password_hash: str, role: str = "user") -> UserRecord:
        with self.db.tx() as conn:
            cur = conn.execute(
                "INSERT INTO users(username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role),
            )
        return UserRecord(cur.lastrowid, username, password_hash, role)

    def by_username(self, username: str) -> UserRecord | None:
        rows = self.db.query("SELECT id, username, password_hash, role FROM users "
                             "WHERE username = ?", (username,))
        return UserRecord(**dict(rows[0])) if rows else None

    def by_id(self, user_id: int) -> UserRecord | None:
        rows = self.db.query("SELECT id, username, password_hash, role FROM users WHERE id = ?",
                             (user_id,))
        return UserRecord(**dict(rows[0])) if rows else None

    def count(self) -> int:
        return self.db.query("SELECT COUNT(*) FROM users")[0][0]
