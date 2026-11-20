import pytest

from app.ingestion.sniff import ContentMismatch, check_content


def test_accepts_matching_content(fixtures_dir):
    check_content((fixtures_dir / "sample.pdf").read_bytes(), "a.pdf")
    check_content((fixtures_dir / "policy.docx").read_bytes(), "a.docx")
    check_content(b"plain text", "a.txt")
    check_content("utf-16 text".encode("utf-16"), "a.txt")


@pytest.mark.parametrize("data,name", [
    (b"MZ\x90\x00binary", "renamed.pdf"),
    (b"%PDF-1.7", "fake.docx"),
    (b"\x7fELF\x02\x01\x01\x00\x00", "notes.txt"),
])
def test_rejects_mismatched_content(data, name):
    with pytest.raises(ContentMismatch):
        check_content(data, name)
