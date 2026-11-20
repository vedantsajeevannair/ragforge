"""Command-line tools: index a folder and ask questions without the web UI.

    python -m app.cli index ../samples/corpus --collection docs
    python -m app.cli ask "How does reciprocal rank fusion work?"
"""

from __future__ import annotations

import argparse
from pathlib import Path

from app.api.state import build_state
from app.config import get_settings
from app.core.knowledge_base import SearchOptions
from app.db.repositories import DocumentRecord
from app.ingestion.loaders import supported_extensions
from app.ingestion.pipeline import ingest_bytes


def cmd_index(args, state) -> int:
    exts = set(supported_extensions())
    files = [p for p in sorted(Path(args.path).rglob("*")) if p.suffix.lower() in exts]
    for path in files:
        data = path.read_bytes()
        result = ingest_bytes(data, path.name, state.settings.chunk_size,
                              state.settings.chunk_overlap)
        state.kb.add(result, collection=args.collection)
        state.documents.upsert(DocumentRecord(
            result.document.doc_id, path.name, args.collection,
            result.document.metadata.get("type"), len(data), len(result.chunks),
            result.document.metadata.get("title"), None, ""))
        print(f"indexed {path.name}: {len(result.chunks)} chunks")
    print(f"done: {len(files)} files, {state.kb.stats()['chunks']} chunks total")
    return 0


def cmd_ask(args, state) -> int:
    ans = state.engine.answer(args.question, SearchOptions(k=args.k, mode=args.mode))
    print(ans.answer)
    for c in ans.citations:
        print(f"  [{c.number}] {c.source}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ragforge")
    sub = parser.add_subparsers(dest="command", required=True)
    p_index = sub.add_parser("index", help="index every supported file under a folder")
    p_index.add_argument("path")
    p_index.add_argument("--collection", default="default")
    p_ask = sub.add_parser("ask", help="ask a question against the index")
    p_ask.add_argument("question")
    p_ask.add_argument("--k", type=int, default=5)
    p_ask.add_argument("--mode", choices=["dense", "bm25", "hybrid"], default="hybrid")
    args = parser.parse_args(argv)
    state = build_state(get_settings())
    try:
        return {"index": cmd_index, "ask": cmd_ask}[args.command](args, state)
    finally:
        state.jobs.shutdown()
        state.db.close()


if __name__ == "__main__":
    raise SystemExit(main())
