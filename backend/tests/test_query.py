from app.retrieval.query import expand_query, normalize_query


def test_normalize_strips_filler_and_punctuation():
    assert normalize_query("  Can you  explain how RAG works?? ") == "how RAG works"


def test_expand_adds_synonyms():
    assert expand_query("what is RAG") == "what is RAG retrieval augmented generation"
    assert expand_query("plain words", {}) == "plain words"
