"""Resolve Wiktionary entry titles from article and index.php URLs."""

from urllib.parse import parse_qs, quote, unquote, urlsplit


def parse_entry_url(url: str) -> tuple[str, str]:
    """Return a clean article URL and decoded word, preserving title case."""
    parts = urlsplit(url.strip())
    title = ""
    if (
        parts.scheme in {"http", "https"}
        and parts.netloc.lower() == "en.wiktionary.org"
    ):
        if parts.path.startswith("/wiki/"):
            title = unquote(parts.path.removeprefix("/wiki/"))
        elif parts.path == "/w/index.php":
            # parse_qs already decodes percent escapes and query-string spaces.
            title = parse_qs(parts.query, keep_blank_values=True).get("title", [""])[0]

    word = title.replace("_", " ").strip()
    if not word:
        raise ValueError("Expected an English Wiktionary entry URL with a page title")

    path = quote(word.replace(" ", "_"), safe="/:")
    return f"https://en.wiktionary.org/wiki/{path}", word
