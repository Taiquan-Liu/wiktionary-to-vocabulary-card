from pathlib import Path

import pytest
import requests
import yaml
from click.testing import CliRunner

from wiktionary_vocab_card.cards import append_article, card_word
from wiktionary_vocab_card.cli import cli
from wiktionary_vocab_card.file_manager import FileManager
from wiktionary_vocab_card.parser import WiktionaryParser

ENTRY_URL = "https://en.wiktionary.org/wiki/valtio"
REDIRECT_URL = "https://en.wiktionary.org/w/index.php?title=valtio&rdfrom=Valtio"
CAPITALIZED_URL = "https://en.wiktionary.org/wiki/Valtio"
ENTRY_HTML = """
<html><head></head><body>
<h1 id="firstHeading">valtio</h1>
<div id="contentSub">(Auto-redirected from Valtio)</div>
<div class="mw-heading mw-heading2"><h2 id="Finnish">Finnish</h2></div>
<div class="mw-heading mw-heading3"><h3 id="Noun">Noun</h3></div>
<ol><li>state, country</li></ol>
</body></html>
"""
MISSING_HTML = """
<h1>Valtio</h1>
Did you mean <span id="did-you-mean"><a href="/wiki/valtio">valtio</a></span>?
"""


def page_response(url=ENTRY_URL, html=ENTRY_HTML, status=200):
    response = requests.Response()
    response.url = url
    response.status_code = status
    response._content = html.encode("utf-8")
    return response


@pytest.mark.parametrize(
    "url",
    [
        ENTRY_URL,
        REDIRECT_URL,
        REDIRECT_URL + "#Finnish",
        ENTRY_URL + "?rdfrom=Valtio#Finnish",
        "https://en.wiktionary.org/w/index.php?rdfrom=Valtio&title=valtio",
    ],
)
def test_parser_uses_destination_word(url):
    parser = WiktionaryParser(url)

    assert parser.word == "valtio"
    assert parser.url == ENTRY_URL


@pytest.mark.parametrize(
    ("entry", "word", "path"),
    [
        ("wiki/Suomi", "Suomi", "Suomi"),
        ("wiki/yski%C3%A4#Finnish", "yskiä", "yski%C3%A4"),
        ("w/index.php?title=yski%C3%A4&rdfrom=Yski%C3%A4", "yskiä", "yski%C3%A4"),
        ("wiki/saada_aikaan", "saada aikaan", "saada_aikaan"),
        ("w/index.php?title=saada+aikaan", "saada aikaan", "saada_aikaan"),
        ("w/index.php?title=saada%20aikaan", "saada aikaan", "saada_aikaan"),
        ("wiki/a+b", "a+b", "a%2Bb"),
        ("w/index.php?title=a%2Bb", "a+b", "a%2Bb"),
        ("w/index.php?title=%2520", "%20", "%2520"),
        ("w/index.php?title=a%26b%23c", "a&b#c", "a%26b%23c"),
    ],
)
def test_entry_title_keeps_case_and_decodes_once(entry, word, path):
    parser = WiktionaryParser("https://en.wiktionary.org/" + entry)

    assert parser.word == word
    assert parser.url == "https://en.wiktionary.org/wiki/" + path


@pytest.mark.parametrize(
    "url",
    [
        "https://en.wiktionary.org/w/index.php?rdfrom=Valtio",
        "https://en.wiktionary.org/w/index.php?title=",
        "https://en.wiktionary.org/wiki/",
        "https://example.com/wiki/valtio",
    ],
)
def test_rejects_urls_without_a_wiktionary_entry(url):
    with pytest.raises(ValueError, match="Wiktionary"):
        WiktionaryParser(url)


@pytest.mark.parametrize("final_url", [ENTRY_URL, REDIRECT_URL])
def test_http_redirect_updates_word_and_source_url(mocker, final_url):
    mocker.patch(
        "wiktionary_vocab_card.parser.requests.get",
        return_value=page_response(url=final_url),
    )

    parser = WiktionaryParser(CAPITALIZED_URL).parse()

    assert parser.word == "valtio"
    assert parser.url == ENTRY_URL
    assert parser.definitions == ["1. state, country"]


def test_page_canonical_url_resolves_redirect_with_unchanged_response_url(mocker):
    html = ENTRY_HTML.replace(
        "</head>", f'<link rel="canonical" href="{ENTRY_URL}"></head>'
    )
    mocker.patch(
        "wiktionary_vocab_card.parser.requests.get",
        return_value=page_response(url=CAPITALIZED_URL, html=html),
    )

    parser = WiktionaryParser(CAPITALIZED_URL).parse()

    assert parser.word == "valtio"
    assert parser.url == ENTRY_URL


def test_existing_capitalized_entry_keeps_its_title(mocker):
    url = "https://en.wiktionary.org/wiki/Suomi"
    get = mocker.patch(
        "wiktionary_vocab_card.parser.requests.get",
        return_value=page_response(url=url, html=ENTRY_HTML.replace("valtio", "Suomi")),
    )

    parser = WiktionaryParser(url).parse()

    assert parser.word == "Suomi"
    assert parser.url == url
    assert get.call_count == 1


