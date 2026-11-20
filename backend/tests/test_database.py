import pytest

from app.db.database import MIGRATIONS, Database


def test_migrations_set_user_version(tmp_path):
    with Database(tmp_path / "x.db") as db:
        assert db.version == len(MIGRATIONS)
    with Database(tmp_path / "x.db") as again:  # re-open is a no-op
        assert again.version == len(MIGRATIONS)


def test_tx_rolls_back_on_error():
    with Database(":memory:") as db:
        with pytest.raises(RuntimeError):
            with db.tx() as conn:
                conn.execute("INSERT INTO users(username, password_hash) VALUES ('a', 'h')")
                raise RuntimeError
        assert db.query("SELECT * FROM users") == []


def test_visibility_column_defaults_to_shared():
    with Database(":memory:") as db:
        db.query("INSERT INTO documents(doc_id, filename, size_bytes, chunk_count) "
                 "VALUES ('d', 'f', 1, 1)")
        assert db.query("SELECT visibility FROM documents")[0][0] == "shared"
