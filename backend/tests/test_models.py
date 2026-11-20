from app.ingestion.models import Chunk, Document


def test_doc_id_is_stable_and_content_based():
    a = Document(text="hello", source="a.txt")
    b = Document(text="hello", source="a.txt")
    c = Document(text="hello!", source="a.txt")
    assert a.doc_id == b.doc_id
    assert a.doc_id != c.doc_id
    assert len(a.doc_id) == 16


def test_chunk_id_combines_doc_and_index():
    chunk = Chunk(text="x", doc_id="abc", index=3, start=0, end=1)
    assert chunk.chunk_id == "abc:3"
