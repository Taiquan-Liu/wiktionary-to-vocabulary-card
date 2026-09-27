"""Offline Finnish word-form frequencies, with explicit unscored cases."""

import math
import unicodedata
from dataclasses import asdict, dataclass
from functools import lru_cache
from importlib.metadata import version
from typing import Mapping, Optional

from wordfreq import get_frequency_dict


@dataclass(frozen=True)
class Band:
    key: str
    folder: str
    minimum: Optional[float]


BANDS = (
    Band("very-common", "01 Very common", 5.0),
    Band("common", "02 Common", 4.0),
    Band("less-common", "03 Less common", 3.0),
    Band("rare", "04 Rare", 0.0),
    Band("unscored", "05 Unscored", None),
)
BAND_BY_KEY = {band.key: band for band in BANDS}


def normalize_word(word: str) -> str:
    return unicodedata.normalize("NFC", word).strip().casefold()


@lru_cache(maxsize=1)
def finnish_frequencies():
    return get_frequency_dict("fi", wordlist="large")


@dataclass(frozen=True)
class Frequency:
    word: str
    lookup: str
    band: str
    zipf: Optional[float]
    reason: str

    @property
    def folder(self) -> str:
        return BAND_BY_KEY[self.band].folder

    def to_dict(self):
        return {**asdict(self), "folder": self.folder}


class FrequencyClassifier:
    def __init__(self, overrides: Optional[Mapping[str, str]] = None):
        self.overrides = {}
        if overrides is not None and not isinstance(overrides, Mapping):
            raise ValueError("frequency.overrides must map words to band names")
        for word, band in (overrides or {}).items():
            if (
                not isinstance(word, str)
                or not isinstance(band, str)
                or band not in BAND_BY_KEY
            ):
                raise ValueError(
                    f"Invalid frequency override {word!r}: {band!r}; "
                    f"choose from {', '.join(BAND_BY_KEY)}"
                )
            self.overrides[normalize_word(word)] = band

    @property
    def source(self):
        return {
            "name": "wordfreq",
            "version": version("wordfreq"),
            "language": "fi",
            "wordlist": "large",
            "unit": "observed word form, not lemma or CEFR level",
            "url": "https://github.com/rspeer/wordfreq",
            "data_license": "CC BY-SA 4.0",
        }

    def classify(self, word: str) -> Frequency:
        lookup = normalize_word(word)
        score = None
        if not lookup or any(char.isspace() for char in lookup):
            reason = "phrase_or_empty"
        elif lookup.startswith("-") or lookup.endswith("-"):
            reason = "affix"
        else:
            # Exact lookup avoids wordfreq's component-based phrase estimates.
            frequency = finnish_frequencies().get(lookup)
            if frequency:
                score = round(math.log10(frequency) + 9, 2)
                reason = "observed_word_form"
            else:
                reason = "not_in_wordlist"

        band = "unscored"
        if score is not None:
            band = next(
                band.key
                for band in BANDS
                if band.minimum is not None and score >= band.minimum
            )
        if lookup in self.overrides:
            band = self.overrides[lookup]
            reason = "manual_override"
        return Frequency(word, lookup, band, score, reason)
