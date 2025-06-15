#!/usr/bin/env python3
"""
Integration example showing how to use the FileManager with MarkdownGenerator.

This demonstrates the complete workflow for intelligent wordcard handling.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wiktionary_vocab_card.file_manager import FileManager
from wiktionary_vocab_card.config import load_config


def create_sample_content():
    """Create sample content that would come from the parser and generator."""
    # This simulates what would come from parsing a Wiktionary page
    sample_parsed_content = {
        "word": "testword",
        "word_types": ["noun"],
        "kotus_types": ["kala"],
        "definitions": ["A test word for demonstration"],
        "conjugation_tables": [
            "| Case | Singular | Plural |\n|------|----------|--------|\n| Nominative | testword | testwords |"
        ],
    }

    # This simulates what MarkdownGenerator would create
    sample_new_content = {
        "word": "testword",
        "tags": ["noun", "kala"],
        "url": "https://en.wiktionary.org/wiki/testword",
        "custom_text": "",
        "word_sections": [
            {
                "type": "noun",
                "content": [
                    "```ad-note",
                    "title: Conjugation Table",
                    "collapse: collapse",
                    "| Case | Singular | Plural |",
                    "|------|----------|--------|",
                    "| Nominative | testword | testwords |",
                    "```",
                    "```ad-note",
                    "title: Definition",
                    "collapse: collapse",
                    "A test word for demonstration",
                    "```",
                ],
            }
        ],
        "articles": [],
    }

    return sample_new_content


def demonstrate_integration():
    """Demonstrate the complete integration workflow."""
    print("=== FileManager Integration Example ===\n")

    # Load configuration
    config = load_config()

    # Initialize file manager
    manager = FileManager(config)

    # Create sample content (this would normally come from MarkdownGenerator)
    new_content = create_sample_content()
    word = new_content["word"]

    print(f"Processing wordcard for: {word}")
    print(f"New content has {len(new_content['word_sections'])} word sections")

    # Sample article content to append
    new_article = "test article #example ([web](http://example.com), [[local]])"

    try:
        # Process the wordcard with intelligent stage management
        final_path, was_moved = manager.process_wordcard(
            word=word, new_content=new_content, new_article=new_article
        )

        print(f"✅ Wordcard processed successfully!")
        print(f"   Final location: {final_path}")
        print(f"   Was moved between stages: {was_moved}")

        # Read back the saved content to verify
        if final_path.exists():
            saved_content = final_path.read_text(encoding="utf-8")
            print(f"\n📄 Saved content preview (first 300 chars):")
            print(
                saved_content[:300] + "..."
                if len(saved_content) > 300
                else saved_content
            )

    except Exception as e:
        print(f"❌ Error processing wordcard: {e}")
        return False

    return True


def demonstrate_existing_wordcard_handling():
    """Demonstrate handling of existing wordcards."""
    print("\n=== Existing Wordcard Handling ===\n")

    config = load_config()
    manager = FileManager(config)

    # Test with an existing wordcard
    existing_word = "helleraja"

    print(f"Testing with existing word: {existing_word}")

    # Find existing wordcard
    result = manager.find_existing_wordcard(existing_word)
    if result:
        filepath, stage = result
        print(f"Found existing wordcard in {stage}: {filepath}")

        # Parse existing content
        existing_content = manager.parse_existing_wordcard(filepath)
        print(f"Existing content has {len(existing_content['articles'])} articles")

        # Create new content (simulating new Wiktionary data)
        new_content = {
            "word": existing_word,
            "tags": ["noun", "kala"],
            "url": f"https://en.wiktionary.org/wiki/{existing_word}",
            "custom_text": "",
            "word_sections": [
                {"type": "noun", "content": ["Updated conjugation table..."]}
            ],
            "articles": [],
        }

        # New article to append
        new_article = "updated article #weather ([web](http://example.com), [[local]])"

        try:
            # Process with article appending
            final_path, was_moved = manager.process_wordcard(
                word=existing_word, new_content=new_content, new_article=new_article
            )

            print(f"✅ Existing wordcard updated!")
            print(f"   Final location: {final_path}")
            print(f"   Was moved: {was_moved}")

        except Exception as e:
            print(f"❌ Error updating existing wordcard: {e}")
            return False
    else:
        print(f"No existing wordcard found for {existing_word}")

    return True


def demonstrate_stage_movement():
    """Demonstrate moving wordcards between stages."""
    print("\n=== Stage Movement Demonstration ===\n")

    config = load_config()
    manager = FileManager(config)

    # Simulate a wordcard in "remembered" stage
    word = "remembered_word_example"

    print(f"Simulating wordcard '{word}' in 'remembered' stage")

    # Determine where it should go (should move to memorizing)
    target_path, target_stage = manager.determine_target_location(word, "remembered")

    print(f"Target location: {target_stage}")
    print(f"Target path: {target_path}")

    if target_stage == "memorizing":
        print("✅ Correctly determined to move from 'remembered' to 'memorizing'")
    else:
        print("❌ Unexpected target stage")
        return False

    return True


if __name__ == "__main__":
    try:
        success = True
        success &= demonstrate_integration()
        success &= demonstrate_existing_wordcard_handling()
        success &= demonstrate_stage_movement()

        if success:
            print("\n🎉 All integration examples completed successfully!")
            print("\nThe FileManager module is ready for use with:")
            print("- Intelligent wordcard discovery across learning stages")
            print("- Content parsing and merging")
            print("- Article field transformation (custom_text -> article)")
            print("- Stage management rules (New -> Memorizing -> Remembered)")
            print("- Safe file operations with directory creation")
        else:
            print("\n❌ Some integration examples failed")

    except Exception as e:
        print(f"\n💥 Integration example failed: {e}")
        import traceback

        traceback.print_exc()
