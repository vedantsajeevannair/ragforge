"""Check that file contents match the extension before parsing."""

from __future__ import annotations

from pathlib import Path

_MAGIC = {
    ".pdf": (b"%PDF-",),
    ".docx": (b"PK\x03\x04",),
}
_TEXT_EXTS = {".txt", ".md", ".markdown", ".html", ".htm", ".csv", ".tsv", ".json"}


class ContentMismatch(ValueError):
    pass


def looks_binary(data: bytes, sample: int = 4096) -> bool:
    chunk = data[:sample]
    if b"\x00" in chunk and not chunk.startswith((b"\xff\xfe", b"\xfe\xff")):
        return True
    return False


def check_content(data: bytes, filename: str) -> None:
    ext = Path(filename).suffix.lower()
    magic = _MAGIC.get(ext)
    if magic and not data.lstrip()[:8].startswith(magic):
        raise ContentMismatch(f"file content is not a valid {ext} file")
    if ext in _TEXT_EXTS and looks_binary(data):
        raise ContentMismatch(f"{ext} file contains binary data")
