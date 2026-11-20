import pytest

from app.core.knowledge_base import KnowledgeBase, SearchOptions
from app.embeddings.hashing import HashingEmbedder
from app.ingestion.pipeline import ingest_bytes
from app.vectorstore.memory import InMemoryVectorStore

DOCS = {
    "bm25.md": "# BM25\nBM25 is a lexical ranking function based on term frequency "
               "and inverse document frequency.",
    "vectors.md": "# Vectors\nDense retrieval embeds text into vectors and finds "
                  "nearest neighbours with cosine similarity.",
    "cooking.md": "# Bread\nKnead the dough for ten minutes and bake at 220 degrees.",
}


@pytest.fixture
def kb():
    base = KnowledgeBase(HashingEmbedder(512), InMemoryVectorStore(512))
    for name, text in DOCS.items():
        base.add(ingest_bytes(text.encode(), name, chunk_size=300, chunk_overlap=0),
                 collection="cooking" if "cook" in name else "ir")
    return base


@pytest.mark.parametrize("mode", ["dense", "bm25", "hybrid"])
def test_search_modes_find_relevant_doc(kb, mode):
    hits = kb.search("what is BM25 ranking", SearchOptions(k=1, mode=mode))
    assert hits[0].chunk.metadata["source"] == "bm25.md"


def test_collection_filter(kb):
    hits = kb.search("bake bread", SearchOptions(k=3, flt={"collection": "ir"}))
    assert all(h.chunk.metadata["collection"] == "ir" for h in hits)


def test_reindexing_same_document_replaces_chunks(kb):
    before = kb.stats()
    kb.add(ingest_bytes(DOCS["bm25.md"].encode(), "bm25.md"), collection="ir")
    assert kb.stats() == before


def test_delete_removes_from_both_indexes(kb):
    doc_id = kb.search("BM25", SearchOptions(k=1, mode="bm25"))[0].chunk.doc_id
    assert kb.delete(doc_id) >= 1
    for mode in ("bm25", "dense"):
        hits = kb.search("BM25 lexical ranking", SearchOptions(k=5, mode=mode))
        assert all(h.chunk.doc_id != doc_id for h in hits)


def test_empty_query_returns_nothing(kb):
    assert kb.search("   ?? ") == []


def test_stats(kb):
    assert kb.stats()["documents"] == 3


from app.core.knowledge_base import chunk_header  # noqa: E402


def test_chunk_header_combines_source_and_section():
    assert chunk_header({"source": "dense-retrieval.md", "section": "Dense retrieval > Why"}) \
        == "dense retrieval > Dense retrieval > Why"
    assert chunk_header({}) == ""
