from pathlib import Path

from app import cli
from app.config import get_settings

CORPUS = Path(__file__).resolve().parents[2] / "samples" / "corpus"


def test_index_then_ask(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("RAGFORGE_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        assert cli.main(["index", str(CORPUS), "--collection", "docs"]) == 0
        assert "done: 9 files" in capsys.readouterr().out
        assert cli.main(["ask", "What value of k is usually used in RRF?"]) == 0
        out = capsys.readouterr().out
        assert "hybrid-search.md" in out
    finally:
        get_settings.cache_clear()
