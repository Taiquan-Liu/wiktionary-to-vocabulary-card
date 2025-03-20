import pyperclip

class MarkdownGenerator:
    def __init__(self, parser, content, config):
        self.parser = parser
        self.content = content
        self.config = config

    def generate_tags(self):
        tags = []
        if self.content['pos']:
            tags.append(f"#{self.content['pos']}")
        if self.content['kotus']:
            tags.append(f"#{self.content['kotus']}")
        return ' '.join(tags)

    def generate_table(self):
        if not self.content['conjugation']:
            return ""

        if self.config['table_folding']:
            # Create folding section without extra newlines
            return self.generate_ad_note(
                title="Conjugation Table",
                collapse=self.config['table_folding'],
                text=self.content['conjugation']
            )

        return self.content['conjugation']

    def generate_card(self):
        # Build the card with parts that exist
        parts = []
        parts.append(f"## {self.content['word']}")

        tags = self.generate_tags()
        if tags:
            parts.append(tags)

        parts.append(f"{self.parser.url}")

        if self.config['custom_text']:
            parts.append(f"{self.config['custom_text']}")

        table = self.generate_table()
        if table:
            parts.append(table)

        definition = self.generate_ad_note(
            title="Definition",
            collapse=self.config['table_folding'],
            text=self.content['definition']
        )
        parts.append(definition)

        # Join everything with no extra newlines
        result = "".join([part + "\n" for part in parts]).strip()
        pyperclip.copy(result)
        return result

    def generate_ad_note(self, title: str, collapse: bool, text: str):
        collapse_str = "collapse" if collapse else "open"
        return f"```ad-note\ntitle: {title}\ncollapse: {collapse_str}\n{text}\n```"
