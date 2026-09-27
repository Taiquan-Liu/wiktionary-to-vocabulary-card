from pathlib import Path

import pytest
import yaml
from bs4 import BeautifulSoup
from click.testing import CliRunner

from wiktionary_vocab_card.cards import append_article
from wiktionary_vocab_card.cli import cli
from wiktionary_vocab_card.config import load_config
from wiktionary_vocab_card.file_manager import FileManager
from wiktionary_vocab_card.parser import WiktionaryParser
from wiktionary_vocab_card.utils import open_in_obsidian


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
@pytest.mark.parametrize("articles_first", [True, False])
def test_existing_card_keeps_deck_schedule_and_hand_edits(
    isolated_config, newline, articles_first
):
    _, config = isolated_config
    root = Path(config["vault"]["path"])
    path = root / "01 Very common/renamed by user.md"
    path.parent.mkdir()
    articles = "# Articles\n- article - First article\n"
    answer = "??\n# noun\nA personal definition\n?\nA second card\n<!--SR:!2026-10-05,50,250!2026-10-07,52,240-->\n+++\n"
    original = "---\naliases: [candidate]\nsr-due: 2026-10-05\n---\n# ehdokas\n#flashcards #my-tag\nhttps://en.wiktionary.org/wiki/ehdokas\n"
    original += articles + answer if articles_first else answer + articles
    original = original.replace("\n", newline)
    path.write_bytes(original.encode("utf-8"))
    # A passed config takes precedence over anything in the default config file.
    manager = FileManager(config)
    final, moved = manager.process_wordcard(
        "ehdokas", {"word_sections": ["replacement must not appear"]}, "Second article"
    )
    assert final == path and not moved
    updated = path.read_bytes().decode("utf-8")
    assert updated.replace("- article - Second article" + newline, "") == original
    manager.process_wordcard("ehdokas", {}, "Second article")
    assert path.read_bytes().decode("utf-8") == updated


def test_insert_articles_before_card_without_touching_schedule():
    original = "# kissa\n#flashcards\nhttps://en.wiktionary.org/wiki/kissa\n??\ncat\n<!--SR:!2026-10-05,50,250-->\n+++\n"
    updated = append_article(original, "A cat article")
    assert updated.split("??")[1] == original.split("??")[1]
    assert updated.replace("# Articles\n- article - A cat article\n", "") == original


def test_config_override_does_not_modify_default(isolated_config, tmp_path):
    default_path, _ = isolated_config
    original = default_path.read_bytes()
    alternate = tmp_path / "alternate.yaml"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--config",
            str(alternate),
            "configure",
            "--organization",
            "frequency",
            "--vault-path",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert yaml.safe_load(alternate.read_text())["vault"]["path"] == str(tmp_path)
    assert default_path.read_bytes() == original
    assert load_config()["vault"]["path"] != str(tmp_path)


def test_missing_config_read_is_non_mutating(tmp_path, monkeypatch):
    path = tmp_path / "does-not-exist/config.yaml"
    monkeypatch.setenv("WIKT_VOCAB_CONFIG", str(path))
    first = load_config()
    assert first["vault"]["organization"] == "frequency"
    assert first["vault"]["path"] == str(Path.home() / "Documents/1st remote/Suomi")
    first["vault"]["name"] = "changed"
    assert load_config()["vault"]["name"] != "changed"
    assert not path.parent.exists()


def test_default_html_to_frequency_deck_then_second_import(
    isolated_config, monkeypatch
):
    config_path, config = isolated_config
    del config["vault"]["organization"]
    config_path.write_text(yaml.safe_dump(config))
    example = Path(__file__).resolve().parents[1] / "examples/ehdokas.html"

    def fetch_fixture(parser):
        parser.soup = BeautifulSoup(example.read_bytes(), "html.parser")

    monkeypatch.setattr(WiktionaryParser, "fetch_page", fetch_fixture)
    runner = CliRunner()
    args = [
        "generate",
        "https://en.wiktionary.org/wiki/ehdokas",
        "--no-open",
    ]
    result = runner.invoke(cli, args + ["-t", "First article"])
    assert result.exit_code == 0, result.output
    path = Path(config["vault"]["path"]) / "02 Common/ehdokas.md"
    assert path.exists()
    original = path.read_text(encoding="utf-8").replace(
        "+++", "<!--SR:!2026-10-05,50,250-->\n+++"
    )
    path.write_text(original, encoding="utf-8")
    result = runner.invoke(cli, args + ["-t", "Second article"])
    assert result.exit_code == 0, result.output
    updated = path.read_text(encoding="utf-8")
    assert updated.replace("- article - Second article\n", "") == original
    assert len(list(Path(config["vault"]["path"]).rglob("ehdokas.md"))) == 1


