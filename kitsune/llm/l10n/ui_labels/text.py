"""Clean up text before comparing a label with a product's string."""

import html
import re
import unicodedata

CURLY_QUOTES = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})


def normalize(text: str) -> str:
    """Remove differences that never matter when comparing labels: HTML entities,
    curly quotes, three dots for an ellipsis, extra or non-breaking spaces, and whether
    an accented letter is one character or two."""
    text = html.unescape(text).translate(CURLY_QUOTES).replace("...", "…")
    return unicodedata.normalize("NFC", " ".join(text.split()))


def loosen(text: str) -> str:
    """Also ignore case and a trailing ellipsis, colon or period: "Save As..." is "save as"."""
    text = normalize(text)
    return (re.sub(r"[…:.\s]+$", "", text) or text).casefold()
