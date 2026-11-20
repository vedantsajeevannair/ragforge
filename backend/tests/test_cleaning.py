from app.ingestion.cleaning import (
    clean_text,
    collapse_whitespace,
    join_hyphenated_breaks,
    strip_control_chars,
)


def test_collapse_whitespace_squeezes_spaces_and_blank_lines():
    raw = "a   b\t\tc\r\n\n\n\n d "
    assert collapse_whitespace(raw) == "a b c\n\nd"


def test_strip_control_chars_keeps_newlines():
    assert strip_control_chars("a\x00b\nc\x07") == "ab\nc"


def test_join_hyphenated_breaks():
    assert join_hyphenated_breaks("retrie-\nval works") == "retrieval works"


def test_clean_text_normalises_unicode_ligatures():
    assert clean_text("eﬃcient") == "efficient"
