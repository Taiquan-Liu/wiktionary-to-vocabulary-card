class MarkdownGenerator:
    def __init__(self, content, config):
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
            return f"<details>\n<summary>Conjugation Table</summary>\n\n{self.content['conjugation']}\n</details>\n"
        return self.content['conjugation']

    def generate_card(self):
        return f"""## {self.content['word']}
{self.generate_tags()}
{self.parser.url}
{self.config['custom_text']}
{self.generate_table()}```spoiler-block
{self.content['definition']}
```"""
