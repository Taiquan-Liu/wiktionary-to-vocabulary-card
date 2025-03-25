A tool to generate Obsidian markdown vocabulary cards from Wiktionary pages.

Usage:

Install the package:

```bash
poetry install
```

Command-line usage:

```bash
# Generate card
wikt-vocab generate https://en.wiktionary.org/wiki/ehdokas -o card.md

# Configure custom text
wikt-vocab configure --custom-text "My custom text"
```

Debug:
Run `debug.py` to debug the app. You can select the word to debug by:
- Passing the word as an argument
- Set `WIKT_DEBUG_WORD` environment variable
- Use the selection prompt

New examples can be added by running the following commands:

```bash
# Generate example
make add-word URL=https://en.wiktionary.org/wiki/saada
```

```bash
# Regenerate all examples
make regenerate-examples
```
