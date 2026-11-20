from app.auth.passwords import hash_password, verify_password


def test_hash_and_verify():
    h = hash_password("s3cret!")
    assert h.startswith("scrypt$")
    assert verify_password("s3cret!", h)
    assert not verify_password("wrong", h)


def test_hashes_are_salted():
    assert hash_password("same") != hash_password("same")


def test_verify_rejects_malformed():
    assert not verify_password("x", "not-a-hash")
    assert not verify_password("x", "bcrypt$1$2$3$4$5")
