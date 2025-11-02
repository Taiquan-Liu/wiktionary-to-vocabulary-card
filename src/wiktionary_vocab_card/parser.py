import re
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

SUPPORTED_WORD_TYPES = [
    "Noun",
    "Verb",
    "Adjective",
    "Adverb",
    "Pronoun",
    "Participle",
    "Preposition",
    "Postposition",
    "Conjunction",
    "Phrase",
    "Prefix",
    "Numeral",
    "Particle",
]


def html_table_to_markdown(table):
    """Convert a BeautifulSoup table element to Markdown format."""
    if not table:
        return ""

    # First, remove all nested tables completely
    nested_tables = table.find_all("table", recursive=True)
    for nested in nested_tables:
        if nested != table:  # Don't remove the main table
            nested.decompose()

    # Now parse the simplified table
    rows = table.find_all("tr")
    if not rows:
        return ""

    # Analyze table structure
    max_cols = 0
    for row in rows:
        cells = row.find_all(["th", "td"])
        cols_in_row = sum(
            int(cell.get("colspan", 1)) for cell in cells if cell is not None
        )
        max_cols = max(max_cols, cols_in_row)

    markdown_rows = []
    for row in rows:
        cells = row.find_all(["th", "td"])
        markdown_cells = []

        for cell in cells:
            if cell is None:
                continue

            # Extract text, handling line breaks
            text = cell.get_text().strip()
            text = re.sub(r"\s+", " ", text)

            # Handle colspan
            colspan = int(cell.get("colspan", 1))
            markdown_cells.append(text)

            # Add empty cells for spanning columns
            for _ in range(1, colspan):
                markdown_cells.append("")

        # Pad with empty cells if needed
        while len(markdown_cells) < max_cols:
            markdown_cells.append("")

        markdown_rows.append(markdown_cells)

    # Find the maximum non-empty column
    max_used_cols = 0
    for row in markdown_rows:
        for i in range(len(row) - 1, -1, -1):
            if row[i].strip():
                max_used_cols = max(max_used_cols, i + 1)
                break

    # Trim rows to only include used columns
    trimmed_rows = [row[:max_used_cols] for row in markdown_rows]

    # Convert to markdown
    result = []
    for i, row in enumerate(trimmed_rows):
        if all(cell == "" for cell in row):
            continue

        line = "| " + " | ".join(row) + " |"
        result.append(line)

        if i == 0:
            result.append("| " + " | ".join(["---"] * len(row)) + " |")

    return "\n".join(result)


