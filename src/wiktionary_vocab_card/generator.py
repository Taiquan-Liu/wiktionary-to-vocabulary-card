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
            return "<details><summary>Conjugation Table</summary>" + self.content['conjugation'] + "</details>"
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

        parts.append(f"```spoiler-block\n{self.content['definition']}\n```")

        # Join everything with no extra newlines
        result = "".join([part + "\n" for part in parts]).strip()
        pyperclip.copy(result)
        return result
