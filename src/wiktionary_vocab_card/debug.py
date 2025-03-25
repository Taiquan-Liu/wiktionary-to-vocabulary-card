import json
import os
import sys
from pathlib import Path

from wiktionary_vocab_card.cli import generate


def get_examples():
    """Load examples from examples.json file"""
    examples_path = Path("examples/examples.json")
    if examples_path.exists():
        with open(examples_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def debug_word(word=None):
    """Debug a specific word or choose from available examples"""
    examples = get_examples()

    # 1. Check if word is provided via command line argument
    if len(sys.argv) > 1:
        word = sys.argv[1]

    # 2. Check if word is provided via environment variable
    if not word:
        word = os.environ.get("WIKT_DEBUG_WORD", "ehdokas")

    # 3. If not provided or invalid, show menu to choose from examples
    if not word or word not in examples:
        if not examples:
            print("No examples found. Please add some with 'make add-word URL=...'")
            return

        print("Choose a word to debug:")
        for idx, (word_key, url) in enumerate(examples.items(), 1):
            print(f"{idx}. {word_key}")

        choice = input("\nEnter number (or word): ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(examples):
            word = list(examples.keys())[int(choice) - 1]
        elif choice in examples:
            word = choice
        else:
            print(f"Invalid choice: {choice}")
            return

    # Debug the selected word
    url = examples.get(word)
    if not url:
        print(f"URL for '{word}' not found in examples.json")
        return

    print(f"Debugging word: {word} ({url})")
    # Call the click command function directly with the arguments
    # This bypasses Click's CLI exit handling
    generate.callback(url=url, output=f"examples/{word}.md")


if __name__ == "__main__":
    debug_word()
