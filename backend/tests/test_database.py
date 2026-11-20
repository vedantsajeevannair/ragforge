import pytest

from app.db.database import MIGRATIONS, Database


def test_migrations_set_user_version(tmp_path):
    db = Database(tmp_path / "x.db")
    assert db.version == len(MIGRATIONS)
    Database(tmp_path / "x.db")  # re-open is a no-op
    assert db.version == len(MIGRATIONS)


def test_tx_rolls_back_on_error():
    db = Database(":memory:")
    with pytest.raises(RuntimeError):
        with db.tx() as conn:
            conn.execute("INSERT INTO users(username, password_hash) VALUES ('a', 'h')")
            raise RuntimeError
    assert db.query("SELECT * FROM users") == []
