"""Prompt construction with numbered context blocks the model can cite."""

from __future__ import annotations

from app.vectorstore.base import SearchHit

SYSTEM_PROMPT = (
    "You answer questions using only the numbered context passages provided. "
    "Cite every claim with the passage number in square brackets, like [1] or [2][3]. "
    "If the passages do not contain the answer, say you could not find it in the documents. "
    "Be concise."
)


def source_label(hit: SearchHit) -> str:
    meta = hit.chunk.metadata
    label = meta.get("source", hit.chunk.doc_id)
    if "page" in meta:
        label += f", p. {meta['page']}"
    if "section" in meta:
        label += f" ({meta['section']})"
    return label


def format_context(hits: list[SearchHit], max_chars: int = 12000) -> str:
    blocks, used = [], 0
    for i, hit in enumerate(hits, start=1):
        block = f"[{i}] Source: {source_label(hit)}\n{hit.chunk.text.strip()}"
        if used + len(block) > max_chars and blocks:
            break
        blocks.append(block)
        used += len(block)
    return "\n\n".join(blocks)


def build_user_prompt(question: str, hits: list[SearchHit], max_chars: int = 12000) -> str:
    return f"Context:\n{format_context(hits, max_chars)}\n\nQuestion: {question.strip()}"
