from app.retrieval.highlight import highlight_spans


def test_highlights_stemmed_matches():
    text = "Ranking documents: BM25 ranks each document."
    spans = highlight_spans("rank the documents", text)
    assert [text[s:e] for s, e in spans] == ["Ranking", "documents", "ranks", "document"]


def test_ignores_stopwords_and_limits():
    assert highlight_spans("the of and", "the cat and the dog") == []
    assert len(highlight_spans("a", "a " * 10)) == 0
    assert len(highlight_spans("cat", "cat " * 100, max_spans=5)) == 5
