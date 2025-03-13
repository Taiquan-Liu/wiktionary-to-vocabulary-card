from bs4 import BeautifulSoup
import re
from urllib.parse import unquote
import requests


def html_table_to_markdown(table):
    """Convert a BeautifulSoup table element to Markdown format."""
    headers = []
    rows = []
    # Extract headers from the first row (th elements)
    header_row = table.find('tr')
    if not header_row:
        return ""
    for th in header_row.find_all(['th', 'td']):
        headers.append(th.get_text().strip())

    # Extract data rows
    for row in table.find_all('tr')[1:]:  # Skip header row
        cells = row.find_all(['td', 'th'])
        row_data = [cell.get_text().strip() for cell in cells]
        rows.append(row_data)

    # Build Markdown table
    if not headers and not rows:
        return ""
    markdown = ""
    if headers:
        markdown += "| " + " | ".join(headers) + " |\n"
        markdown += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    for row in rows:
        markdown += "| " + " | ".join(row) + " |\n"
    # Remove trailing newline to prevent extra blank line
    return markdown.rstrip()


class WiktionaryParser:
    def __init__(self, url):
        self.url = url
        self.word = unquote(url.split('/wiki/')[-1]).replace('_', ' ')
        self.soup = None
        self.finnish_section = None
        self.part_of_speech = None
        self.kotus_type = None
        self.definition = None
        self.conjugation_table = None  # Add this property

    def fetch_page(self):
        response = requests.get(self.url)
        response.raise_for_status()
        self.soup = BeautifulSoup(response.content, 'html.parser')

    def find_finnish_section(self):
        finnish_header = self.soup.find('h2', {'id': 'Finnish'})
        if not finnish_header:
            raise ValueError("Finnish section not found")
        self.finnish_section = finnish_header

    def parse_part_of_speech(self):
        # Find the h3 tag with "Noun", "Verb", etc.
        # Search through all elements after Finnish section, not just siblings
        current = self.finnish_section
        while current:
            current = current.find_next()
            if not current:
                break
            # Check for h3 within a div
            if current.name == 'div' and 'mw-heading' in current.get('class', []):
                h3 = current.find('h3')
                if h3 and h3.get('id') in ['Noun', 'Verb', 'Adjective', 'Adverb', 'Pronoun']:
                    self.part_of_speech = h3.get_text().strip().lower()
                    break

    def parse_kotus_info(self):
        # Find the declension heading first
        current = self.finnish_section
        declension_header = None

        while current:
            current = current.find_next()
            if not current:
                break

            # Check for h4 within a div
            if current.name == 'div' and 'mw-heading' in current.get('class', []):
                h4 = current.find('h4')
                if h4 and 'Declension' in h4.get_text():
                    declension_header = h4
                    break

        if declension_header:
            # Find the inflection table after the declension header
            inflection_table = None
            current = declension_header

            while current:
                current = current.find_next()
                if not current:
                    break

                if current.name == 'table' and 'inflection-table' in current.get('class', []):
                    inflection_table = current
                    break

            if inflection_table:
                # Extract Kotus type from the table header text
                th = inflection_table.find('th', {'colspan': '4'})
                if th:
                    th_text = th.get_text()
                    match = re.search(r'Kotus type ([^,\s)]+)', th_text)
                    if match:
                        kotus_full = match.group(1)
                        kotus_parts = kotus_full.split('/')
                        self.kotus_type = kotus_parts[-1]  # Take the last part after /

                # Convert table to markdown for conjugation_table
                self.conjugation_table = html_table_to_markdown(inflection_table)

    def parse_definitions(self):
        # Wait until we've found the part of speech
        if not self.part_of_speech:
            return

        # Find the list element containing definitions
        current = self.finnish_section
        found_pos = False

        while current:
            current = current.find_next()
            if not current:
                break

            if current.name == 'div' and 'mw-heading' in current.get('class', []):
                h3 = current.find('h3')
                if h3 and h3.get_text().strip().lower() == self.part_of_speech:
                    found_pos = True

            if found_pos and current.name == 'ol':
                items = current.find_all('li', recursive=False)
                self.definition = '\n'.join([f"{i+1}. {li.get_text().strip()}" for i, li in enumerate(items)])
                break

    def parse(self):
        """Process everything in the right order"""
        self.fetch_page()
        self.find_finnish_section()
        self.parse_part_of_speech()
        self.parse_definitions()
        self.parse_kotus_info()
        return self