class WiktionaryParser:
    def __init__(self, url):
        self.url = self._clean_url(url)
        self.word = unquote(self.url.split("/wiki/")[-1]).replace("_", " ")
        self.soup = None
        self.finnish_section = None
        self.word_types = {}
        self.kotus_types = []
        self.definitions = []
        self.conjugation_tables = []
        # Word with one word type has h3 header, multiple word types have h4 header
        self.header_level = 3

    @property
    def header_level_str(self):
        return f"h{self.header_level}"

    @staticmethod
    def _clean_url(url):
        return url.split("#")[0]

    def fetch_page(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(self.url, headers=headers)
        response.raise_for_status()
        self.soup = BeautifulSoup(response.content, "html.parser")

    def find_finnish_section(self):
        finnish_header = self.soup.find("h2", {"id": "Finnish"})
        if not finnish_header:
            raise ValueError("Finnish section not found")
        self.finnish_section = finnish_header

    def find_next_non_finnish_section(self):
        self.next_non_finnish_section = None
        current = self.finnish_section
        while current:
            current = current.find_next()
            if not current:
                break
            if current.name == "h2":
                self.next_non_finnish_section = current
                break

    def _parse_word_type_headers(self, current, header_level):
        header = current.find(header_level)
        if header and header.get("id").split("_", 1)[0] in SUPPORTED_WORD_TYPES:
            self.word_types[header.get_text().strip().lower()] = header

    def parse_word_type(self):
        # Find the h3 tag with "Noun", "Verb", etc.
        # Search through all elements after Finnish section, not just siblings
        current = self.finnish_section
        while current:
            current = current.find_next()
            if not current:
                break
            # Check if it already in the next non-finnish section
            if current == self.next_non_finnish_section:
                break
            # Check for h3 within a div
            if current.name == "div" and "mw-heading" in current.get("class", []):
                self._parse_word_type_headers(current, self.header_level_str)

    def _parse_form_table_header(self, form_table_name, word_type):
        """Parse either the declension or conjugation table based on the type of the
        word"""
        current = self.finnish_section

        while current:
            current = current.find_next()
            if not current:
                break

            if current.name == "div" and "mw-heading" in current.get("class", []):
                header = current.find(f"h{self.header_level + 1}")
                if header and form_table_name in header.get_text():
                    return header

    def parse_non_verb_declension(self, word_type):
        # Find the declension heading first
        current = self._parse_form_table_header("Declension", word_type)

        if current:
            # Find the inflection table after the declension header
            inflection_table = None

            while current:
                current = current.find_next()
                if not current:
                    break

                if current.name == "table" and "inflection-table" in current.get(
                    "class", []
                ):
                    inflection_table = current
                    break

            if inflection_table:
                # Extract Kotus type from the table header text
                th = inflection_table.find("th", {"colspan": "4"})
                if th:
                    th_text = th.get_text()
                    match = re.search(r"Kotus type ([^,\s)]+)", th_text)
                    if match:
                        kotus_full = match.group(1)
                        kotus_parts = kotus_full.split("/")
                        self.kotus_types.append(
                            kotus_parts[-1]
                        )  # Take the last part after /

                # Convert table to markdown for conjugation_table
                self.conjugation_tables.append(html_table_to_markdown(inflection_table))

    def parse_verb_conjugation(self, word_type):
        # Find conjugation header for verbs
        current = self._parse_form_table_header("Conjugation", word_type)

        if current:
            # Find the inflection table after the conjugation header
            while current:
                current = current.find_next()
                if not current:
                    break  # Stop if no more elements
                
                # Stop at next heading (but not just any div)
                if current.name == "div" and "mw-heading" in current.get("class", []):
                    break  # Stop at next header

                if (
                    current
                    and current.name == "table"
                    and "inflection-table" in current.get("class", [])
                ):
                    # Extract Kotus type from table header text if present
                    th = current.find("th")
                    if th:
                        th_text = th.get_text()
                        match = re.search(r"Kotus type ([^,\s)]+)", th_text)
                        if match:
                            kotus_full = match.group(1)
                            kotus_parts = kotus_full.split("/")
                            self.kotus_types.append(kotus_parts[-1])

                    # Convert table to markdown
                    self.conjugation_tables.append(html_table_to_markdown(current))
                    return

    def parse_definitions(self, word_type):
        # Find the list element containing definitions
        current = self.finnish_section
        found_pos = False

        while current:
            current = current.find_next()
            if not current:
                break

            if current.name == "div" and "mw-heading" in current.get("class", []):
                header = current.find(self.header_level_str)
                if header and header.get_text().strip().lower() == word_type:
                    found_pos = True

            if found_pos and current.name == "ol":
                items = current.find_all("li", recursive=False)
                self.definitions.append(
                    "\n".join(
                        [
                            f"{i+1}. {li.get_text().strip()}"
                            for i, li in enumerate(items)
                        ]
                    )
                )
                break

    def parse(self):
        """Process everything in the right order"""
        self.fetch_page()
        self.find_finnish_section()
        self.find_next_non_finnish_section()
        # For words with one word type, the header is an h3
        self.parse_word_type()
        if not self.word_types:
            # For words with multiple word types, the header is an h4
            self.header_level = 4
            self.parse_word_type()

        for word_type in self.word_types:
            self.parse_definitions(word_type)
            if word_type == "verb":
                self.parse_verb_conjugation(word_type)
            else:
                self.parse_non_verb_declension(word_type)  # For nouns, adjectives, etc.

        return self
