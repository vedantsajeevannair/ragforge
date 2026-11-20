"""Evaluation datasets: questions with the sources (and optional phrases) that answer them."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EvalExample:
    question: str
    relevant_sources: list[str]
    expected_phrases: list[str] = field(default_factory=list)


def load_dataset(path: str | Path) -> list[EvalExample]:
    """Read JSONL: one {"question", "relevant_sources", "expected_phrases"?} per line."""
    examples = []
    for n, line in enumerate(Path(path).read_text().splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if "question" not in row or not row.get("relevant_sources"):
            raise ValueError(f"line {n}: needs 'question' and non-empty 'relevant_sources'")
        examples.append(EvalExample(row["question"], list(row["relevant_sources"]),
                                    list(row.get("expected_phrases", []))))
    return examples
