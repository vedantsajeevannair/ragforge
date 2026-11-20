"""Loaders that turn raw files into Document objects."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from collections.abc import Callable
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

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


_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def load_docx(data: bytes, source: str) -> Document:
    """Read paragraph text from a .docx without extra dependencies.

    Heading styles become Markdown-style '#' lines so the Markdown chunker can
    attach section paths.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            xml = zf.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise ValueError("not a valid .docx file") from exc
    root = ElementTree.fromstring(xml)
    lines = []
    for para in root.iter(f"{_W}p"):
        text = "".join(t.text or "" for t in para.iter(f"{_W}t")).strip()
        if not text:
            continue
        style = para.find(f"{_W}pPr/{_W}pStyle")
        level = 0
        if style is not None:
            name = style.get(f"{_W}val", "")
            if name.lower().startswith("heading") and name[-1:].isdigit():
                level = int(name[-1])
            elif name.lower() == "title":
                level = 1
        lines.append(f"{'#' * level} {text}" if level else text)
    return Document(text="\n\n".join(lines), source=source, metadata={"type": "markdown"})


def load_csv(data: bytes, source: str) -> Document:
    """Render each row as 'column: value' lines so rows are retrievable on their own."""
    text = _decode(data)
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    rows = []
    for i, row in enumerate(reader, start=1):
        fields = [f"{k.strip()}: {(v or '').strip()}" for k, v in row.items()
                  if k and (v or "").strip()]
        if fields:
            rows.append(f"Row {i}. " + "; ".join(fields) + ".")
    return Document(text="\n\n".join(rows), source=source,
                    metadata={"type": "csv", "rows": len(rows),
                              "columns": list(reader.fieldnames or [])})


def _flatten(value, prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        out = []
        for k, v in value.items():
            out.extend(_flatten(v, f"{prefix}.{k}" if prefix else str(k)))
        return out
    if isinstance(value, list):
        if all(not isinstance(v, dict | list) for v in value):
            return [f"{prefix}: {', '.join(map(str, value))}"] if value else []
        out = []
        for i, v in enumerate(value):
            out.extend(_flatten(v, f"{prefix}[{i}]"))
        return out
    return [f"{prefix}: {value}"] if value not in (None, "") else []


def load_json(data: bytes, source: str) -> Document:
    """Flatten JSON into 'path: value' lines; a top-level array becomes one block per item."""
    try:
        payload = json.loads(_decode(data))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc.msg} at line {exc.lineno}") from exc
    items = payload if isinstance(payload, list) else [payload]
    blocks = ["\n".join(_flatten(item)) for item in items]
    return Document(text="\n\n".join(b for b in blocks if b), source=source,
                    metadata={"type": "json"})


_LOADERS: dict[str, Loader] = {
    ".txt": load_text,
    ".md": load_markdown,
    ".markdown": load_markdown,
    ".html": load_html,
    ".htm": load_html,
    ".pdf": load_pdf,
    ".docx": load_docx,
    ".csv": load_csv,
    ".tsv": load_csv,
    ".json": load_json,
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
