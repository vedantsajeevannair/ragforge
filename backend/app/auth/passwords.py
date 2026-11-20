"""scrypt password hashing (stdlib, no extra dependency)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os

_N, _R, _P, _DKLEN = 2**14, 8, 1, 32


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=_DKLEN)
    salt_b64 = base64.b64encode(salt).decode()
    dk_b64 = base64.b64encode(dk).decode()
    return f"scrypt${_N}${_R}${_P}${salt_b64}${dk_b64}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algo, n, r, p, salt_b64, dk_b64 = encoded.split("$")
    except ValueError:
        return False
    if algo != "scrypt":
        return False
    expected = base64.b64decode(dk_b64)
    dk = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt_b64), n=int(n), r=int(r),
                        p=int(p), dklen=len(expected))
    return hmac.compare_digest(dk, expected)
