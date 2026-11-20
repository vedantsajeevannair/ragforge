"""Text normalisation applied before chunking."""

import re
import unicodedata

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SPACES = re.compile(r"[ \t ]+")
_BLANK_LINES = re.compile(r"\n{3,}")
_HYPHEN_BREAK = re.compile(r"(\w)-\n(\w)")


def normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def strip_control_chars(text: str) -> str:
    return _CONTROL.sub("", text)


def collapse_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _SPACES.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    return _BLANK_LINES.sub("\n\n", text).strip()


def join_hyphenated_breaks(text: str) -> str:
    """Re-join words split across lines by PDF hyphenation, e.g. 'retrie-\\nval'."""
    return _HYPHEN_BREAK.sub(r"\1\2", text)


def clean_text(text: str) -> str:
    text = normalize_unicode(text)
    text = strip_control_chars(text)
    text = join_hyphenated_breaks(text)
    return collapse_whitespace(text)
