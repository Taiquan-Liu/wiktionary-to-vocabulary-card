"""Plan and publish a sorted copy; never move or rewrite source notes."""

import hashlib
import json
import shutil
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import quote

from .cards import card_word
from .frequency import BANDS, FrequencyClassifier

MANIFEST = ".frequency-manifest.json"
REPORT = "Frequency report.md"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def path_key(path: Path) -> str:
    # Obsidian vaults are often shared between case-insensitive filesystems.
    return unicodedata.normalize("NFC", path.as_posix()).casefold()


def plan_copy(source: Path, destination: Path, classifier: FrequencyClassifier):
    source = source.expanduser().resolve()
    destination = destination.expanduser().resolve()
    if not source.is_dir():
        raise ValueError(f"Source is not a directory: {source}")
    if (
        source == destination
        or destination.is_relative_to(source)
        or source.is_relative_to(destination)
    ):
        raise ValueError(
            "Source and destination must be separate, non-overlapping folders"
        )
    if destination.exists():
        raise ValueError(
            f"Destination already exists; choose a new folder: {destination}"
        )

    generated_reports = set()
    manifest_path, report_path = source / MANIFEST, source / REPORT
    if manifest_path.exists() or report_path.exists():
        try:
            previous = json.loads(manifest_path.read_text(encoding="utf-8"))
            if previous["schema"] != 1 or report_path.read_text(
                encoding="utf-8"
            ) != report_text(previous):
                raise ValueError("Report has been edited")
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise ValueError(
                f"Reserved report filenames contain unrecognized or edited files in {source}; "
                "rename those files before copying so their contents are preserved"
            ) from error
        generated_reports = {MANIFEST, REPORT}

    entries = []
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if path.is_symlink():
            raise ValueError(
                f"Source contains a symlink; copy real files instead: {path}"
            )
        if not path.is_file():
            continue
        # A previous copy's reports describe an older layout and are regenerated.
        if relative.as_posix() in generated_reports:
            continue
        data = path.read_bytes()
        entry = {
            "source": relative.as_posix(),
            "destination": relative.as_posix(),
            "sha256": digest(data),
            "classification": None,
        }
        if path.suffix.lower() == ".md" and not any(
            part.startswith(".") for part in relative.parts
        ):
            text = data.decode("utf-8")
            word = card_word(path, text)
            if word:
                result = classifier.classify(word)
                entry["classification"] = result.to_dict()
                entry["destination"] = (Path(result.folder) / path.name).as_posix()
        entries.append(entry)

    counts = Counter(path_key(Path(entry["destination"])) for entry in entries)
    for entry in entries:
        if counts[path_key(Path(entry["destination"]))] > 1:
            # Keep every version, including test cards, without picking a winner.
            band = entry["classification"]
            parent = Path(band["folder"]) if band else Path("Unsorted")
            entry["destination"] = (parent / "Duplicates" / entry["source"]).as_posix()
            entry["duplicate"] = True

    targets = [path_key(Path(entry["destination"])) for entry in entries]
    if len(targets) != len(set(targets)):
        raise ValueError("Some names still collide after preserving duplicate folders")
    reserved = {path_key(Path(MANIFEST)), path_key(Path(REPORT))}
    all_targets = set(targets) | reserved
    for entry in entries:
        target = Path(entry["destination"])
        if path_key(target) in reserved or any(
            path_key(parent) in all_targets
            for parent in target.parents
            if parent != Path(".")
        ):
            raise ValueError(f"Destination file/directory conflict: {target}")

    return {
        "schema": 1,
        "source_root": str(source),
        "destination_root": str(destination),
        "frequency_source": classifier.source,
        "bands": [
            {"key": band.key, "folder": band.folder, "minimum_zipf": band.minimum}
            for band in BANDS
        ],
        "overrides": classifier.overrides,
        "entries": entries,
    }


