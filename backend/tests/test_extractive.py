from app.generation.extractive import NOT_FOUND, ExtractiveProvider
from app.generation.prompt import build_user_prompt
from app.vectorstore.base import SearchHit, StoredChunk


def _prompt(question, *texts):
    hits = [SearchHit(StoredChunk(str(i), "d", t, {"source": f"s{i}"}), 1.0)
            for i, t in enumerate(texts)]
    return build_user_prompt(question, hits)


def test_extractive_picks_matching_sentence_with_citation():
    user = _prompt("What does BM25 rank by?",
                   "Cats nap. BM25 ranks documents by term frequency.",
                   "Vectors use cosine similarity.")
    answer = ExtractiveProvider(max_sentences=1).complete("", user)
    assert answer == "BM25 ranks documents by term frequency. [1]"


def test_extractive_cites_second_passage():
    user = _prompt("cosine similarity", "Nothing here.", "Vectors use cosine similarity.")
    assert ExtractiveProvider().complete("", user).endswith("[2]")


def test_extractive_returns_not_found():
    user = _prompt("quantum physics", "Bread needs flour.")
    assert ExtractiveProvider().complete("", user) == NOT_FOUND


def test_extractive_dedupes_sentences():
    user = _prompt("vector search", "Vector search is fast.", "Vector search is fast.")
    assert ExtractiveProvider().complete("", user).count("Vector search is fast.") == 1


def test_extractive_does_not_quote_markdown_headings():
    user = _prompt("How does fusion merge lists?",
                   "## Reciprocal rank fusion\nFusion merges ranked lists without scores.")
    answer = ExtractiveProvider(max_sentences=1).complete("", user)
    assert answer == "Fusion merges ranked lists without scores. [1]"


def test_extractive_drops_weak_filler_sentences():
    user = _prompt("How does reciprocal rank fusion combine rankings?",
                   "Reciprocal rank fusion combines rankings by summing reciprocal ranks.",
                   "Mean reciprocal rank rewards early hits.",
                   "BM25 is a ranking function.")
    answer = ExtractiveProvider().complete("", user)
    assert answer == "Reciprocal rank fusion combines rankings by summing reciprocal ranks. [1]"


def test_extractive_ignores_question_words():
    user = _prompt("How does fusion work?",
                   "Fusion merges rankings.", "This shows how relevant a document is.")
    assert ExtractiveProvider().complete("", user) == "Fusion merges rankings. [1]"
