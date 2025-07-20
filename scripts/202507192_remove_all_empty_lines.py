#!/usr/bin/env python3
"""
Script to remove all empty lines from markdown files in the Suomi directory.

This script:
1. Processes all .md files in ~/Documents/1st remote/Suomi and subdirectories
2. Removes all empty lines (lines that are completely empty or contain only whitespace)
3. Preserves all other content and formatting
"""

from pathlib import Path


def process_file(file_path):
    """
    Process a single markdown file to remove all empty lines.

    Args:
        file_path (Path): Path to the markdown file

    Returns:
        tuple: (success, lines_removed, error_message)
    """
    try:
        # Read the file with UTF-8 encoding
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        lines = content.split("\n")

        # Remove empty lines (lines that are empty or contain only whitespace)
        non_empty_lines = []
        empty_lines_removed = 0

        for line in lines:
            if line.strip():  # Keep lines that have non-whitespace content
                non_empty_lines.append(line)
            else:
                empty_lines_removed += 1

        # Join the non-empty lines back together
        new_content = "\n".join(non_empty_lines)

        # Write back if changes were made
        if new_content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True, empty_lines_removed, None
        else:
            return True, 0, None

    except Exception as e:
        return False, 0, str(e)


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
    total_lines_removed = 0
    total_errors = 0

    for file_path in md_files:
        try:
            relative_path = file_path.relative_to(base_dir)
            success, lines_removed, error = process_file(file_path)

            if success:
                total_processed += 1
                if lines_removed > 0:
                    total_changed += 1
                    total_lines_removed += lines_removed
                    print(f"✓ {relative_path} ({lines_removed} empty lines removed)")
                else:
                    print(f"○ {relative_path} (no empty lines found)")
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
    print(f"  Total empty lines removed: {total_lines_removed}")
    print(f"  Errors: {total_errors}")


if __name__ == "__main__":
    main()
