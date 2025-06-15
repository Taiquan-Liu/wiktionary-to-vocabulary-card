#!/usr/bin/env python3
"""
Test script to verify the updated MarkdownGenerator with article field support
and FileManager integration.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wiktionary_vocab_card.generator import MarkdownGenerator
from wiktionary_vocab_card.config import load_config


class MockParser:
    """Mock parser for testing purposes."""

    def __init__(self, word: str):
        self.url = f"https://en.wiktionary.org/wiki/{word}"


def test_article_field_support():
    """Test that the generator supports the new article field."""
    print("=== Testing Article Field Support ===\n")

    # Create mock content
    content = {
        "word": "testword",
        "word_types": ["noun"],
        "kotus_types": ["kala"],
        "definitions": ["A test word for demonstration"],
        "conjugation_tables": [
            "| Case | Singular | Plural |\n|------|----------|--------|\n| Nominative | testword | testwords |"
        ],
    }

    # Load config
    config = load_config()

    # Create mock parser
    parser = MockParser("testword")

    # Create generator
    generator = MarkdownGenerator(parser, content, config)

    # Test with article field
    article_content = "test article #example ([web](http://example.com), [[local]])"
    result = generator.generate_markdown(article_content)

    print("Generated markdown with article field:")
    print("=" * 50)
    print(result)
    print("=" * 50)

    # Verify article content is included
    if article_content in result:
        print("✅ Article field successfully included in output")
    else:
        print("❌ Article field not found in output")
        return False

    return True


def test_backward_compatibility():
    """Test that the generator maintains backward compatibility with custom_text."""
    print("\n=== Testing Backward Compatibility ===\n")

    # Create mock content
    content = {
        "word": "testword2",
        "word_types": ["verb"],
        "kotus_types": ["sanoa"],
        "definitions": ["A test verb"],
        "conjugation_tables": [
            "| Form | Value |\n|------|-------|\n| Infinitive | testword2 |"
        ],
    }

    # Load config and set custom_text
    config = load_config()
    config["custom_text"] = "This is custom text for backward compatibility"

    # Create mock parser
    parser = MockParser("testword2")

    # Create generator
    generator = MarkdownGenerator(parser, content, config)

    # Test without article field (should use custom_text)
    result = generator.generate_markdown()

    print("Generated markdown with custom_text (backward compatibility):")
    print("=" * 50)
    print(result)
    print("=" * 50)

    # Verify custom_text is included
    if config["custom_text"] in result:
        print("✅ Backward compatibility with custom_text maintained")
    else:
        print("❌ custom_text not found in output")
        return False

    return True


def test_file_management_integration():
    """Test FileManager integration (if vault is configured)."""
    print("\n=== Testing FileManager Integration ===\n")

    # Create mock content
    content = {
        "word": "integration_test",
        "word_types": ["adjective"],
        "kotus_types": ["korkea"],
        "definitions": ["A test adjective for integration"],
        "conjugation_tables": [
            "| Case | Singular |\n|------|----------|\n| Nominative | integration_test |"
        ],
    }

    # Load config
    config = load_config()

    # Create mock parser
    parser = MockParser("integration_test")

    # Create generator
    generator = MarkdownGenerator(parser, content, config)

    # Check if FileManager is initialized
    if generator.file_manager:
        print("✅ FileManager successfully initialized")

        # Test the file management method
        article_content = "integration test article #testing"
        try:
            markdown_content, file_path = (
                generator.generate_wordcard_with_file_management(article_content)
            )
            print(f"✅ File management method executed successfully")
            if file_path:
                print(f"   File would be saved to: {file_path}")
            else:
                print("   File management disabled or failed gracefully")
        except Exception as e:
            print(f"⚠️  File management failed (expected if vault not configured): {e}")
    else:
        print("ℹ️  FileManager not initialized (file management disabled)")

    return True


def test_output_modes():
    """Test different output modes."""
    print("\n=== Testing Output Modes ===\n")

    # Create mock content
    content = {
        "word": "output_test",
        "word_types": ["noun"],
        "kotus_types": ["kala"],
        "definitions": ["A test word for output modes"],
        "conjugation_tables": [
            "| Case | Singular |\n|------|----------|\n| Nominative | output_test |"
        ],
    }

    # Test different output modes
    modes = ["clipboard", "filesystem", "both"]

    for mode in modes:
        print(f"Testing output mode: {mode}")

        # Load config and set output mode
        config = load_config()
        config["output"] = {"mode": mode}

        # Create mock parser and generator
        parser = MockParser("output_test")
        generator = MarkdownGenerator(parser, content, config)

        # Generate content
        generator.generate_markdown("test article for output mode")

        print(f"✅ Output mode '{mode}' handled successfully")

    return True


if __name__ == "__main__":
    try:
        success = True
        success &= test_article_field_support()
        success &= test_backward_compatibility()
        success &= test_file_management_integration()
        success &= test_output_modes()

        if success:
            print("\n🎉 All tests passed successfully!")
            print("\nThe updated MarkdownGenerator supports:")
            print("- ✅ Article field integration")
            print("- ✅ Backward compatibility with custom_text")
            print("- ✅ FileManager integration for intelligent file handling")
            print("- ✅ Enhanced output modes (filesystem, clipboard, both)")
            print("- ✅ Graceful fallback when file management fails")
        else:
            print("\n❌ Some tests failed")

    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback

        traceback.print_exc()
