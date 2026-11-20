import pytest

from app.eval.dataset import load_dataset


def test_load_dataset(tmp_path):
    p = tmp_path / "d.jsonl"
    p.write_text('{"question": "q", "relevant_sources": ["a.md"]}\n\n'
                 '{"question": "r", "relevant_sources": ["b.md"], "expected_phrases": ["x"]}\n')
    rows = load_dataset(p)
    assert len(rows) == 2 and rows[1].expected_phrases == ["x"]


def test_load_dataset_validates(tmp_path):
    p = tmp_path / "d.jsonl"
    p.write_text('{"question": "q", "relevant_sources": []}\n')
    with pytest.raises(ValueError, match="line 1"):
        load_dataset(p)
