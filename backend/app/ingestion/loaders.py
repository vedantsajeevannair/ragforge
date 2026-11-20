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


class _HTMLTextExtractor(HTMLParser):
    _SKIP = {"script", "style", "noscript", "head"}
    _BLOCK = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "section"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.title = ""
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag in self._BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False
        if tag in self._BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title += data.strip()
        elif not self._skip_depth:
            self.parts.append(data)


def load_html(data: bytes, source: str) -> Document:
    parser = _HTMLTextExtractor()
    parser.feed(_decode(data))
    metadata = {"type": "html"}
    if parser.title:
        metadata["title"] = parser.title
    return Document(text="".join(parser.parts), source=source, metadata=metadata)


def load_pdf(data: bytes, source: str) -> Document:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(pages)
    offsets, pos = [], 0
    for page in pages:
        offsets.append(pos)
        pos += len(page) + 2
    metadata = {"type": "pdf", "pages": len(pages), "page_offsets": offsets}
    info = reader.metadata
    if info and info.title:
        metadata["title"] = str(info.title)
    return Document(text=text, source=source, metadata=metadata)


_LOADERS: dict[str, Loader] = {
    ".txt": load_text,
    ".md": load_markdown,
    ".markdown": load_markdown,
    ".html": load_html,
    ".htm": load_html,
    ".pdf": load_pdf,
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
