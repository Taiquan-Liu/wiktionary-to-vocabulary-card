"""
File Management Module for Intelligent Wordcard Handling

This module implements intelligent wordcard handling across learning stages,
including file discovery, content analysis, stage management, and article
field transformation.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .config import get_all_stage_directories, is_vault_configured, load_config

logger = logging.getLogger(__name__)


class FileManager:
    """Manages wordcard files across learning stages with intelligent handling."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize FileManager with configuration.

        Args:
            config: Optional configuration dictionary. If None, loads from config file.
        """
        self.config = config or load_config()
        self.stage_directories = get_all_stage_directories()

    def find_existing_wordcard(self, word: str) -> Optional[Tuple[Path, str]]:
        """Search for existing wordcard across all stage directories.

        Args:
            word: The word to search for

        Returns:
            Tuple of (filepath, stage) if found, None otherwise
        """
        if not is_vault_configured():
            logger.warning("Vault not configured, cannot search for existing wordcards")
            return None

        # Normalize word for filename matching
        normalized_word = self._normalize_filename(word)

        # Search in order: new, memorizing, remembered
        search_order = ["new", "memorizing", "remembered"]

        for stage in search_order:
            stage_dir = self.stage_directories.get(stage)
            if not stage_dir or not stage_dir.exists():
                continue

            # Look for exact match first
            exact_match = stage_dir / f"{normalized_word}.md"
            if exact_match.exists():
                logger.info(f"Found exact match for '{word}' in {stage}: {exact_match}")
                return exact_match, stage

            # Look for case-insensitive match
            for file_path in stage_dir.glob("*.md"):
                if file_path.stem.lower() == normalized_word.lower():
                    logger.info(
                        f"Found case-insensitive match for '{word}' in {stage}: {file_path}"
                    )
                    return file_path, stage

        logger.info(f"No existing wordcard found for '{word}'")
        return None

    def parse_existing_wordcard(self, filepath: Path) -> Dict[str, Any]:
        """Extract content from existing markdown wordcard file.

        Args:
            filepath: Path to the existing wordcard file

        Returns:
            Dictionary containing parsed content with keys:
            - word: The word from the filename
            - tags: List of hashtags
            - url: Wiktionary URL
            - custom_text: Custom text section
            - word_sections: List of word type sections
            - articles: List of existing articles
        """
        try:
            content = filepath.read_text(encoding="utf-8")

            parsed = {
                "word": filepath.stem,
                "tags": [],
                "url": "",
                "custom_text": "",
                "word_sections": [],
                "articles": [],
            }

            lines = content.split("\n")
            current_section = None
            current_word_section = None
            article_section_started = False

            for line in lines:
                line = line.strip()

                # Extract hashtags
                if (
                    line.startswith("#")
                    and not line.startswith("##")
                    and not line.startswith("# ")
                ):
                    tags = re.findall(r"#(\w+)", line)
                    parsed["tags"].extend(tags)

                # Extract URL
                elif line.startswith("https://en.wiktionary.org/wiki/"):
                    parsed["url"] = line

                # Extract custom text (lines that contain {custom text} or similar)
                elif "{custom text}" in line or (
                    line
                    and not line.startswith("#")
                    and not line.startswith("```")
                    and not line.startswith("https://")
                    and not line.startswith("-")
                    and not article_section_started
                    and current_section != "word_section"
                ):
                    if line != "{custom text}":
                        parsed["custom_text"] = line

                # Detect word type sections (# verb, # noun, etc.)
                elif line.startswith("# ") and line[2:].strip() in [
                    "verb",
                    "noun",
                    "adjective",
                    "adverb",
                ]:
                    if current_word_section:
                        parsed["word_sections"].append(current_word_section)
                    current_word_section = {"type": line[2:].strip(), "content": []}
                    current_section = "word_section"

                # Detect Articles section
                elif line == "# Articles":
                    if current_word_section:
                        parsed["word_sections"].append(current_word_section)
                        current_word_section = None
                    article_section_started = True
                    current_section = "articles"

                # Collect content for current section
                elif current_section == "word_section" and current_word_section:
                    current_word_section["content"].append(line)

                elif current_section == "articles" and line.startswith("- "):
                    parsed["articles"].append(line)

            # Don't forget the last word section
            if current_word_section:
                parsed["word_sections"].append(current_word_section)

            logger.info(f"Successfully parsed wordcard: {filepath}")
            return parsed

        except Exception as e:
            logger.error(f"Error parsing wordcard {filepath}: {e}")
            return {
                "word": filepath.stem,
                "tags": [],
                "url": "",
                "custom_text": "",
                "word_sections": [],
                "articles": [],
            }

    def append_article_content(
        self, existing_content: Dict[str, Any], new_article: str
    ) -> Dict[str, Any]:
        """Merge new article content with existing wordcard content.

        Args:
            existing_content: Parsed content from existing wordcard
            new_article: New article content to append

        Returns:
            Updated content dictionary with appended article
        """
        # Handle custom_text to article field transformation
        if (
            existing_content.get("custom_text")
            and existing_content["custom_text"] != "{custom text}"
        ):
            # Convert custom_text to article format if it's not already
            custom_text = existing_content["custom_text"]
            if not custom_text.startswith("- "):
                # Transform custom_text into article format
                article_entry = f"- article - {custom_text}"
                existing_content["articles"].append(article_entry)
                existing_content["custom_text"] = (
                    ""  # Clear custom_text after conversion
                )

        # Add new article if provided
        if new_article and new_article.strip():
            if not new_article.startswith("- "):
                new_article = f"- article - {new_article}"

            # Check for duplicates before adding
            if new_article not in existing_content["articles"]:
                existing_content["articles"].append(new_article)

        logger.info(
            f"Appended article content to wordcard for '{existing_content['word']}'"
        )
        return existing_content

    def determine_target_location(
        self, word: str, existing_location: Optional[str] = None
    ) -> Tuple[Path, str]:
        """Determine target location for wordcard based on stage management rules.

        Stage Management Rules:
        1. If wordcard doesn't exist -> Create in New folder
        2. If wordcard exists in any folder (New, Memorizing, Remembered) -> Move to New folder

        Args:
            word: The word for the wordcard
            existing_location: Current stage if wordcard exists

        Returns:
            Tuple of (target_path, target_stage)
        """
        normalized_word = self._normalize_filename(word)

        if existing_location is None:
            # New wordcard -> Create in New folder
            target_stage = "new"
        else:
            # Any existing wordcard -> Move to New folder (restart learning process)
            target_stage = "new"
            if existing_location != "new":
                logger.info(
                    f"Moving wordcard '{word}' from '{existing_location}' to New"
                )

        target_dir = self.stage_directories.get(target_stage)
        if not target_dir:
            raise ValueError(f"Target stage directory not configured: {target_stage}")

        target_path = target_dir / f"{normalized_word}.md"

        logger.info(
            f"Target location for '{word}': {target_path} (stage: {target_stage})"
        )
        return target_path, target_stage

    def save_wordcard(self, content: Dict[str, Any], target_path: Path) -> bool:
        """Write wordcard content to target path with directory creation.

        Args:
            content: Wordcard content dictionary
            target_path: Target file path

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            if self.config.get("output", {}).get("create_directories", True):
                target_path.parent.mkdir(parents=True, exist_ok=True)

            # Backup existing file if configured
            if target_path.exists() and self.config.get("output", {}).get(
                "backup_existing", False
            ):
                backup_path = target_path.with_suffix(".md.bak")
                target_path.rename(backup_path)
                logger.info(f"Backed up existing file to: {backup_path}")

            # Generate markdown content
            markdown_content = self._generate_markdown_content(content)

            # Write to file
            target_path.write_text(markdown_content, encoding="utf-8")

            logger.info(f"Successfully saved wordcard to: {target_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving wordcard to {target_path}: {e}")
            return False

    def process_wordcard(
        self, word: str, new_content: Dict[str, Any], new_article: str = ""
    ) -> Tuple[Path, bool]:
        """Process a wordcard with intelligent stage management.

        This is the main entry point that orchestrates the entire workflow:
        1. Find existing wordcard
        2. Parse existing content if found
        3. Append new article content
        4. Determine target location
        5. Save wordcard

        Args:
            word: The word for the wordcard
            new_content: New wordcard content (from MarkdownGenerator)
            new_article: New article content to append

        Returns:
            Tuple of (final_path, was_moved) where was_moved indicates if file was moved between stages
        """
        if not is_vault_configured():
            raise ValueError("Vault not configured. Cannot process wordcard.")

        # Check if file management is enabled
        if not self.config.get("file_management", {}).get("check_existing", True):
            # Simple mode: just save to New folder
            target_path, _ = self.determine_target_location(word)
            success = self.save_wordcard(new_content, target_path)
            return target_path, False

        # Find existing wordcard
        existing_result = self.find_existing_wordcard(word)
        was_moved = False

        if existing_result:
            existing_path, existing_stage = existing_result

            # Parse existing content
            existing_content = self.parse_existing_wordcard(existing_path)

            # Append article content if enabled
            if self.config.get("file_management", {}).get("append_articles", True):
                existing_content = self.append_article_content(
                    existing_content, new_article
                )

            # Determine target location
            target_path, target_stage = self.determine_target_location(
                word, existing_stage
            )

            # Check if we're moving the file
            was_moved = existing_stage != "new" and target_stage == "new"

            # Merge new content with existing (preserve existing structure, add new sections)
            merged_content = self._merge_wordcard_content(existing_content, new_content)

            # Remove old file if moving
            if was_moved and target_path != existing_path:
                try:
                    existing_path.unlink()
                    logger.info(f"Removed old file: {existing_path}")
                except Exception as e:
                    logger.warning(f"Could not remove old file {existing_path}: {e}")

            # Save merged content
            success = self.save_wordcard(merged_content, target_path)

        else:
            # New wordcard
            target_path, _ = self.determine_target_location(word)

            # Add article content to new wordcard if provided
            if new_article and self.config.get("file_management", {}).get(
                "append_articles", True
            ):
                new_content = self.append_article_content(new_content, new_article)

            success = self.save_wordcard(new_content, target_path)

        if not success:
            raise RuntimeError(f"Failed to save wordcard for '{word}'")

        return target_path, was_moved

    def _normalize_filename(self, word: str) -> str:
        """Normalize word for use as filename."""
        # Remove or replace characters that are problematic in filenames
        normalized = re.sub(r'[<>:"/\\|?*]', "_", word)
        return normalized.strip()

    def _merge_wordcard_content(
        self, existing: Dict[str, Any], new: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge new wordcard content with existing content.

        Priority: existing content is preserved, new content is added only if missing.
        """
        merged = existing.copy()

        # Update URL if missing
        if not merged.get("url") and new.get("url"):
            merged["url"] = new["url"]

        # Merge tags (avoid duplicates)
        existing_tags = set(merged.get("tags", []))
        new_tags = set(new.get("tags", []))
        merged["tags"] = list(existing_tags | new_tags)

        # Merge word sections (avoid duplicates by type)
        existing_types = {
            section["type"] for section in merged.get("word_sections", [])
        }
        for new_section in new.get("word_sections", []):
            if new_section["type"] not in existing_types:
                merged["word_sections"].append(new_section)

        return merged

    def _generate_markdown_content(self, content: Dict[str, Any]) -> str:
        """Generate markdown content from content dictionary.

        This recreates the markdown format expected by the application.
        """
        parts = []

        # Empty line at start (matching existing format)
        parts.append("")

        # Tags
        if content.get("tags"):
            tag_line = " ".join(f"#{tag}" for tag in content["tags"])
            parts.append(tag_line)

        # URL
        if content.get("url"):
            parts.append(content["url"])

        # Custom text (if any)
        if content.get("custom_text") and content["custom_text"] != "{custom text}":
            parts.append(content["custom_text"])

        # Word sections
        for section in content.get("word_sections", []):
            parts.append(f"# {section['type']}")
            parts.extend(section["content"])

        # Articles section
        if content.get("articles"):
            parts.append("# Articles")
            parts.extend(content["articles"])

        return "\n".join(parts)


# Convenience functions for direct use
def find_existing_wordcard(
    word: str, config: Optional[Dict[str, Any]] = None
) -> Optional[Tuple[Path, str]]:
    """Find existing wordcard across all stage directories."""
    manager = FileManager(config)
    return manager.find_existing_wordcard(word)


def parse_existing_wordcard(filepath: Path) -> Dict[str, Any]:
    """Parse existing wordcard file content."""
    manager = FileManager()
    return manager.parse_existing_wordcard(filepath)


def append_article_content(
    existing_content: Dict[str, Any], new_article: str
) -> Dict[str, Any]:
    """Append article content to existing wordcard content."""
    manager = FileManager()
    return manager.append_article_content(existing_content, new_article)


def determine_target_location(
    word: str,
    existing_location: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Tuple[Path, str]:
    """Determine target location for wordcard based on stage management rules."""
    manager = FileManager(config)
    return manager.determine_target_location(word, existing_location)


def save_wordcard(
    content: Dict[str, Any], target_path: Path, config: Optional[Dict[str, Any]] = None
) -> bool:
    """Save wordcard content to target path."""
    manager = FileManager(config)
    return manager.save_wordcard(content, target_path)
