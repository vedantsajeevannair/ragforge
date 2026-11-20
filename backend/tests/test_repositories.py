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
