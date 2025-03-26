import re
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup


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
        self.url = url
        self.word = unquote(url.split("/wiki/")[-1]).replace("_", " ")
        self.soup = None
        self.finnish_section = None
        self.word_type = None
        self.kotus_type = None
        self.definition = None
        self.conjugation_table = None
        self.form_table_header = None

    def fetch_page(self):
        response = requests.get(self.url)
        response.raise_for_status()
        self.soup = BeautifulSoup(response.content, "html.parser")

    def find_finnish_section(self):
        finnish_header = self.soup.find("h2", {"id": "Finnish"})
        if not finnish_header:
            raise ValueError("Finnish section not found")
        self.finnish_section = finnish_header

    def parse_word_type(self):
        # Find the h3 tag with "Noun", "Verb", etc.
        # Search through all elements after Finnish section, not just siblings
        current = self.finnish_section
        while current:
            current = current.find_next()
            if not current:
                break
            # Check for h3 within a div
            if current.name == "div" and "mw-heading" in current.get("class", []):
                h3 = current.find("h3")
                if h3 and h3.get("id").split("_", 1)[0] in [
                    "Noun",
                    "Verb",
                    "Adjective",
                    "Adverb",
                    "Pronoun",
                ]:
                    self.word_type = h3.get_text().strip().lower()
                    break

    def parse_form_table(self, form_table_name):
        """Parse either the declension or conjugation table based on the type of the
        word"""
        self.form_table_header = None

        current = self.finnish_section

        while current:
            current = current.find_next()
            if not current:
                break

            if current.name == "div" and "mw-heading" in current.get("class", []):
                h4 = current.find("h4")
                if h4 and form_table_name in h4.get_text():
                    self.form_table_header = h4
                    break

    def parse_non_verb_declension(self):
        # Find the declension heading first
        self.parse_form_table("Declension")

        if self.form_table_header:
            # Find the inflection table after the declension header
            inflection_table = None
            current = self.form_table_header

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
                        self.kotus_type = kotus_parts[-1]  # Take the last part after /

                # Convert table to markdown for conjugation_table
                self.conjugation_table = html_table_to_markdown(inflection_table)

    def parse_verb_conjugation(self):
        # Find conjugation header for verbs
        self.parse_form_table("Conjugation")

        if self.form_table_header:
            # Find the inflection table after the conjugation header
            current = self.form_table_header
            while current:
                current = current.find_next()
                if (
                    not current
                    and current.name == "div"
                    and "mw-heading" in current.get("class", [])
                ):
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
                            self.kotus_type = kotus_parts[-1]

                    # Convert table to markdown
                    self.conjugation_table = html_table_to_markdown(current)
                    return

    def parse_definitions(self):
        # Wait until we've found the part of speech
        if not self.word_type:
            return

        # Find the list element containing definitions
        current = self.finnish_section
        found_pos = False

        while current:
            current = current.find_next()
            if not current:
                break

            if current.name == "div" and "mw-heading" in current.get("class", []):
                h3 = current.find("h3")
                if h3 and h3.get_text().strip().lower() == self.word_type:
                    found_pos = True

            if found_pos and current.name == "ol":
                items = current.find_all("li", recursive=False)
                self.definition = "\n".join(
                    [f"{i+1}. {li.get_text().strip()}" for i, li in enumerate(items)]
                )
                break

    def parse(self):
        """Process everything in the right order"""
        self.fetch_page()
        self.find_finnish_section()
        self.parse_word_type()
        self.parse_definitions()

        if self.word_type == "verb":
            self.parse_verb_conjugation()
        else:
            self.parse_non_verb_declension()  # For nouns, adjectives, etc.

        return self
