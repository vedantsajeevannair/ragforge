from app.generation.prompt import build_user_prompt, format_context, source_label
from app.vectorstore.base import SearchHit, StoredChunk


def _hit(text, **meta):
    return SearchHit(StoredChunk("c", "d", text, meta), 1.0)


def test_source_label_includes_page_and_section():
    assert source_label(_hit("x", source="a.pdf", page=3)) == "a.pdf, p. 3"
    assert source_label(_hit("x", source="g.md", section="Install")) == "g.md (Install)"


def test_format_context_numbers_passages():
    ctx = format_context([_hit("first", source="a"), _hit("second", source="b")])
    assert ctx.startswith("[1] Source: a\nfirst")
    assert "[2] Source: b\nsecond" in ctx


def test_format_context_truncates_but_keeps_first():
    ctx = format_context([_hit("x" * 50, source="a"), _hit("y" * 50, source="b")], max_chars=60)
    assert "[1]" in ctx and "[2]" not in ctx


def test_build_user_prompt():
    prompt = build_user_prompt(" What? ", [_hit("ctx", source="a")])
    assert prompt.endswith("Question: What?")
