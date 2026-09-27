"""Small edits that preserve card bodies and Spaced Repetition comments."""

import os
import re
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

WIKTIONARY_LINE = re.compile(
    r"^https?://en\.wiktionary\.org/wiki/[^\s]+[ \t\r]*$", re.MULTILINE
)


def card_word(path: Path, text: str):
    """Use the original entry URL, or a tagged hand-written card's filename."""
    match = WIKTIONARY_LINE.search(text)
    if match:
        path_part = urlsplit(match.group().strip()).path
        return unquote(path_part.removeprefix("/wiki/")).replace("_", " ")
    if re.search(r"(?<!\S)#flashcards(?=[/\s]|$)", text):
        return path.stem
    return None


def append_article(text: str, article: str) -> str:
    """Insert an article without parsing or regenerating the existing card."""
    if not article.strip():
        return text
    newline = "\r\n" if "\r\n" in text else "\n"
    article = article.strip().replace("\r\n", "\n").replace("\n", newline)
    entry = article if article.startswith("- ") else f"- article - {article}"
    if entry in text.split(newline) or newline + entry + newline in text:
        return text

    section = re.search(r"^# Articles[ \t]*\r?\n", text, re.MULTILINE)
    if section:
        return text[: section.end()] + entry + newline + text[section.end() :]

    url = WIKTIONARY_LINE.search(text)
    if url:
        end = text.find("\n", url.end())
        if end == -1:
            return text + newline + "# Articles" + newline + entry + newline
        end += 1
    else:
        separator = re.search(r"^\?\??[ \t]*\r?$", text, re.MULTILINE)
        end = separator.start() if separator else len(text)
    prefix = text[:end]
    if prefix and not prefix.endswith("\n"):
        prefix += newline
    return prefix + "# Articles" + newline + entry + newline + text[end:]


def write_card(path: Path, text: str):
    """Replace a card only after its complete new contents have been written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=".card-", delete=False
        ) as f:
            temporary = Path(f.name)
            f.write(text.encode("utf-8"))
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
