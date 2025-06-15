from pathlib import Path


def process_file(file_path):
    """
    Process a single markdown file to extract article lines and reorganize them.

    Args:
        file_path (Path): Path to the markdown file

    Returns:
        tuple: (success, article_count, error_message)
    """
    try:
        # Read the file with UTF-8 encoding
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Find and extract article lines
        article_lines = []
        remaining_lines = []

        for line in lines:
            if line.strip().startswith("article -"):
                article_lines.append(line.strip())
            else:
                remaining_lines.append(line)

        # Build the new content
        new_content = []

        # Add the original content (without article lines)
        new_content.extend(remaining_lines)

        # Add Articles section
        new_content.append("\n# Articles\n")

        if article_lines:
            # Add each article line as a list item
            for article_line in article_lines:
                new_content.append(f"- {article_line}\n")
        else:
            # Add empty line if no articles found
            new_content.append("\n")

        # Write the modified content back to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_content)

        return True, len(article_lines), None

    except Exception as e:
        return False, 0, str(e)


def main():
    """Main function to process all markdown files in the target directory."""
    target_dir = Path("/Users/taiquanliu/Documents/1st remote/Suomi/New")

    if not target_dir.exists():
        print(f"Error: Directory {target_dir} does not exist.")
        return

    # Get all .md files in the directory
    md_files = list(target_dir.glob("*.md"))

    if not md_files:
        print(f"No markdown files found in {target_dir}")
        return

    print(f"Processing {len(md_files)} markdown files in {target_dir}")
    print("-" * 60)

    total_processed = 0
    total_articles_moved = 0
    errors = []

    for file_path in sorted(md_files):
        success, article_count, error_msg = process_file(file_path)

        if success:
            total_processed += 1
            total_articles_moved += article_count
            status = f"✓ {file_path.name}: {article_count} article(s) moved"
            print(status)
        else:
            errors.append(f"✗ {file_path.name}: {error_msg}")
            print(f"✗ {file_path.name}: Error - {error_msg}")

    print("-" * 60)
    print(f"Processing complete!")
    print(f"Files processed successfully: {total_processed}")
    print(f"Total article lines moved: {total_articles_moved}")

    if errors:
        print(f"Errors encountered: {len(errors)}")
        for error in errors:
            print(f"  {error}")
    else:
        print("No errors encountered.")


if __name__ == "__main__":
    main()
