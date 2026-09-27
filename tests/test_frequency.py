import json

import pytest
from click.testing import CliRunner

from wiktionary_vocab_card.cli import cli
from wiktionary_vocab_card.frequency import FrequencyClassifier


def test_real_finnish_data_and_uncertain_forms():
    classifier = FrequencyClassifier()
    expected = {
        "olla": ("very-common", 6.44),
        "ehdokas": ("common", 4.33),
        "arvonlisävero": ("less-common", 3.34),
        "helleraja": ("rare", 1.74),
        "saada aikaan": ("unscored", None),
        "-painotteinen": ("unscored", None),
        "linja-auto": ("unscored", None),
        "qwertyolematonsanatesti": ("unscored", None),
    }
    for word, result in expected.items():
        actual = classifier.classify(word)
        assert (actual.band, actual.zipf) == result
    assert (
        classifier.classify("MA\u0308A\u0308RA\u0308").zipf
        == classifier.classify("määrä").zipf
    )


@pytest.mark.parametrize(
    "score,band",
    [
        (5, "very-common"),
        (4.99, "common"),
        (4, "common"),
        (3.99, "less-common"),
        (3, "less-common"),
        (2.99, "rare"),
    ],
)
def test_band_boundaries(monkeypatch, score, band):
    monkeypatch.setattr(
        "wiktionary_vocab_card.frequency.finnish_frequencies",
        lambda: {"sana": 10 ** (score - 9)},
    )
    assert FrequencyClassifier().classify("sana").band == band


def test_overrides_change_priority_without_inventing_scores():
    classifier = FrequencyClassifier(
        {"Helleraja": "common", "saada aikaan": "very-common"}
    )
    assert classifier.classify("helleraja").band == "common"
    assert classifier.classify("helleraja").zipf == 1.74
    assert classifier.classify("saada aikaan").zipf is None
    assert classifier.classify("saada aikaan").reason == "manual_override"
    with pytest.raises(ValueError):
        FrequencyClassifier({"sana": "A1"})


def test_classify_cli_explains_source_and_score():
    result = CliRunner().invoke(
        cli, ["classify", "--json", "ehdokas", "saada aikaan", "--", "-painotteinen"]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["source"]["version"] == "3.1.1"
    assert data["words"][0]["folder"] == "02 Common"
    assert data["words"][1]["reason"] == "phrase_or_empty"
    assert data["words"][2]["reason"] == "affix"
