"""Loaders that turn raw files into Document objects."""

from __future__ import annotations

import io
from collections.abc import Callable
from html.parser import HTMLParser
from pathlib import Path

from app.ingestion.models import Document

Loader = Callable[[bytes, str], Document]


class UnsupportedFileType(ValueError):
    pass


def _decode(data: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def load_text(data: bytes, source: str) -> Document:
    return Document(text=_decode(data), source=source, metadata={"type": "text"})


def load_markdown(data: bytes, source: str) -> Document:
    return Document(text=_decode(data), source=source, metadata={"type": "markdown"})


_LOADERS: dict[str, Loader] = {
    ".txt": load_text,
    ".md": load_markdown,
    ".markdown": load_markdown,
}


def register_loader(extension: str, loader: Loader) -> None:
    _LOADERS[extension.lower()] = loader


def supported_extensions() -> list[str]:
    return sorted(_LOADERS)


def load_bytes(data: bytes, filename: str) -> Document:
    ext = Path(filename).suffix.lower()
    loader = _LOADERS.get(ext)
    if loader is None:
        raise UnsupportedFileType(f"Unsupported file type: {ext or '(none)'}")
    return loader(data, filename)


def load_path(path: str | Path) -> Document:
    path = Path(path)
    return load_bytes(path.read_bytes(), path.name)
