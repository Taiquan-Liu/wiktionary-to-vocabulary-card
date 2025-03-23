from wiktionary_vocab_card.cli import generate

if __name__ == "__main__":
    # Call the click command function directly with the arguments
    # This bypasses Click's CLI exit handling
    generate.callback(url="https://en.wiktionary.org/wiki/ehdokas", output="card.md")
