A tool to generate Obsidian markdown vocabulary cards from Wiktionary pages.

## Installation

Install the package:

```bash
poetry install
```

## Usage

The `wikt-vocab` CLI provides three main commands: `generate`, `configure`, and `status`.

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
```

**Options:**
- `-o, --output TEXT`: Output file path (overrides configuration)
- `-t, --custom-text TEXT`: Article content for the wordcard

**Behavior:**
- Uses intelligent file management when Obsidian vault is configured
- Falls back to file output or clipboard based on configuration
- Creates output directories automatically if they don't exist

### Configure Command

Configure vault path, output modes, and other settings:

```bash
# Set Obsidian vault path
wikt-vocab configure --vault-path /path/to/obsidian/vault

# Set output mode
wikt-vocab configure --output-mode filesystem
wikt-vocab configure --output-mode clipboard
wikt-vocab configure --output-mode both

# Enable/disable table folding
wikt-vocab configure --table-folding true
wikt-vocab configure --table-folding false

# Set deprecated custom text (use -t with generate instead)
wikt-vocab configure --custom-text "My custom text"
```

**Options:**
- `--vault-path TEXT`: Set Obsidian vault path
- `--output-mode [filesystem|clipboard|both]`: Set output mode
- `--table-folding BOOLEAN`: Enable/disable table folding
- `--custom-text TEXT`: Set custom text for cards (deprecated)

### Status Command

Show current configuration and vault status:

```bash
wikt-vocab status
```

This displays:
- Vault path and accessibility status
- Current output mode
- File management settings
- Table folding setting
- Default output location

## Output Modes

1. **Filesystem**: Saves cards to files
2. **Clipboard**: Copies cards to clipboard
3. **Both**: Saves to files and copies to clipboard

## File Management

When an Obsidian vault is configured, the tool provides intelligent file management:
- Checks for existing files
- Appends articles to existing cards
- Moves files from "remembered" locations
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
