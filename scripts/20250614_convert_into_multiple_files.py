import os
import re
from collections import defaultdict

vault_dir = "~/Documents/1st remote/Suomi"
file_name = "Sanat.md"


def sanitize_filename(name):
    """Sanitize filename by removing invalid characters"""
    # Remove or replace invalid characters for filenames
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = name.strip()
    return name


def process_markdown_file():
    # Expand the path
    vault_path = os.path.expanduser(vault_dir)
    input_file = os.path.join(vault_path, file_name)
    output_dir = os.path.join(vault_path, "New")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Read the input file
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by ## headings
    sections = re.split(r"^## (.+)$", content, flags=re.MULTILINE)

    # The first element is content before the first ## heading (if any)
    # Skip it if it's just whitespace
    if sections[0].strip():
        print("Warning: Content found before first ## heading:")
        print(sections[0][:200] + "..." if len(sections[0]) > 200 else sections[0])

    # Process sections in pairs (heading, content)
    headings_content = {}
    duplicate_headings = defaultdict(list)

    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            heading = sections[i].strip()
            content = sections[i + 1]

            # Track duplicates
            if heading in headings_content:
                duplicate_headings[heading].append(content)
                if len(duplicate_headings[heading]) == 1:
                    # First duplicate found, add the original content
                    duplicate_headings[heading].insert(0, headings_content[heading])
            else:
                headings_content[heading] = content

    # Handle duplicates - show content and ask user to choose
    if duplicate_headings:
        print("\nDuplicate headings found:")
        for heading, contents in duplicate_headings.items():
            print(f"\n{'='*50}")
            print(f"DUPLICATE HEADING: {heading}")
            print(f"Found {len(contents)} instances:")

            for idx, content in enumerate(contents, 1):
                print(f"\n--- Instance {idx} ---")
                # Show first 300 characters of content
                preview = content[:300].strip()
                if len(content) > 300:
                    preview += "..."
                print(preview)

            print(f"\n{'='*50}")

        print("\nPlease review the duplicate headings above.")
        print("The script will continue and create files for unique headings only.")
        print("You'll need to manually handle the duplicates.")

    # Create files for unique headings
    created_files = []
    for heading, content in headings_content.items():
        if heading not in duplicate_headings:
            # Sanitize filename
            filename = sanitize_filename(heading) + ".md"
            filepath = os.path.join(output_dir, filename)

            # Adjust subheadings (### becomes #, #### becomes ##, etc.)
            adjusted_content = re.sub(r"^###", "#", content, flags=re.MULTILINE)
            adjusted_content = re.sub(
                r"^####", "##", adjusted_content, flags=re.MULTILINE
            )
            adjusted_content = re.sub(
                r"^#####", "###", adjusted_content, flags=re.MULTILINE
            )
            adjusted_content = re.sub(
                r"^######", "####", adjusted_content, flags=re.MULTILINE
            )

            # Add the heading as the main title
            file_content = f"{adjusted_content}"

            # Write the file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(file_content)

            created_files.append(filename)

    print(f"\nProcessing complete!")
    print(f"Created {len(created_files)} files in {output_dir}")
    print(f"Files created: {', '.join(sorted(created_files))}")

    if duplicate_headings:
        print(
            f"\nWarning: {len(duplicate_headings)} duplicate headings were not processed:"
        )
        for heading in duplicate_headings.keys():
            print(f"  - {heading}")


if __name__ == "__main__":
    process_markdown_file()
