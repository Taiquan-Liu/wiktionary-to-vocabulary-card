A tool to generate Obsidian markdown vocabulary cards from Wiktionary pages.

Usage:

Install the package:

```bash
pip install .
```

Command-line usage:

```bash
# Generate card
wikt-vocab generate https://en.wiktionary.org/wiki/ehdokas -o card.md

# Configure custom text
wikt-vocab configure --custom-text "My custom text"
```
