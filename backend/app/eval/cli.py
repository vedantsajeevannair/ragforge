"""Compare retrieval configurations on a labelled dataset.

Usage:
    python -m app.eval.cli --corpus ../samples/corpus --dataset ../samples/eval.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.core.knowledge_base import KnowledgeBase, SearchOptions
from app.embeddings.hashing import HashingEmbedder
from app.eval.dataset import load_dataset
from app.eval.runner import evaluate_answers, evaluate_retrieval
from app.generation.answer import AnswerEngine
from app.generation.extractive import ExtractiveProvider
from app.ingestion.loaders import supported_extensions
from app.ingestion.pipeline import ingest_bytes
from app.vectorstore.memory import InMemoryVectorStore

CONFIGS = [
    SearchOptions(mode="bm25", use_rerank=False, expand=False),
    SearchOptions(mode="dense", use_rerank=False, expand=False),
    SearchOptions(mode="hybrid", use_rerank=False, expand=False),
    SearchOptions(mode="hybrid", use_rerank=True, expand=True),
    SearchOptions(mode="hybrid", use_rerank=True, expand=True, use_mmr=True),
]


def build_kb(corpus: Path, dim: int, chunk_size: int, overlap: int) -> KnowledgeBase:
    kb = KnowledgeBase(HashingEmbedder(dim), InMemoryVectorStore(dim))
    exts = set(supported_extensions())
    for path in sorted(corpus.rglob("*")):
        if path.is_file() and path.suffix.lower() in exts:
            kb.add(ingest_bytes(path.read_bytes(), path.name, chunk_size, overlap))
    return kb


def label(opts: SearchOptions) -> str:
    extras = [x for x, on in (("rerank", opts.use_rerank), ("expand", opts.expand),
                              ("mmr", opts.use_mmr)) if on]
    return opts.mode + (f"+{'+'.join(extras)}" if extras else "")


def format_table(rows: list[tuple[str, dict[str, float]]], keys: list[str]) -> str:
    header = "| config | " + " | ".join(keys) + " |"
    sep = "|---|" + "---:|" * len(keys)
    lines = [header, sep]
    for name, metrics in rows:
        lines.append(f"| {name} | " + " | ".join(f"{metrics[k]:.3f}" for k in keys) + " |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--dim", type=int, default=512)
    parser.add_argument("--chunk-size", type=int, default=400)
    parser.add_argument("--overlap", type=int, default=60)
    parser.add_argument("--json", type=Path, help="also write the full report as JSON")
    parser.add_argument("--failures", action="store_true",
                        help="list questions the best config did not rank first")
    args = parser.parse_args(argv)

    kb = build_kb(args.corpus, args.dim, args.chunk_size, args.overlap)
    examples = load_dataset(args.dataset)
    rows, full = [], []
    for base in CONFIGS:
        opts = SearchOptions(**{**vars(base), "k": args.k})
        report = evaluate_retrieval(kb, examples, opts)
        rows.append((label(opts), report.metrics))
        full.append(vars(report))
    print(f"{kb.stats()['documents']} documents, {kb.stats()['chunks']} chunks, "
          f"{len(examples)} questions, k={args.k}\n")
    print(format_table(rows, ["hit@1", "hit@k", "mrr", "ndcg@k", "recall@k", "p50_ms"]))
    if args.failures:
        print("\nQuestions where hybrid+rerank+expand missed rank 1:")
        for row in full[3]["per_question"]:
            if row["hit@1"] < 1:
                got = ", ".join(row["ranked_sources"][:3]) or "(nothing)"
                print(f"- {row['question']}\n    got: {got}")
    best = SearchOptions(mode="hybrid", k=args.k)
    answers = evaluate_answers(AnswerEngine(kb, ExtractiveProvider()), examples, best)
    print("\nExtractive answers (hybrid+rerank+expand):")
    print(format_table([("extractive", answers)], list(answers)))
    if args.json:
        args.json.write_text(json.dumps({"retrieval": full, "answers": answers}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
