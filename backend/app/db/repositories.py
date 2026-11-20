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
    visibility: str = "shared"


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
                       chunk_count, title, owner_id, visibility)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(doc_id) DO UPDATE SET filename=excluded.filename,
                       collection=excluded.collection, chunk_count=excluded.chunk_count,
                       title=excluded.title, visibility=excluded.visibility""",
                (rec.doc_id, rec.filename, rec.collection, rec.doc_type, rec.size_bytes,
                 rec.chunk_count, rec.title, rec.owner_id, rec.visibility),
            )

    def get(self, doc_id: str) -> DocumentRecord | None:
        rows = self.db.query("SELECT * FROM documents WHERE doc_id = ?", (doc_id,))
        return DocumentRecord(**dict(rows[0])) if rows else None

    @staticmethod
    def _where(collection: str | None, viewer_id: int | None) -> tuple[str, list]:
        clauses, params = [], []
        if collection:
            clauses.append("collection = ?")
            params.append(collection)
        if viewer_id is not None:
            clauses.append("(visibility = 'shared' OR owner_id = ?)")
            params.append(viewer_id)
        return ("WHERE " + " AND ".join(clauses)) if clauses else "", params

    def list(self, collection: str | None = None, limit: int | None = None,
             offset: int = 0, viewer_id: int | None = None) -> list[DocumentRecord]:
        """List documents; pass viewer_id to hide other users' private documents."""
        where, params = self._where(collection, viewer_id)
        sql = f"SELECT * FROM documents {where} ORDER BY created_at DESC, filename"
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params += [limit, offset]
        return [DocumentRecord(**dict(r)) for r in self.db.query(sql, tuple(params))]

    def count(self, collection: str | None = None, viewer_id: int | None = None) -> int:
        where, params = self._where(collection, viewer_id)
        return self.db.query(f"SELECT COUNT(*) FROM documents {where}", tuple(params))[0][0]

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

    def list(self) -> list[UserRecord]:
        rows = self.db.query("SELECT id, username, password_hash, role FROM users ORDER BY id")
        return [UserRecord(**dict(r)) for r in rows]

    def set_role(self, user_id: int, role: str) -> bool:
        with self.db.tx() as conn:
            return conn.execute("UPDATE users SET role = ? WHERE id = ?",
                                (role, user_id)).rowcount > 0

    def set_password(self, user_id: int, password_hash: str) -> None:
        with self.db.tx() as conn:
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                         (password_hash, user_id))

    def delete(self, user_id: int) -> bool:
        with self.db.tx() as conn:
            return conn.execute("DELETE FROM users WHERE id = ?", (user_id,)).rowcount > 0

    def admin_count(self) -> int:
        return self.db.query("SELECT COUNT(*) FROM users WHERE role = 'admin'")[0][0]


@dataclass
class QueryRecord:
    id: int
    user_id: int | None
    question: str
    answer: str
    grounded: bool
    mode: str
    citations_json: str
    retrieval_ms: float | None
    generation_ms: float | None
    feedback: int | None
    created_at: str


class QueryRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def log(self, user_id: int, question: str, answer: str, grounded: bool, mode: str,
            citations_json: str, retrieval_ms: float, generation_ms: float) -> int:
        with self.db.tx() as conn:
            cur = conn.execute(
                """INSERT INTO queries(user_id, question, answer, grounded, mode, citations_json,
                       retrieval_ms, generation_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, question, answer, int(grounded), mode, citations_json,
                 retrieval_ms, generation_ms),
            )
        return cur.lastrowid

    def for_user(self, user_id: int, limit: int = 50) -> list[QueryRecord]:
        rows = self.db.query("SELECT * FROM queries WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                             (user_id, limit))
        return [QueryRecord(**{**dict(r), "grounded": bool(r["grounded"])}) for r in rows]

    def set_feedback(self, query_id: int, user_id: int, value: int) -> bool:
        if value not in (-1, 1):
            raise ValueError("feedback must be -1 or 1")
        with self.db.tx() as conn:
            cur = conn.execute("UPDATE queries SET feedback = ? WHERE id = ? AND user_id = ?",
                               (value, query_id, user_id))
        return cur.rowcount > 0

    def summary(self) -> dict[str, float]:
        row = self.db.query(
            """SELECT COUNT(*) AS total, AVG(grounded) AS grounded_rate,
                      AVG(retrieval_ms) AS retrieval_ms, AVG(generation_ms) AS generation_ms,
                      SUM(feedback = 1) AS up, SUM(feedback = -1) AS down FROM queries"""
        )[0]
        return {k: (row[k] or 0) for k in row.keys()}
