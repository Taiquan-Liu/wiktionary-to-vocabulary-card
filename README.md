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

# Disable opening in Obsidian (enabled by default)
wikt-vocab generate https://en.wiktionary.org/wiki/ehdokas --no-open
```

**Options:**
- `-o, --output TEXT`: Output file path (overrides configuration)
- `-t, --custom-text TEXT`: Article content for the wordcard
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

# Set deprecated custom text (use -t with generate instead)
wikt-vocab configure --custom-text "My custom text"
```

**Options:**
- `--vault-path TEXT`: Set Obsidian vault path
- `--vault-name TEXT`: Set Obsidian vault name (if different from folder name)
- `--output-mode [filesystem|clipboard|both]`: Set output mode
- `--table-folding BOOLEAN`: Enable/disable table folding
- `--open-obsidian BOOLEAN`: Enable/disable opening files in Obsidian
- `--custom-text TEXT`: Set custom text for cards (deprecated)

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
