import json
import subprocess
import urllib.parse
from pathlib import Path
from typing import Optional


def add_word(word, url):
    with open("./examples/examples.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    data[word] = url
    with open("./examples/examples.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        print("Added to examples.json")


def generate_all_examples():
    with open("./examples/examples.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    for word, url in data.items():
        print(f"Regenerating {word}...")
        cmd = [
            "wikt-vocab",
            "generate",
            url,
            "-o",
            f"examples/{word}.md",
            "-t",
            "examples",
        ]
        subprocess.run(cmd, check=True)
        print(f"✓ examples/{word}.md")


def open_in_obsidian(
    file_path: Path, vault_path: Path, vault_name: Optional[str] = None
) -> bool:
    """Open a file in Obsidian using the obsidian:// URI scheme.

    Args:
        file_path: Path to the file to open
        vault_path: Path to the Obsidian vault
        vault_name: Name of the vault (if None, will extract from vault_path)

    Returns:
        True if the command was executed successfully, False otherwise
    """
    try:
        # Get vault name from path if not provided
        if vault_name is None:
            vault_name = vault_path.name

        # Get relative path from vault to file
        relative_path = file_path.relative_to(vault_path)

        # URL encode the vault name and file path
        vault_encoded = urllib.parse.quote(vault_name)
        file_encoded = urllib.parse.quote(str(relative_path))

        # Construct the Obsidian URI
        obsidian_uri = f"obsidian://open?vault={vault_encoded}&file={file_encoded}"

        # Open the URI using the system's default handler
        subprocess.run(["open", obsidian_uri], check=True)

        return True

    except Exception as e:
        print(f"Error opening file in Obsidian: {e}")
        return False
