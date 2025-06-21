#!/usr/bin/env python3
"""
Test script for the file management module.

This script demonstrates the intelligent wordcard handling functionality
and tests the integration with the existing configuration system.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wiktionary_vocab_card.config import is_vault_configured, load_config
from wiktionary_vocab_card.file_manager import (FileManager,
                                                find_existing_wordcard)


def test_file_manager():
    """Test the file management module functionality."""
    print("=== File Manager Test ===\n")

    # Load configuration
    config = load_config()
    print(
        f"Configuration loaded: {config.get('vault', {}).get('path', 'Not configured')}"
    )
    print(f"Vault configured: {is_vault_configured()}")
    print()

    # Initialize file manager
    manager = FileManager(config)
    print(f"Stage directories: {list(manager.stage_directories.keys())}")
    print()

    # Test finding existing wordcards
    test_words = ["helleraja", "rikkoutua", "yhteys", "nonexistent"]

    for word in test_words:
        print(f"Searching for '{word}':")
        result = manager.find_existing_wordcard(word)
        if result:
            filepath, stage = result
            print(f"  Found in {stage}: {filepath}")

            # Parse the existing wordcard
            parsed = manager.parse_existing_wordcard(filepath)
            print(f"  Tags: {parsed['tags']}")
            print(f"  URL: {parsed['url']}")
            print(f"  Custom text: {parsed['custom_text']}")
            print(f"  Word sections: {[s['type'] for s in parsed['word_sections']]}")
            print(f"  Articles: {len(parsed['articles'])} found")
        else:
            print(f"  Not found")
        print()

    # Test target location determination
    print("=== Target Location Tests ===")
    test_cases = [
        ("newword", None),  # New word
        ("existingword", "new"),  # Existing in New
        ("memorizedword", "memorizing"),  # Existing in Memorizing
        ("rememberedword", "remembered"),  # Existing in Remembered
    ]

    for word, existing_stage in test_cases:
        target_path, target_stage = manager.determine_target_location(
            word, existing_stage
        )
        print(f"Word: {word}, Current: {existing_stage} -> Target: {target_stage}")
        print(f"  Path: {target_path}")
    print()

    # Test article content appending
    print("=== Article Content Appending Test ===")
    sample_content = {
        "word": "testword",
        "tags": ["noun"],
        "url": "https://en.wiktionary.org/wiki/testword",
        "custom_text": "Some custom text",
        "word_sections": [{"type": "noun", "content": ["Sample content"]}],
        "articles": ["- article - existing article"],
    }

    new_article = "new article content #tag ([web](http://example.com), [[local]])"
    updated_content = manager.append_article_content(sample_content, new_article)

    print("Original articles:", sample_content["articles"])
    print("Updated articles:", updated_content["articles"])
    print("Custom text after conversion:", updated_content["custom_text"])
    print()

    # Test markdown generation
    print("=== Markdown Generation Test ===")
    markdown = manager._generate_markdown_content(updated_content)
    print("Generated markdown:")
    print(markdown)


def test_convenience_functions():
    """Test the convenience functions."""
    print("\n=== Convenience Functions Test ===")

    # Test find_existing_wordcard function
    result = find_existing_wordcard("helleraja")
    if result:
        filepath, stage = result
        print(f"Found helleraja in {stage}: {filepath}")
    else:
        print("helleraja not found")


if __name__ == "__main__":
    try:
        test_file_manager()
        test_convenience_functions()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
