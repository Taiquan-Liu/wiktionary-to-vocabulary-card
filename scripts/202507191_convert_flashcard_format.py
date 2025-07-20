#!/usr/bin/env python3
"""
Script to convert flashcard format in all markdown files in the Suomi directory.

This script:
1. Adds #flashcards tag to the tag line if not already present
2. Adds '?' before definition boxes (ad-note with Definition title or spoiler-block)
3. Adds '+++' after definition boxes
4. Moves Articles section to be after the wiktionary link
"""

import re
from pathlib import Path


def process_file(file_path):
    """
    Process a single markdown file to convert flashcard format.

    Args:
        file_path (Path): Path to the markdown file

    Returns:
        tuple: (success, changes_made, error_message)
    """
    try:
        # Read the file with UTF-8 encoding
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        lines = content.split("\n")

        # Track changes
        changes = []

        # 1. Add #flashcards tag to the first line with tags
        for i, line in enumerate(lines):
            if (
                line.strip().startswith("#")
                and not line.strip().startswith("##")
                and not line.strip().startswith("# ")
            ):
                # This is a tag line
                if "#flashcards" not in line:
                    lines[i] = line.rstrip() + " #flashcards"
                    changes.append("Added #flashcards tag")
                break

        # 2. Add '?' before definition boxes and '+++' after them
        new_lines = []
        in_definition_box = False

        for i, line in enumerate(lines):
            # Check if this is a definition box start
            is_definition_box_start = False

            # Check for ad-note with Definition title
            if line.strip() == "```ad-note":
                # Look ahead for title: Definition
                if i + 1 < len(lines) and "title: Definition" in lines[i + 1]:
                    is_definition_box_start = True

            # Check for spoiler-block
            elif line.strip() == "```spoiler-block":
                is_definition_box_start = True

            if is_definition_box_start:
                # Check if previous line is not already '?'
                if new_lines and new_lines[-1].strip() != "?":
                    new_lines.append("?")
                    changes.append("Added '?' before definition box")
                in_definition_box = True

            new_lines.append(line)

            # Check if this is the end of a definition box
            if in_definition_box and line.strip() == "```":
                # We've found the closing ``` for our definition box
                new_lines.append("+++")
                changes.append("Added '+++' after definition box")
                in_definition_box = False

        lines = new_lines

        # 3. Move Articles section after wiktionary link
        content = "\n".join(lines)

        # Find wiktionary link
        wiktionary_match = re.search(
            r"^(https://en\.wiktionary\.org/wiki/.+)$", content, re.MULTILINE
        )

        # Find Articles section
        articles_match = re.search(
            r"^# Articles.*?(?=^# |\Z)", content, re.MULTILINE | re.DOTALL
        )

        if wiktionary_match and articles_match:
            wiktionary_line = wiktionary_match.group(1)
            articles_section = articles_match.group(0).rstrip()

            # Remove the articles section from its current location
            content_without_articles = content.replace(articles_section, "").strip()

            # Find the position after the wiktionary link
            wiktionary_pos = content_without_articles.find(wiktionary_line)
            if wiktionary_pos != -1:
                wiktionary_end = wiktionary_pos + len(wiktionary_line)

                # Split content at wiktionary line
                before_wiktionary = content_without_articles[:wiktionary_end]
                after_wiktionary = content_without_articles[wiktionary_end:]

                # Insert articles section with proper spacing
                if not before_wiktionary.endswith("\n"):
                    before_wiktionary += "\n"

                # Add empty line before articles if not present
                if not after_wiktionary.startswith("\n"):
                    articles_with_spacing = "\n" + articles_section
                else:
                    articles_with_spacing = articles_section

                # Add empty line after articles if not present
                if not after_wiktionary.startswith("\n\n") and after_wiktionary.strip():
                    articles_with_spacing += "\n"

                content = before_wiktionary + articles_with_spacing + after_wiktionary
                changes.append("Moved Articles section after wiktionary link")

        # Write back if changes were made
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
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
                    print(f"○ {relative_path} (no changes needed)")
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
    print(f"  Changed: {total_changed}")
    print(f"  Errors: {total_errors}")


if __name__ == "__main__":
    main()
