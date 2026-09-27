import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from wiktionary_vocab_card.cli import cli
from wiktionary_vocab_card.frequency import FrequencyClassifier
from wiktionary_vocab_card.reorganize import MANIFEST, REPORT, copy_plan, plan_copy


def make_card(path, word="ehdokas", newline="\n"):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = f"---\nsr-due: 2026-10-05\nsr-interval: 40\nsr-ease: 250\n---\n# {word}\n#flashcards #noun\nhttp://en.wiktionary.org/wiki/{word}\n# Articles\n- [[Reading]]\n??\nA handwritten definition\n<!--SR:!2026-10-05,40,250!2026-10-08,43,260-->\n+++\n"
    path.write_bytes(text.replace("\n", newline).encode("utf-8"))
    return path.read_bytes()


def test_sorted_copy_preserves_every_byte_and_duplicate(tmp_path):
    source, destination = tmp_path / "original", tmp_path / "copy"
    first = make_card(source / "Memorizing/ehdokas.md", newline="\r\n")
    second = make_card(source / "Remembered/ehdokas.md")
    other = source / "notes.md"
    other.write_text("Not a vocabulary card\n[[ehdokas]]", encoding="utf-8")
    (source / "image.png").write_bytes(b"image bytes")
    originals = {
        str(p.relative_to(source)): p.read_bytes()
        for p in source.rglob("*")
        if p.is_file()
    }
    plan = plan_copy(source, destination, FrequencyClassifier())
    assert not destination.exists()
    report = copy_plan(plan)
    assert report.exists()
    assert (
        destination / "02 Common/Duplicates/Memorizing/ehdokas.md"
    ).read_bytes() == first
    assert (
        destination / "02 Common/Duplicates/Remembered/ehdokas.md"
    ).read_bytes() == second
    for entry in json.loads((destination / MANIFEST).read_text())["entries"]:
        assert (destination / entry["destination"]).read_bytes() == originals[
            entry["source"]
        ]
        assert (source / entry["source"]).read_bytes() == originals[entry["source"]]

    # A fresh sort regenerates its own reports while keeping all original files.
    repeat = plan_copy(destination, tmp_path / "second-copy", FrequencyClassifier())
    assert len(repeat["entries"]) == len(originals)
    (destination / REPORT).write_text("My annotations in the report", encoding="utf-8")
    with pytest.raises(ValueError, match="rename those files"):
        plan_copy(destination, tmp_path / "third-copy", FrequencyClassifier())


def test_reserved_report_name_never_discards_an_unrelated_note(tmp_path):
    source = tmp_path / "source"
    make_card(source / "ehdokas.md")
    (source / REPORT).write_text("Personal notes", encoding="utf-8")
    with pytest.raises(ValueError, match="rename those files"):
        plan_copy(source, tmp_path / "copy", FrequencyClassifier())
    assert (source / REPORT).read_text() == "Personal notes"


@pytest.mark.parametrize("target", ["same", "child", "parent", "existing"])
def test_copy_refuses_overlapping_or_existing_destination(tmp_path, target):
    source = tmp_path / "original"
    source.mkdir()
    existing = tmp_path / "existing"
    existing.mkdir()
    destination = {
        "same": source,
        "child": source / "child",
        "parent": tmp_path,
        "existing": existing,
    }[target]
    with pytest.raises(ValueError):
        plan_copy(source, destination, FrequencyClassifier())


def test_symlinks_and_changed_source_do_not_publish_partial_copy(tmp_path):
    source = tmp_path / "source"
    card = source / "ehdokas.md"
    make_card(card)
    link = source / "linked.md"
    link.symlink_to(card)
    with pytest.raises(ValueError, match="symlink"):
        plan_copy(source, tmp_path / "first", FrequencyClassifier())
    link.unlink()
    destination = tmp_path / "second"
    plan = plan_copy(source, destination, FrequencyClassifier())
    card.write_text("edited while planning")
    with pytest.raises(ValueError, match="Source changed"):
        copy_plan(plan)
    assert not destination.exists()
    assert card.read_text() == "edited while planning"


def test_dry_run_and_rerun_are_safe(tmp_path):
    source = tmp_path / "source"
    original = make_card(source / "ehdokas.md")
    destination = tmp_path / "copy"
    runner = CliRunner()
    result = runner.invoke(
        cli, ["reorganize", str(source), str(destination), "--dry-run"]
    )
    assert result.exit_code == 0, result.output
    assert "02 Common: 1" in result.output
    assert not destination.exists()
    result = runner.invoke(cli, ["reorganize", str(source), str(destination)])
    assert result.exit_code == 0, result.output
    result = runner.invoke(cli, ["reorganize", str(source), str(destination)])
    assert result.exit_code != 0
    assert "already exists" in result.output
    assert (source / "ehdokas.md").read_bytes() == original


def test_path_in_url_is_decoded_and_filename_preserved(tmp_path):
    source, destination = tmp_path / "source", tmp_path / "copy"
    make_card(source / "määra custom.md", "m%C3%A4%C3%A4r%C3%A4#Finnish")
    plan = plan_copy(source, destination, FrequencyClassifier())
    assert plan["entries"][0]["classification"]["word"] == "määrä"
    assert plan["entries"][0]["destination"] == "01 Very common/määra custom.md"