def test_file_manager_defaults_to_frequency_and_accepts_explicit_stages(
    isolated_config,
):
    _, config = isolated_config
    del config["vault"]["organization"]
    assert (
        FileManager(config).determine_target_location("ehdokas")[0].parent.name
        == "02 Common"
    )
    config["vault"]["organization"] = "stages"
    assert (
        FileManager(config).determine_target_location("ehdokas")[0].parent.name == "New"
    )


def test_explicit_output_does_not_require_a_vault(
    isolated_config, tmp_path, monkeypatch
):
    config_path, config = isolated_config
    config["vault"]["path"] = str(tmp_path / "missing-vault")
    config_path.write_text(yaml.safe_dump(config))
    example = Path(__file__).resolve().parents[1] / "examples/ehdokas.html"

    def fetch_fixture(parser):
        parser.soup = BeautifulSoup(example.read_bytes(), "html.parser")

    monkeypatch.setattr(WiktionaryParser, "fetch_page", fetch_fixture)
    output = tmp_path / "card.md"
    result = CliRunner().invoke(
        cli,
        [
            "generate",
            "https://en.wiktionary.org/wiki/ehdokas",
            "--no-open",
            "-o",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.output
    assert output.read_text().startswith("# ehdokas")
    assert not (tmp_path / "missing-vault").exists()


def test_duplicate_import_is_an_error_and_cannot_overwrite(
    isolated_config, monkeypatch
):
    _, config = isolated_config
    root = Path(config["vault"]["path"])
    text = "https://en.wiktionary.org/wiki/ehdokas\n??\nDefinition\n+++\n"
    for folder in ("01 Very common", "02 Common"):
        (root / folder).mkdir()
        (root / folder / "ehdokas.md").write_text(text)
    with pytest.raises(ValueError, match="Multiple cards"):
        FileManager(config).process_wordcard("ehdokas", {}, "new article")
    for path in root.rglob("*.md"):
        assert path.read_text() == text


def test_new_import_refuses_noncard_filename_collision(isolated_config):
    _, config = isolated_config
    path = Path(config["vault"]["path"]) / "02 Common/ehdokas.md"
    path.parent.mkdir()
    path.write_text("An unrelated note")
    with pytest.raises(ValueError, match="Refusing to overwrite"):
        FileManager(config).process_wordcard("ehdokas", {}, "article")
    assert path.read_text() == "An unrelated note"


def test_obsidian_opens_card_relative_to_actual_vault(tmp_path, monkeypatch):
    from urllib.parse import parse_qs, urlsplit

    vault = tmp_path / "test-vault"
    (vault / ".obsidian").mkdir(parents=True)
    folder = vault / "Suomi"
    path = folder / "02 Common/määrä.md"
    calls = []
    monkeypatch.setattr(
        "wiktionary_vocab_card.utils.subprocess.run",
        lambda args, **kwargs: calls.append(args),
    )
    assert open_in_obsidian(path, folder)
    assert parse_qs(urlsplit(calls[0][1]).query) == {
        "vault": ["test-vault"],
        "file": ["Suomi/02 Common/määrä.md"],
    }


def test_missing_frequency_vault_is_an_error_before_network(isolated_config):
    path, config = isolated_config
    config["vault"]["path"] += "/missing"
    path.write_text(yaml.safe_dump(config))
    result = CliRunner().invoke(
        cli, ["generate", "https://en.wiktionary.org/wiki/ehdokas", "--no-open"]
    )
    assert result.exit_code != 0
    assert "requires an existing vocabulary folder" in result.output


def test_failed_legacy_move_keeps_source(isolated_config, monkeypatch):
    _, config = isolated_config
    config["vault"]["organization"] = "stages"
    path = Path(config["vault"]["path"]) / "Remembered/ehdokas.md"
    path.parent.mkdir()
    text = "# ehdokas\nhttps://en.wiktionary.org/wiki/ehdokas\n# noun\nMy definition\n"
    path.write_text(text)
    manager = FileManager(config)
    monkeypatch.setattr(manager, "save_wordcard", lambda *args: False)
    with pytest.raises(RuntimeError):
        manager.process_wordcard("ehdokas", {}, "article")
    assert path.read_text() == text
