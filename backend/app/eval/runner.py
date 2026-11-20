"""Run an evaluation dataset against a KnowledgeBase and aggregate metrics."""

from __future__ import annotations

import statistics
import time
from dataclasses import dataclass, field

from app.core.knowledge_base import KnowledgeBase, SearchOptions
from app.eval.dataset import EvalExample
from app.eval.metrics import hit_rate_at_k, ndcg_at_k, recall_at_k, reciprocal_rank
from app.generation.answer import AnswerEngine


def _dedupe(seq: list[str]) -> list[str]:
    return list(dict.fromkeys(seq))


@dataclass
class EvalReport:
    config: dict
    n: int
    metrics: dict[str, float]
    per_question: list[dict] = field(default_factory=list)


def evaluate_retrieval(kb: KnowledgeBase, examples: list[EvalExample],
                       options: SearchOptions) -> EvalReport:
    rows, latencies = [], []
    for ex in examples:
        t0 = time.perf_counter()
        hits = kb.search(ex.question, options)
        latencies.append((time.perf_counter() - t0) * 1000)
        ranked = _dedupe([h.chunk.metadata.get("source", "") for h in hits])
        rel = set(ex.relevant_sources)
        k = options.k
        rows.append({
            "question": ex.question,
            "ranked_sources": ranked,
            "recall@k": recall_at_k(ranked, rel, k),
            "hit@1": hit_rate_at_k(ranked, rel, 1),
            "hit@k": hit_rate_at_k(ranked, rel, k),
            "mrr": reciprocal_rank(ranked, rel),
            "ndcg@k": ndcg_at_k(ranked, rel, k),
        })
    metrics = {key: statistics.fmean(r[key] for r in rows) if rows else 0.0
               for key in ("recall@k", "hit@1", "hit@k", "mrr", "ndcg@k")}
    metrics["p50_ms"] = statistics.median(latencies) if latencies else 0.0
    config = {"mode": options.mode, "k": options.k, "rerank": options.use_rerank,
              "mmr": options.use_mmr, "expand": options.expand}
    return EvalReport(config, len(rows), metrics, rows)


def evaluate_answers(engine: AnswerEngine, examples: list[EvalExample],
                     options: SearchOptions) -> dict[str, float]:
    """Grounding rate, citation precision and phrase recall for generated answers."""
    grounded, cite_prec, phrase_recall = [], [], []
    for ex in examples:
        ans = engine.answer(ex.question, options)
        grounded.append(1.0 if ans.grounded else 0.0)
        if ans.citations:
            ok = [c for c in ans.citations
                  if any(c.source.startswith(s) for s in ex.relevant_sources)]
            cite_prec.append(len(ok) / len(ans.citations))
        if ex.expected_phrases:
            lowered = ans.answer.lower()
            found = [p for p in ex.expected_phrases if p.lower() in lowered]
            phrase_recall.append(len(found) / len(ex.expected_phrases))
    mean = lambda xs: statistics.fmean(xs) if xs else 0.0  # noqa: E731
    return {"grounded_rate": mean(grounded), "citation_precision": mean(cite_prec),
            "phrase_recall": mean(phrase_recall)}
