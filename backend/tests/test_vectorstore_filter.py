from app.vectorstore.base import matches


def test_matches_empty_filter():
    assert matches({"a": 1}, None)
    assert matches({"a": 1}, {})


def test_matches_exact_and_any_of():
    meta = {"type": "pdf", "collection": "hr"}
    assert matches(meta, {"type": "pdf"})
    assert not matches(meta, {"type": "html"})
    assert matches(meta, {"collection": ["hr", "legal"]})
    assert not matches(meta, {"collection": ["legal"]})
    assert not matches(meta, {"missing": 1})


def test_matches_or_clause():
    flt = {"collection": "hr", "$or": [{"visibility": "shared"}, {"owner_id": 7}]}
    assert matches({"collection": "hr", "visibility": "shared", "owner_id": 1}, flt)
    assert matches({"collection": "hr", "visibility": "private", "owner_id": 7}, flt)
    assert not matches({"collection": "hr", "visibility": "private", "owner_id": 1}, flt)
    assert not matches({"collection": "it", "visibility": "shared"}, flt)
