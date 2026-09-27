A tool to generate Obsidian markdown vocabulary cards from Wiktionary pages.

## Installation

Install the package:

```bash
poetry install
```

## Usage

The `wikt-vocab` CLI provides `generate`, `configure`, `status`, `classify`, and `reorganize`.

## Finnish frequency decks

Frequency decks are the default organization. They help you spend more review time on words you are likely to meet again. The tool uses the free, offline Finnish data bundled with [wordfreq](https://github.com/rspeer/wordfreq). Spaced Repetition still controls review intervals.

| Folder | Zipf score | Approximate occurrences per million words |
| --- | --- | --- |
| `01 Very common` | 5 and above | 100 and above |
| `02 Common` | 4 to below 5 | 10 to below 100 |
| `03 Less common` | 3 to below 4 | 1 to below 10 |
| `04 Rare` | Below 3, when listed | Below 1 |
| `05 Unscored` | No score | Missing words, phrases, affixes and unsupported spellings |

These are observed word-form frequencies, not A1 through C2 levels. Finnish inflections spread a word's usage across spellings. Phrases and hyphenated compounds are not assigned estimated scores from their component words. An unscored word can still be useful. See [docs/finnish-frequency-sources.md](docs/finnish-frequency-sources.md) for source comparisons, licenses and limitations.

```bash
poetry run wikt-vocab classify olla ehdokas arvonlisävero helleraja "saada aikaan"
poetry run wikt-vocab classify --json ehdokas
```

### Try a sorted copy

Create a separate test vault so the original and copied cards do not share review queues. The destination vocabulary folder must not exist. `reorganize` never modifies the source or the CLI configuration.

```bash
poetry run wikt-vocab reorganize "/path/to/live-vault/Suomi" "/path/to/test-vault/Suomi" --dry-run
poetry run wikt-vocab reorganize "/path/to/live-vault/Suomi" "/path/to/test-vault/Suomi"

# A separate configuration keeps test imports in the test vault.
poetry run wikt-vocab --config .scratch/preview.yaml configure \
  --vault-path "/path/to/test-vault/Suomi" \
  --vault-name "test-vault" --organization frequency --open-obsidian false
poetry run wikt-vocab --config .scratch/preview.yaml generate \
  https://en.wiktionary.org/wiki/ehdokas -t "My article reference" --no-open
```

Open the test vault in Obsidian. Enable Spaced Repetition's **Convert folders to decks** option and retain your existing card separators. This project's cards use `??` for a reversed multiline card and `+++` for its end. Copy the relevant plugin settings or set these options in the test vault.

The copy includes every source file. Vocabulary cards are identified by their standalone Wiktionary URL or a `#flashcards` tag; other files retain their relative paths. Cards keep their exact bytes, including scheduling comments, frontmatter, tags, definitions, article links and filenames. Duplicate filenames keep both versions under `Duplicates/<original path>` in the destination deck. The CLI refuses a later import when multiple notes represent the same word.

The generated `Suomi/Frequency report.md` lists scores, unscored reasons and duplicates. `Suomi/.frequency-manifest.json` records all source/destination paths, SHA-256 hashes, thresholds, overrides and the package version. Both paths are relative to the test vault root. Relative or folder-specific links may need updating after a move; the copy preserves their text. Article notes outside the copied tree need to be copied separately if you want those links to open in the test vault.

### Use the decks

Start reviews in `01 Very common` and `02 Common` when time is limited. Study the lower-frequency decks for vocabulary relevant to your reading or work, and inspect `05 Unscored` manually.

New imports enter the matching frequency folder. Importing an existing word appends its new article reference and preserves the note, schedule and current folder. It does not refresh definitions from Wiktionary. You can move a card to another priority folder in Obsidian, and repeat imports will keep that choice.

Set the vocabulary folder inside your synced vault once, then use the usual command without a preview configuration:

```bash
poetry run wikt-vocab configure --vault-path "/path/to/1st remote/Suomi" --vault-name "1st remote"
poetry run wikt-vocab generate https://en.wiktionary.org/wiki/ehdokas
```

The vocabulary folders and the plugin's scheduling comments live in the same vault, so they can sync with your other notes. Use **Convert folders to decks** on each device. Changing the default does not automatically reorganize existing files; `reorganize` still creates a separate copy for inspection before replacement.

To retain a priority choice across future reorganizations or new imports, add an override to the selected configuration:

```yaml
frequency:
  overrides:
    helleraja: common
    saada aikaan: very-common
```

Allowed override values are `very-common`, `common`, `less-common`, `rare`, and `unscored`. They choose the deck without changing the measured score. `--config PATH` selects a configuration for one command; `WIKT_VOCAB_CONFIG` can select it for a shell session. Configurations without an organization setting use frequency decks. The legacy layout remains available through `configure --organization stages`.

Run the isolated regression tests with `poetry run pytest tests -q`. These tests use temporary vaults and saved Wiktionary HTML. The older root-level demonstration scripts can access a configured vault; do not run them against your live learning data.

### Generate Command

Generate vocabulary cards from Wiktionary URLs:

```bash
# Basic usage
wikt-vocab generate https://en.wiktionary.org/wiki/ehdokas

# Save to specific file
wikt-vocab generate https://en.wiktionary.org/wiki/ehdokas -o card.md

# Add custom article content
wikt-vocab generate https://en.wiktionary.org/wiki/ehdokas -t "My custom article content"

# Combine output file and custom text
wikt-vocab generate https://en.wiktionary.org/wiki/ehdokas -o /path/to/card.md -t "Custom content"

# Disable opening in Obsidian (enabled by default)
wikt-vocab generate https://en.wiktionary.org/wiki/ehdokas --no-open
```

**Options:**
- `-o, --output TEXT`: Output file path (overrides configuration)
- `-t, --custom-text TEXT`: Article content to add to the wordcard's articles section
- `--no-open`: Don't open the generated file in Obsidian (opening is enabled by default)

**Behavior:**
- Uses intelligent file management when Obsidian vault is configured
- Falls back to file output or clipboard based on configuration
- Creates output directories automatically if they don't exist
- **Automatically opens generated files in Obsidian when vault is configured** (can be disabled with `--no-open`)

### Configure Command

Configure vault path, output modes, and other settings:

```bash
# Set Obsidian vault path
wikt-vocab configure --vault-path /path/to/obsidian/vault

# Set Obsidian vault name (if different from folder name)
wikt-vocab configure --vault-name "1st remote"

# Set output mode
wikt-vocab configure --output-mode filesystem
wikt-vocab configure --output-mode clipboard
wikt-vocab configure --output-mode both

# Enable/disable table folding
wikt-vocab configure --table-folding true
wikt-vocab configure --table-folding false

# Enable/disable opening files in Obsidian
wikt-vocab configure --open-obsidian true
wikt-vocab configure --open-obsidian false

# Set default custom text (used when no -t option is provided)
wikt-vocab configure --custom-text "My default custom text"
```

**Options:**
- `--vault-path TEXT`: Set Obsidian vault path
- `--vault-name TEXT`: Set Obsidian vault name (if different from folder name)
- `--organization [frequency|stages]`: Choose frequency decks or the legacy learning-stage layout
- `--output-mode [filesystem|clipboard|both]`: Set output mode
- `--table-folding BOOLEAN`: Enable/disable table folding
- `--open-obsidian BOOLEAN`: Enable/disable opening files in Obsidian
- `--custom-text TEXT`: Set default custom text for cards (used when no -t option is provided)

### Status Command

Show current configuration and vault status:

```bash
wikt-vocab status
```

This displays:
- Vault path, name, and accessibility status
- Current output mode
- Obsidian opening setting
- File management settings
- Table folding setting
- Default output location

## Output Modes

1. **Filesystem**: Saves cards to files
2. **Clipboard**: Copies cards to clipboard
3. **Both**: Saves to files and copies to clipboard

## Obsidian Integration

When an Obsidian vault is configured, the tool integrates seamlessly:
- **Automatically opens generated files in Obsidian** using the `obsidian://` URI scheme
- Supports custom vault names and file paths
- Works with all output modes (filesystem, clipboard, both)
- Can be disabled with `--no-open` flag or configuration

## File Management

When an Obsidian vault is configured, the tool provides intelligent file management:
- Checks for existing files
- Appends articles to existing cards
- Preserves existing cards' folders, handwritten edits, and review schedules in the default frequency organization
- Handles duplicate content intelligently

## Debug

Run `debug.py` to debug the app. You can select the word to debug by:
- Passing the word as an argument
- Set `WIKT_DEBUG_WORD` environment variable
- Use the selection prompt

## Examples

New examples can be added by running the following commands:

```bash
# Generate example
make add-word URL=https://en.wiktionary.org/wiki/saada
```

```bash
# Regenerate all examples
make regenerate-examples
```

## Use the vocabulary cards
There are a couple of Obsidian community plugins needed for the Vocabulary card to work:
- Spaced Repetition: This is the main interface to the cards. You need to choose the difficulty level everytime a card is shown, and the level will be used to calculate the repetition intervals of the card.
- Spoiler Block: This is the syntax we use to "fold" the conjugation and description of a word.
