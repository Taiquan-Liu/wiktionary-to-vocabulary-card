from itertools import zip_longest

import pyperclip


class MarkdownGenerator:
    def __init__(self, parser, content, config):
        self.parser = parser
        self.content = content
        self.config = config

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

    def generate_card(self):
        # Build the card with parts that exist
        parts = []
        parts.append(f"## {self.content['word']}")

        tags = self.generate_tags()
        if tags:
            parts.append(tags)

        parts.append(f"{self.parser.url}")

        if self.config["custom_text"]:
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
        pyperclip.copy(result)
        return result

    def generate_ad_note(self, title: str, collapse: bool, text: str):
        collapse_str = "collapse" if collapse else "open"
        return f"```ad-note\ntitle: {title}\ncollapse: {collapse_str}\n{text}\n```"