def test_follows_missing_pages_did_you_mean_link(mocker):
    get = mocker.patch(
        "wiktionary_vocab_card.parser.requests.get",
        side_effect=[
            page_response(url=CAPITALIZED_URL, html=MISSING_HTML, status=404),
            page_response(),
        ],
    )

    parser = WiktionaryParser(CAPITALIZED_URL).parse()

    assert parser.word == "valtio"
    assert parser.url == ENTRY_URL
    assert parser.definitions == ["1. state, country"]
    assert [call.args[0] for call in get.call_args_list] == [CAPITALIZED_URL, ENTRY_URL]


@pytest.mark.parametrize(
    ("status", "html"),
    [
        (404, "<h1>Missing entry</h1>"),
        (403, MISSING_HTML),
        (500, MISSING_HTML),
        (404, MISSING_HTML.replace("/wiki/valtio", CAPITALIZED_URL)),
        (404, MISSING_HTML.replace("/wiki/valtio", "https://example.com/wiki/valtio")),
    ],
)
def test_preserves_http_errors_without_following_unusable_suggestions(
    mocker, status, html
):
    get = mocker.patch(
        "wiktionary_vocab_card.parser.requests.get",
        return_value=page_response(url=CAPITALIZED_URL, html=html, status=status),
    )

    with pytest.raises(requests.HTTPError):
        WiktionaryParser(CAPITALIZED_URL).parse()

    assert get.call_count == 1


def test_did_you_mean_retry_is_bounded(mocker):
    get = mocker.patch(
        "wiktionary_vocab_card.parser.requests.get",
        side_effect=[
            page_response(url=CAPITALIZED_URL, html=MISSING_HTML, status=404),
            page_response(
                html=MISSING_HTML.replace("/wiki/valtio", "/wiki/Valtio"), status=404
            ),
        ],
    )

    with pytest.raises(requests.HTTPError):
        WiktionaryParser(CAPITALIZED_URL).parse()

    assert get.call_count == 2


@pytest.mark.parametrize("url", [ENTRY_URL, REDIRECT_URL, CAPITALIZED_URL])
def test_cli_import_and_repeat_use_one_canonical_card(isolated_config, mocker, url):
    _, config = isolated_config
    responses = [page_response(), page_response()]
    if url == CAPITALIZED_URL:
        responses.insert(0, page_response(url=url, html=MISSING_HTML, status=404))
    get = mocker.patch(
        "wiktionary_vocab_card.parser.requests.get", side_effect=responses
    )
    runner = CliRunner()

    result = runner.invoke(cli, ["generate", url, "--no-open", "-t", "First article"])

    assert result.exit_code == 0, result.output
    cards = list(Path(config["vault"]["path"]).rglob("*.md"))
    assert len(cards) == 1
    assert cards[0].name == "valtio.md"
    original = cards[0].read_text(encoding="utf-8")
    assert original.startswith("# valtio\n")
    assert ENTRY_URL + "\n" in original
    assert "1. state, country" in original
    assert "Auto-redirected" not in original
    assert "rdfrom" not in original
    assert get.call_args_list[0].args[0] == (
        CAPITALIZED_URL if url == CAPITALIZED_URL else ENTRY_URL
    )

    result = runner.invoke(
        cli, ["generate", ENTRY_URL, "--no-open", "-t", "Second article"]
    )

    assert result.exit_code == 0, result.output
    assert list(Path(config["vault"]["path"]).rglob("*.md")) == cards
    assert (
        cards[0].read_text(encoding="utf-8").replace("- article - Second article\n", "")
        == original
    )


def test_cli_without_vault_uses_resolved_word_in_filename(
    isolated_config, tmp_path, mocker
):
    config_path, config = isolated_config
    config["vault"].update(path="", organization="stages")
    config["default_output"] = str(tmp_path / "card")
    config_path.write_text(yaml.safe_dump(config))
    mocker.patch(
        "wiktionary_vocab_card.parser.requests.get", return_value=page_response()
    )

    result = CliRunner().invoke(cli, ["generate", REDIRECT_URL, "--no-open"])

    assert result.exit_code == 0, result.output
    assert (tmp_path / "card_valtio.md").read_text().startswith("# valtio\n")


def test_existing_card_with_redirect_url_keeps_identity_and_contents(isolated_config):
    _, config = isolated_config
    path = Path(config["vault"]["path"]) / "renamed by user.md"
    original = f"# valtio\n{REDIRECT_URL}\n??\nMy definition\n<!--SR:!2026-10-05,50,250-->\n+++\n"
    path.write_text(original, encoding="utf-8")

    assert card_word(path, original) == "valtio"
    expected = original.replace(
        REDIRECT_URL + "\n", REDIRECT_URL + "\n# Articles\n- article - New article\n"
    )
    assert append_article(original, "New article") == expected
    manager = FileManager(config)
    final, moved = manager.process_wordcard("valtio", {}, "New article")
    assert final == path and not moved
    assert path.read_text(encoding="utf-8") == expected
    assert manager.parse_existing_wordcard(path)["url"] == REDIRECT_URL
