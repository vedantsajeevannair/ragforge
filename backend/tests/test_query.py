from app.retrieval.query import expand_query, normalize_query


def test_normalize_strips_filler_and_punctuation():
    assert normalize_query("  Can you  explain how RAG works?? ") == "how RAG works"


def test_expand_adds_synonyms():
    assert expand_query("what is RAG") == "what is RAG retrieval augmented generation"
    assert expand_query("plain words", {}) == "plain words"


import json  # noqa: E402

import pytest  # noqa: E402

from app.retrieval.query import load_synonyms  # noqa: E402


def test_load_synonyms_merges_over_defaults(tmp_path):
    p = tmp_path / "syn.json"
    p.write_text(json.dumps({"PTO": ["paid time off", "leave"], "rag": ["custom"]}))
    syn = load_synonyms(p)
    assert syn["pto"] == ["paid time off", "leave"]
    assert syn["rag"] == ["custom"]
    assert "llm" in syn
    assert expand_query("how much PTO", syn) == "how much PTO paid time off leave"


def test_load_synonyms_validates(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"x": "not a list"}))
    with pytest.raises(ValueError):
        load_synonyms(p)
    assert load_synonyms(None)["db"] == ["database"]
