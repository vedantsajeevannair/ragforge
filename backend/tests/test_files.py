import pytest

from app.core.files import FileStore, safe_filename


@pytest.mark.parametrize("raw,expected", [
    ("report.pdf", "report.pdf"),
    ("../../etc/passwd", "passwd"),
    ("C:\\Users\\me\\notes final.md", "notes_final.md"),
    ("...", "upload"),
    ("héllo wörld.txt", "h_llo_w_rld.txt"),
])
def test_safe_filename(raw, expected):
    assert safe_filename(raw) == expected


def test_safe_filename_keeps_extension_when_truncating():
    assert safe_filename("a" * 200 + ".pdf", max_length=20) == "a" * 16 + ".pdf"


def test_file_store_round_trip(tmp_path):
    store = FileStore(tmp_path / "files")
    store.save("0123456789abcdef", b"data")
    assert store.load("0123456789abcdef") == b"data"
    store.delete("0123456789abcdef")
    assert store.load("0123456789abcdef") is None


def test_file_store_rejects_path_tricks(tmp_path):
    with pytest.raises(ValueError):
        FileStore(tmp_path).save("../escape", b"x")


def test_disabled_store_is_noop():
    store = FileStore(None)
    store.save("0123456789abcdef", b"x")
    assert store.load("0123456789abcdef") is None
