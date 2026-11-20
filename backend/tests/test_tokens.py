import pytest

from app.auth.tokens import TokenError, create_token, decode_token


def test_round_trip():
    payload = decode_token(create_token(7, "admin", "k" * 32, 5), "k" * 32)
    assert payload["sub"] == "7" and payload["role"] == "admin"


def test_wrong_secret_rejected():
    with pytest.raises(TokenError, match="invalid"):
        decode_token(create_token(1, "user", "a" * 32, 5), "b" * 32)


def test_expired_rejected():
    with pytest.raises(TokenError, match="expired"):
        decode_token(create_token(1, "user", "a" * 32, -1), "a" * 32)
