"""First guard: the tutor reads plain text only, no images, files or markup.

The chat UI has no attachment button and blocks pasted images, but the API is
the real boundary: data URIs, <img>/<svg> tags, Markdown images, links to image
files and long base64 blobs are refused before anything else runs.
"""

import re
from enum import Enum

__all__ = ["MAX_MESSAGE_CHARS", "InputProblem", "check_input", "clean_input"]

MAX_MESSAGE_CHARS = 280

_NOT_TEXT = re.compile(
    r"data:\s*[a-z]+/[\w.+-]+\s*;\s*base64"
    r"|<\s*(?:img|svg|picture|video|canvas|iframe|object|embed|script)\b"
    r"|!\[[^\]]*\]\([^)]*\)"
    r"|https?://\S+\.(?:png|jpe?g|gif|webp|bmp|svg|heic|avif)\b"
    r"|[A-Za-z0-9+/]{100,}={0,2}",
    re.IGNORECASE,
)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u200b-\u200f\u2028-\u202e]")


class InputProblem(str, Enum):
    EMPTY = "empty"
    TOO_LONG = "too_long"
    NOT_TEXT = "not_text"


def clean_input(message: str) -> str:
    """Drops control and invisible characters and collapses whitespace."""
    return re.sub(r"\s+", " ", _CONTROL.sub("", message)).strip()


def check_input(message: str) -> InputProblem | None:
    """Why the message cannot be read as a text question, or None if it can."""
    text = clean_input(message)
    if not text:
        return InputProblem.EMPTY
    if _NOT_TEXT.search(text):
        return InputProblem.NOT_TEXT
    if len(text) > MAX_MESSAGE_CHARS:
        return InputProblem.TOO_LONG
    return None
