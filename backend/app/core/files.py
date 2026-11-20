"""Store original uploads so documents can be downloaded and re-indexed later."""

from __future__ import annotations

import re
from pathlib import Path

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(name: str, max_length: int = 120) -> str:
    """Strip directories and unsafe characters; never return an empty or dot-only name."""
    base = Path(name.replace("\\", "/")).name
    cleaned = _UNSAFE.sub("_", base).strip("._") or "upload"
    stem, dot, ext = cleaned.rpartition(".")
    if dot and len(cleaned) > max_length:
        cleaned = stem[: max_length - len(ext) - 1] + "." + ext
    return cleaned[:max_length]


class FileStore:
    def __init__(self, root: Path | None) -> None:
        self.root = root
        if root is not None:
            root.mkdir(parents=True, exist_ok=True)

    def _path(self, doc_id: str) -> Path:
        if self.root is None:
            raise RuntimeError("file store is disabled")
        if not re.fullmatch(r"[0-9a-f]{16}", doc_id):
            raise ValueError("invalid document id")
        return self.root / doc_id

    @property
    def enabled(self) -> bool:
        return self.root is not None

    def save(self, doc_id: str, data: bytes) -> None:
        if self.enabled:
            self._path(doc_id).write_bytes(data)

    def load(self, doc_id: str) -> bytes | None:
        if not self.enabled:
            return None
        path = self._path(doc_id)
        return path.read_bytes() if path.exists() else None

    def delete(self, doc_id: str) -> None:
        if self.enabled:
            self._path(doc_id).unlink(missing_ok=True)
