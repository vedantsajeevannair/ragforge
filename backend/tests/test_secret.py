import stat

import pytest

from app.auth.secret import resolve_jwt_secret


def test_configured_secret_is_used(tmp_path):
    assert resolve_jwt_secret("k" * 32, tmp_path) == "k" * 32


def test_short_secret_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="32 bytes"):
        resolve_jwt_secret("short", tmp_path)


def test_generated_secret_is_persisted_privately(tmp_path):
    first = resolve_jwt_secret("", tmp_path)
    assert len(first) >= 32
    assert resolve_jwt_secret("", tmp_path) == first
    mode = stat.S_IMODE((tmp_path / ".jwt_secret").stat().st_mode)
    assert mode == 0o600
