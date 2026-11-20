import pytest

from app.text.tokenize import stem, terms, tokenize


def test_tokenize_lowercases_and_splits():
    assert tokenize("Hello, World! It's 2026.") == ["hello", "world", "it's", "2026"]


@pytest.mark.parametrize(
    "word,expected",
    [("documents", "document"), ("queries", "query"), ("indexing", "index"),
     ("ranked", "rank"), ("rankings", "rank"), ("boxes", "box"), ("classes", "class"), ("is", "is")],
)
def test_stem(word, expected):
    assert stem(word) == expected


def test_terms_drops_stopwords():
    assert terms("The retrieval of documents") == ["retrieval", "document"]
