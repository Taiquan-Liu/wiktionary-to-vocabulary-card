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
            "word_types": self.parser.word_types,
            "kotus_types": self.parser.kotus_types,
            "definitions": self.parser.definitions,
            "conjugation_tables": self.parser.conjugation_tables,
        }
