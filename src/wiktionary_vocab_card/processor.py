class TableProcessor:
    @staticmethod
    def html_to_markdown(table):
        # Table conversion implementation
        pass


class ContentProcessor:
    def __init__(self, parser, config):
        self.parser = parser
        self.config = config

    def process_content(self):
        # Process all components and return structured data
        return {
            "word": self.parser.word,
            "pos": self.parser.part_of_speech,
            "kotus": self.parser.kotus_type,
            "definition": self.parser.definition,
            "conjugation": self.parser.conjugation_table,
        }
