#!/usr/bin/env python3
"""
Script to extract article tags from Articles sections and add them to the main tag line.

This script:
1. Processes all .md files in ~/Documents/1st remote/Suomi and subdirectories
2. Finds article tags (starting with #) in the Articles section
3. Adds those tags to the main tag line on the first line
4. Removes duplicates and preserves existing tags
"""

import re
from pathlib import Path


def extract_article_tags(content):
    """
    Extract all tags (starting with #) from article lines in the Articles section.

    Args:
        content (str): File content

    Returns:
        set: Set of unique tags found in articles
    """
    article_tags = set()
    lines = content.split("\n")
    in_articles_section = False

    for line in lines:
        line = line.strip()

        # Check if we're entering Articles section
        if line == "# Articles":
            in_articles_section = True
            continue

        # Check if we're leaving Articles section (next # section)
        if in_articles_section and line.startswith("# ") and line != "# Articles":
            break

        # Extract tags from article lines
        if in_articles_section and line.startswith("- "):
            # Find all tags in the line (pattern: #tag-name or #tag_name or #tagname)
            tags = re.findall(r"#([a-zA-Z0-9_-]+)", line)
            article_tags.update(tags)

    return article_tags


def process_file(file_path):
    """
    Process a single markdown file to extract article tags and add them to the main tag line.

    Args:
        file_path (Path): Path to the markdown file

    Returns:
        tuple: (success, tags_added, error_message)
    """
    try:
        # Read the file with UTF-8 encoding
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        lines = content.split("\n")

        # Extract article tags
        article_tags = extract_article_tags(content)

        if not article_tags:
            return True, [], None

        # Find and update the main tag line (first line starting with #)
        main_tag_line_index = -1
        for i, line in enumerate(lines):
            if (
                line.strip().startswith("#")
                and not line.strip().startswith("##")
                and not line.strip().startswith("# ")
            ):
                main_tag_line_index = i
                break

        if main_tag_line_index == -1:
            return True, [], "No main tag line found"

        # Parse existing tags from the main tag line
        main_tag_line = lines[main_tag_line_index].strip()
        existing_tags = re.findall(r"#([a-zA-Z0-9_-]+)", main_tag_line)
        existing_tags_set = set(existing_tags)

        # Find new tags to add (article tags not already in main tag line)
        new_tags = article_tags - existing_tags_set

        if not new_tags:
            return True, [], None

        # Add new tags to the main tag line
        new_tag_strings = [f"#{tag}" for tag in sorted(new_tags)]
        updated_main_tag_line = main_tag_line + " " + " ".join(new_tag_strings)
        lines[main_tag_line_index] = updated_main_tag_line

        # Write back the updated content
        new_content = "\n".join(lines)

        if new_content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True, list(new_tags), None
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
    total_tags_added = 0
    total_errors = 0

    for file_path in md_files:
        try:
            relative_path = file_path.relative_to(base_dir)
            success, tags_added, error = process_file(file_path)

            if success:
                total_processed += 1
                if tags_added:
                    total_changed += 1
                    total_tags_added += len(tags_added)
                    tag_list = ", ".join(f"#{tag}" for tag in tags_added)
                    print(f"✓ {relative_path} (added: {tag_list})")
                else:
                    print(f"○ {relative_path} (no new article tags)")
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
    print(f"  Total tags added: {total_tags_added}")
    print(f"  Errors: {total_errors}")


if __name__ == "__main__":
    main()
