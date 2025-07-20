#!/usr/bin/env python3
"""
Script to add word headers to vocabulary card files.

This script:
1. Processes all .md files in ~/Documents/1st remote/Suomi and subdirectories
2. Adds `# {word}` as the first line of each file
3. The word name is extracted from the filename (without .md extension)
4. Skips files that already have a word header
"""

import os
import re
from pathlib import Path


def extract_word_from_filename(file_path):
    """
    Extract the word from the filename.

    Args:
        file_path (Path): Path to the file

    Returns:
        str: The word extracted from filename
    """
    return file_path.stem


def has_word_header(lines, expected_word):
    """
    Check if the file already has a word header.

    Args:
        lines (list): List of lines from the file
        expected_word (str): The expected word for the header

    Returns:
        bool: True if file already has the correct word header
    """
    if not lines:
        return False

    first_line = lines[0].strip()
    return first_line == f"# {expected_word}"


def process_file(file_path):
    """
    Process a single markdown file to add word header.

    Args:
        file_path (Path): Path to the markdown file

    Returns:
        tuple: (success, changes_made, error_message)
    """
    try:
        # Extract word from filename
        word = extract_word_from_filename(file_path)

        # Read the file
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        lines = content.split('\n')

        # Check if file already has the correct word header
        if has_word_header(lines, word):
            return True, [], None

        # Add word header as the first line
        new_lines = [f"# {word}"] + lines
        changes = [f"Added word header: # {word}"]

        # Write back the updated content
        new_content = '\n'.join(new_lines)

        if new_content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True, changes, None
        else:
            return True, [], None

    except Exception as e:
        return False, [], str(e)


def main():
    """Main function to process all markdown files in the Suomi directory."""

    # Define the base directory
    base_dir = Path.home() / "Documents" / "1st remote" / "Suomi"

    if not base_dir.exists():
        print(f"Error: Directory {base_dir} does not exist")
        return

    # Find all markdown files
    md_files = list(base_dir.rglob("*.md"))

    if not md_files:
        print(f"No markdown files found in {base_dir}")
        return

    print(f"Found {len(md_files)} markdown files to process")
    print(f"Base directory: {base_dir}")
    print("-" * 50)

    # Process each file
    total_processed = 0
    total_changed = 0
    total_errors = 0

    for file_path in md_files:
        try:
            relative_path = file_path.relative_to(base_dir)
            success, changes, error = process_file(file_path)

            if success:
                total_processed += 1
                if changes:
                    total_changed += 1
                    print(f"✓ {relative_path}")
                    for change in changes:
                        print(f"  - {change}")
                else:
                    print(f"○ {relative_path} (already has word header)")
            else:
                total_errors += 1
                print(f"✗ {relative_path}: {error}")

        except Exception as e:
            total_errors += 1
            print(f"✗ {file_path}: Unexpected error - {e}")

    print("-" * 50)
    print(f"Summary:")
    print(f"  Total files: {len(md_files)}")
    print(f"  Processed successfully: {total_processed}")
    print(f"  Files changed: {total_changed}")
    print(f"  Errors: {total_errors}")


if __name__ == "__main__":
    main()