import sqlite3

import pytest

from app.db.database import Database
from app.db.repositories import DocumentRecord, DocumentRepository, UserRepository


@pytest.fixture
def db():
    return Database(":memory:")


def _rec(doc_id="d1", collection="default", chunks=3):
    return DocumentRecord(doc_id, f"{doc_id}.md", collection, "markdown", 100, chunks, None,
                          None, "")


def test_document_upsert_get_list_delete(db):
    repo = DocumentRepository(db)
    repo.upsert(_rec())
    repo.upsert(_rec(chunks=5))
    repo.upsert(_rec("d2", collection="hr"))
    assert repo.get("d1").chunk_count == 5
    assert len(repo.list()) == 2
    assert [d.doc_id for d in repo.list("hr")] == ["d2"]
    assert repo.collections() == [("default", 1), ("hr", 1)]
    assert repo.delete("d1") and not repo.delete("d1")
    assert repo.get("d1") is None


def test_user_create_and_lookup(db):
    users = UserRepository(db)
    u = users.create("alice", "hash", role="admin")
    assert users.by_username("alice").id == u.id
    assert users.by_id(u.id).role == "admin"
    assert users.count() == 1
    with pytest.raises(sqlite3.IntegrityError):
        users.create("alice", "x")


from app.db.repositories import QueryRepository  # noqa: E402


def test_query_log_history_feedback_summary(db):
    uid = UserRepository(db).create("u", "h").id
    other = UserRepository(db).create("v", "h").id
    q = QueryRepository(db)
    first = q.log(uid, "q1", "a1", True, "hybrid", "[]", 10.0, 20.0)
    q.log(uid, "q2", "a2", False, "bm25", "[]", 30.0, 0.0)
    assert [r.question for r in q.for_user(uid)] == ["q2", "q1"]
    assert q.for_user(uid)[1].grounded is True
    assert q.set_feedback(first, uid, 1)
    assert not q.set_feedback(first, other, -1)
    with pytest.raises(ValueError):
        q.set_feedback(first, uid, 5)
    s = q.summary()
    assert s["total"] == 2 and s["grounded_rate"] == 0.5 and s["up"] == 1
