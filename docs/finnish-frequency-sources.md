# Finnish frequency sources and review priorities

Research checked on 2026-09-27.

Use frequency bands to help choose what to study first. Keep a separate override for words that matter to the learner. A low-frequency word needed at work can be more useful than a common word that is already familiar. Frequency should choose the deck; the spaced repetition plugin should continue to choose the review interval.

## Recommended first source

`wordfreq` is the simplest offline option for this Python CLI. It includes a large Finnish list assembled from six source domains, including subtitles, news and web text. Its code uses Apache 2.0 and its bundled data uses CC BY-SA 4.0. Depend on the original package and preserve its attribution rather than extracting a separate uncredited word list. The author explicitly discourages stripped CSV conversions. [Package documentation](https://github.com/rspeer/wordfreq/blob/master/README.md), [code license](https://github.com/rspeer/wordfreq/blob/master/LICENSE.txt).

Pin the package version and use the Finnish `large` wordlist. This feature reads exact entries from `get_frequency_dict("fi", wordlist="large")` and converts the frequency to Zipf with `log10(frequency) + 9`. That avoids estimates assembled from the components of phrases or hyphenated words. The installed package reads bundled files, so frequency lookup needs no web service. Record the version, lookup text and score in migration metadata. The data counts normalized tokens, with no Finnish lemmatization step. Therefore a dictionary headword's score measures that spelling, not all its inflections combined. [Lookup implementation](https://github.com/rspeer/wordfreq/blob/master/wordfreq/__init__.py).

The data describes usage through about 2021 and will not receive corpus updates. It will miss newer vocabulary. [Maintainer's data-freeze explanation](https://github.com/rspeer/wordfreq/blob/master/SUNSET.md).

## Other sources considered

| Source | What it offers | Suitability here |
| --- | --- | --- |
| [Kotus Parole frequency list](https://www.kielipankki.fi/lexical-conceptual-resources/parole-taajuuslista/) | Downloadable counts from 17 million written Finnish tokens. Entries are word forms, not combined lemmas. | Useful comparison, but does not solve the inflection problem. The catalogue links a license record; that record and the download site returned HTTP 403 during this check, so redistribution terms were not verified. |
| [LASTU](https://github.com/dustedmtl/lastu) | Finnish lemma, form, morphology and frequency information derived from the Finnish Internet Parsebank. | The strongest academic candidate for a later lemma-aware provider. Its authors provide SQLite databases and CSV exports. [Download instructions](https://github.com/dustedmtl/lastu/blob/main/docs/USERGUIDE.md). |
| [LASTU dataset releases](https://osf.io/7hrbv/) | Dataset description explicitly states CC BY-SA 4.0. Two downloadable archives currently occupy about 2.2 GB and 3.8 GB. | A large download for a vocabulary CLI. A deliberately prepared, attributed lemma subset would need its own build and validation work. Sizes and license checked through the [dataset API](https://api.osf.io/v2/nodes/7hrbv/) and [file listing](https://api.osf.io/v2/nodes/7hrbv/files/osfstorage/). |
| [Yle Uutisten taajuussanakirja](https://github.com/danradice/yle-uutiset-taajuussanakirja) | Community-built lemma frequencies for 87,870 attested Kotus headword entries in Yle news from 2011 through 2024, with build scripts and CC BY 4.0 attribution. | Compact and relevant to reading news. It is a promising optional provider, but news topics and automated lemma errors can skew general learning priorities. The maintainer documents manual homonym corrections and tagging limitations. |

SUBTLEX is a family of subtitle frequency resources, not a verified Finnish CEFR list. The SUBTLEX datasets named by `wordfreq` cover other languages; Finnish does receive subtitle data within its broader source mixture. I did not verify a separately maintained Finnish SUBTLEX release. Reusing the packaged mixture avoids inventing such a dependency. [Source and attribution details](https://github.com/rspeer/wordfreq/blob/master/README.md#sources-and-supported-languages).

## Why these are not A1 through C2 decks

CEFR defines language proficiency. The Council of Europe explains that language-specific reference descriptions require separate work by national teams. A rank or occurrence count alone does not establish a word's CEFR level. [Council of Europe reference level descriptions](https://www.coe.int/en/web/common-european-framework-reference-languages/reference-level-descriptions).

CEFRLex publishes research-based, downloadable graded lexicons, but its listed languages do not include Finnish. I did not find a comprehensive, openly licensed Finnish A1 through C2 word database with a documented validation method. This is a research limitation, not proof that none exists. Keep any future validated CEFR annotation separate from the frequency score. [CEFRLex language coverage and methodology](https://cental.uclouvain.be/cefrlex/).

## Suggested bands and uncertain cases

These thresholds are product choices, not official learning levels. Zipf is the base-10 logarithm of occurrences per billion tokens. The rates below follow directly from that definition. [Zipf conversion in the package](https://github.com/rspeer/wordfreq/blob/master/wordfreq/__init__.py).

| Priority folder | Zipf score | Estimated rate |
| --- | --- | --- |
| `01 Very common` | At least 5 | At least 100 occurrences per million tokens |
| `02 Common` | At least 4 and below 5 | 10 to under 100 per million |
| `03 Less common` | At least 3 and below 4 | 1 to under 10 per million |
| `04 Rare` | Positive and below 3 | Under 1 per million |
| `05 Unscored` | Missing, unsupported or unsuitable lookup | No defensible estimate |

`wordfreq` returns zero when an item is absent from its list. Multiword input uses an estimate derived from its component words and can overestimate unusual phrases. Treat these cases as unknown or needing manual review. Do not infer that every unknown is rare. [Lookup behavior](https://github.com/rspeer/wordfreq/blob/master/README.md#usage), [tokenization caveat](https://github.com/rspeer/wordfreq/blob/master/README.md#tokenization).

Keep the Wiktionary entry text intact. Prefer its dictionary headword when identified, and store the exact lookup term so the classification can be explained. A surface-form score can understate familiar Finnish verbs and nouns whose usage spreads across many inflections. An explicit user override is useful for this limitation as well as personal priorities.

## Obsidian migration requirements

The Spaced Repetition plugin supports hierarchical tag decks and, as an alternative setting, decks derived from folder paths. Moving cards into new folders changes the review hierarchy only when folder mode is enabled. With tag mode, existing deck tags still determine the decks. [Official deck documentation](https://stephenmwangi.com/obsidian-spaced-repetition/flashcards/decks/).

The documented storage model keeps individual flashcard schedules in `<!--SR:...-->` comments and whole-note schedules in frontmatter fields such as `sr-due`, `sr-interval` and `sr-ease`. Plugin options live in the plugin's configuration data. Preserve all existing scheduling text, card delimiters and card content when making the copy. [Official data storage documentation](https://stephenmwangi.com/obsidian-spaced-repetition/data-storage/).

A separate test vault is preferable to a duplicate card tree inside the active vault. In the active vault, both copies can become reviewable and duplicate basenames can make wikilinks ambiguous. Copy relevant plugin settings into the test vault, select folder decks there, and leave the original vault and its settings untouched until the learner approves replacement. Verify byte-preserved card bodies and schedule comments, and keep a source-to-destination manifest for the eventual move.
