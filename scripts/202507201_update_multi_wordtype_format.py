#!/usr/bin/env python3
"""
Script to update format for vocabulary cards with multiple word types.

This script:
1. Processes all .md files in ~/Documents/1st remote/Suomi and subdirectories
2. For files with multiple word type sections (# noun, # verb, etc.):
   - Removes individual ? and +++ around definition boxes
   - Adds ?? before the first word type section
   - Adds +++ after the last definition box
3. Leaves files without word type sections unchanged
"""

from pathlib import Path


def identify_word_type_sections(lines):
    """
    Identify word type sections in the content.

    Args:
        lines (list): List of lines from the file

    Returns:
        list: List of tuples (line_index, word_type) for word type sections
    """
    word_types = [
        "Noun",
        "Verb",
        "Adjective",
        "Adverb",
        "Pronoun",
        "Participle",
        "Preposition",
        "Postposition",
        "Conjunction",
        "Phrase",
        "Prefix",
        "Numeral",
        "Particle",
    ]

    word_type_sections = []

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith("# ") and not line.startswith("## "):
            word_type: str = line[2:].strip().lower()
            if word_type.capitalize() in word_types:
                word_type_sections.append((i, word_type))

    return word_type_sections


def find_definition_boxes(lines, start_index, end_index):
    """
    Find definition box ranges within a section.

    Args:
        lines (list): List of lines from the file
        start_index (int): Start searching from this line
        end_index (int): Stop searching at this line

    Returns:
        list: List of tuples (start_line, end_line) for definition boxes
    """
    definition_boxes = []
    i = start_index

    while i < end_index:
        line = lines[i].strip()

        # Check for ad-note definition box
        if line == "```ad-note":
            # Look ahead for title: Definition
            if i + 1 < len(lines) and "title: Definition" in lines[i + 1]:
                # Find the closing ```
                j = i + 2
                while j < end_index and lines[j].strip() != "```":
                    j += 1
                if j < end_index:
                    definition_boxes.append((i, j))
                    i = j + 1
                    continue

        # Check for spoiler-block definition box
        elif line == "```spoiler-block":
            # Find the closing ```
            j = i + 1
            while j < end_index and lines[j].strip() != "```":
                j += 1
            if j < end_index:
                definition_boxes.append((i, j))
                i = j + 1
                continue

        i += 1

    return definition_boxes


def process_file(file_path):
    """
    Process a single markdown file to update multi-word-type format.

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

        # Identify word type sections
        word_type_sections = identify_word_type_sections(lines)

        # Only process files with word type sections
        if word_type_sections == []:
            return True, [], None

        changes = []
        new_lines = []
        i = 0

        # Process lines up to first word type section
        first_word_type_index = word_type_sections[0][0]
        while i < first_word_type_index:
            new_lines.append(lines[i])
            i += 1

        # Add ?? before first word type
        new_lines.append("??")
        changes.append("Added ?? before first word type section")

        # Process each word type section
        for section_idx, (word_type_start, word_type) in enumerate(word_type_sections):
            # Add the word type section line
            new_lines.append(lines[word_type_start])
            i = word_type_start + 1

            # Determine the end of this section
            if section_idx + 1 < len(word_type_sections):
                section_end = word_type_sections[section_idx + 1][0]
            else:
                # Last section - find end by looking for next # section or end of file
                section_end = len(lines)
                for j in range(word_type_start + 1, len(lines)):
                    if lines[j].strip().startswith("# ") and not lines[
                        j
                    ].strip().startswith("## "):
                        section_end = j
                        break

            # Find definition boxes in this section
            find_definition_boxes(lines, i, section_end)

            # Process lines in this section, removing ? and +++ around definition boxes
            while i < section_end:
                line = lines[i].strip()

                # Skip standalone ? lines
                if line == "?" or line == "??":
                    changes.append(f"Removed standalone ? from {word_type} section")
                    i += 1
                    continue

                # Skip standalone +++ lines
                if line == "+++":
                    changes.append(f"Removed standalone +++ from {word_type} section")
                    i += 1
                    continue

                # Add the line
                new_lines.append(lines[i])
                i += 1

        # Add remaining lines after last word type section
        while i < len(lines):
            line = lines[i].strip()

            # Skip standalone +++ lines at the end
            if line == "+++":
                changes.append("Removed standalone +++ at end")
                i += 1
                continue

            new_lines.append(lines[i])
            i += 1

        # Add +++ at the end
        new_lines.append("+++")
        changes.append("Added +++ after last definition box")

        # Write back if changes were made
        new_content = "\n".join(new_lines)

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
                    print(f"○ {relative_path} (single word type or no changes needed)")
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