def report_text(plan):
    cards = [entry for entry in plan["entries"] if entry["classification"]]
    counts = Counter(entry["classification"]["folder"] for entry in cards)
    duplicates = [entry for entry in plan["entries"] if entry.get("duplicate")]
    lines = [
        "# Finnish vocabulary by frequency",
        "",
        "Study the first two decks when time is limited. Use the less common and rare decks for words relevant to your current reading. Review Unscored manually.",
        "",
        "These are word-form frequencies, not CEFR levels. Finnish inflections divide a lemma's usage across many spellings. Missing words, phrases and affixes have no assigned score.",
        "",
        f"Copied {len(cards)} vocabulary notes and {len(plan['entries']) - len(cards)} other files. Every copied file retains its original bytes, including review schedules, tags, edits and article links.",
        "",
        f"Source: `{plan['source_root']}`",
        "",
        "| Deck | Notes | Zipf range |",
        "| --- | ---: | --- |",
    ]
    ranges = ["5 and above", "4 to below 5", "3 to below 4", "Below 3", "No score"]
    for band, bounds in zip(BANDS, ranges):
        lines.append(f"| {band.folder} | {counts[band.folder]} | {bounds} |")
    lines += [
        "",
        "The Spaced Repetition plugin must have **Convert folders to decks** enabled. Review intervals still come from the plugin. Moving a card between these folders changes its priority without resetting its schedule.",
        "",
        "Path-specific links from elsewhere in the original vault may need updates before a future replacement. This copy does not change those notes. Links to articles outside this copied folder require those articles in the test vault.",
        "",
    ]
    if duplicates:
        lines += [
            "## Duplicate names",
            "",
            "Both versions are preserved in their deck's Duplicates subfolders. Inspect them before importing the same word again; the CLI refuses to choose between duplicate cards.",
            "",
        ]
        for entry in duplicates:
            lines.append(
                f"- `{entry['source']}` → [{entry['destination']}]({quote(entry['destination'])})"
            )
        lines.append("")
    for band in BANDS:
        lines += [
            f"## {band.folder}",
            "",
            "| Word | Zipf | Basis |",
            "| --- | ---: | --- |",
        ]
        for entry in sorted(
            cards,
            key=lambda item: (-(item["classification"]["zipf"] or 0), item["source"]),
        ):
            result = entry["classification"]
            if result["band"] == band.key:
                score = (
                    "unscored" if result["zipf"] is None else f"{result['zipf']:.2f}"
                )
                word = (
                    result["word"]
                    .replace("|", "\\|")
                    .replace("[", "\\[")
                    .replace("]", "\\]")
                )
                lines.append(
                    f"| [{word}]({quote(entry['destination'])}) | {score} | {result['reason']} |"
                )
        lines.append("")
    source = plan["frequency_source"]
    lines += [
        "## Data attribution",
        "",
        f"[wordfreq {source['version']}]({source['url']}), by Robyn Speer and contributors. Bundled frequency data is [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/); package code is Apache 2.0. Lookups use the bundled Finnish large wordlist. See the package for upstream corpus attributions.",
        "",
    ]
    return "\n".join(lines)


def copy_plan(plan):
    source = Path(plan["source_root"])
    destination = Path(plan["destination_root"])
    if destination.exists():
        raise ValueError(f"Destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Build outside the source and publish the complete copy at once.
    with tempfile.TemporaryDirectory(
        prefix=".frequency-copy-", dir=destination.parent
    ) as temporary:
        staging = Path(temporary) / "cards"
        staging.mkdir()
        for entry in plan["entries"]:
            original = source / entry["source"]
            data = original.read_bytes()
            if original.is_symlink() or digest(data) != entry["sha256"]:
                raise ValueError(f"Source changed during copying; retry: {original}")
            target = staging / entry["destination"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            shutil.copystat(original, target)
            if digest(target.read_bytes()) != entry["sha256"]:
                raise OSError(f"Copy verification failed: {target}")
        for band in BANDS:
            (staging / band.folder).mkdir(exist_ok=True)
        (staging / MANIFEST).write_text(
            json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (staging / REPORT).write_text(report_text(plan), encoding="utf-8")
        if destination.exists():
            raise ValueError(f"Destination appeared during copying: {destination}")
        staging.rename(destination)
    return destination / REPORT
