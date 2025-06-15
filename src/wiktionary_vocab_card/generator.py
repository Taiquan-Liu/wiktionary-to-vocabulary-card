from itertools import zip_longest
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

import pyperclip

from .file_manager import FileManager


class MarkdownGenerator:
    def __init__(self, parser, content, config):
        self.parser = parser
        self.content = content
        self.config = config
        self.file_manager = None

        # Initialize FileManager if file management is enabled
        if self.config.get("file_management", {}).get("check_existing", True):
            self.file_manager = FileManager(config)

    def generate_tags(self):
        tags = []
        if self.content["word_types"]:
            for word_type in self.content["word_types"]:
                tags.append(f"#{word_type}")
        if self.content["kotus_types"]:
            for kotus_type in self.content["kotus_types"]:
                tags.append(f"#{kotus_type}")
        return " ".join(tags)

    def generate_table(self, conjugation):
        if not conjugation:
            return ""

        if self.config["table_folding"]:
            # Create folding section without extra newlines
            return self.generate_ad_note(
                title="Conjugation Table",
                collapse=self.config["table_folding"],
                text=conjugation,
            )

        return conjugation

    def generate_card(self, article: str = "") -> str:
        """Generate markdown card with optional article content.

        Args:
            article: Optional article content to append to the wordcard

        Returns:
            Generated markdown content
        """
        # Build the card with parts that exist
        parts = []
        parts.append(f"## {self.content['word']}")

        tags = self.generate_tags()
        if tags:
            parts.append(tags)

        parts.append(f"{self.parser.url}")

        # Support both article field (new) and custom_text (backward compatibility)
        if article:
            parts.append(f"{article}")
        elif (
            self.config.get("custom_text")
            and self.config["custom_text"] != "{custom text}"
        ):
            parts.append(f"{self.config['custom_text']}")

        for word_type, conjugation, definition in zip_longest(
            self.content["word_types"],
            self.content["conjugation_tables"],
            self.content["definitions"],
        ):
            parts.append(f"### {word_type}")
            table = self.generate_table(conjugation)
            if table:
                parts.append(table)

            definition = self.generate_ad_note(
                title="Definition",
                collapse=self.config["table_folding"],
                text=definition,
            )
            parts.append(definition)

        # Join everything with no extra newlines
        result = "".join([part + "\n" for part in parts]).strip()

        # Handle output based on configuration
        self._handle_output(result, article)

        return result

    def generate_markdown(self, article: str = "") -> str:
        """Generate markdown content with article field support.

        This method provides the main interface for generating wordcards
        with the new article field functionality.

        Args:
            article: Article content to include in the wordcard

        Returns:
            Generated markdown content
        """
        return self.generate_card(article)

    def generate_wordcard_with_file_management(
        self, article: str = ""
    ) -> Tuple[str, Optional[Path]]:
        """Generate wordcard and handle file management intelligently.

        This method integrates with FileManager for intelligent wordcard handling
        across learning stages.

        Args:
            article: Article content to append to existing wordcard

        Returns:
            Tuple of (markdown_content, file_path) where file_path is None if
            file management is disabled
        """
        if not self.file_manager:
            # File management disabled, just generate content
            content = self.generate_card(article)
            return content, None

        # Create content structure for FileManager
        new_content = self._create_content_structure()

        try:
            # Process wordcard with intelligent stage management
            final_path, was_moved = self.file_manager.process_wordcard(
                word=self.content["word"], new_content=new_content, new_article=article
            )

            # Generate the final markdown content
            markdown_content = self.generate_card(article)

            return markdown_content, final_path

        except Exception:
            # Fallback to simple generation if file management fails
            content = self.generate_card(article)
            return content, None

    def _create_content_structure(self) -> Dict[str, Any]:
        """Create content structure compatible with FileManager.

        Returns:
            Dictionary containing structured content for FileManager
        """
        # Create word sections from the parsed content
        word_sections = []

        for word_type, conjugation, definition in zip_longest(
            self.content["word_types"],
            self.content["conjugation_tables"],
            self.content["definitions"],
        ):
            section_content = []

            # Add conjugation table if present
            table = self.generate_table(conjugation)
            if table:
                section_content.extend(table.split("\n"))

            # Add definition
            if definition:
                definition_note = self.generate_ad_note(
                    title="Definition",
                    collapse=self.config["table_folding"],
                    text=definition,
                )
                section_content.extend(definition_note.split("\n"))

            word_sections.append({"type": word_type, "content": section_content})

        return {
            "word": self.content["word"],
            "tags": self.content.get("word_types", [])
            + self.content.get("kotus_types", []),
            "url": self.parser.url,
            "custom_text": self.config.get("custom_text", ""),
            "word_sections": word_sections,
            "articles": [],
        }

    def _handle_output(self, content: str, article: str = "") -> None:
        """Handle output based on configuration settings.

        Args:
            content: Generated markdown content
            article: Article content for file management
        """
        output_mode = self.config.get("output", {}).get("mode", "clipboard")

        if output_mode in ["clipboard", "both"]:
            # Copy to clipboard (existing behavior)
            pyperclip.copy(content)

        if output_mode in ["filesystem", "both"]:
            # Save to filesystem using FileManager
            if self.file_manager:
                try:
                    self.generate_wordcard_with_file_management(article)
                except Exception:
                    # Fallback to clipboard if filesystem fails
                    if output_mode == "filesystem":
                        pyperclip.copy(content)

    def generate_ad_note(self, title: str, collapse: bool, text: str):
        collapse_str = "collapse" if collapse else "open"
        return f"```ad-note\ntitle: {title}\ncollapse: {collapse_str}\n{text}\n```"
