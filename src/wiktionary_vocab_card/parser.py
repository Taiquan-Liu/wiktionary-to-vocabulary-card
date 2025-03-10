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
    return markdown.strip()


class WiktionaryParser:
    def __init__(self, url):
        self.url = url
        self.word = unquote(url.split('/wiki/')[-1]).replace('_', ' ')
        self.soup = None
        self.finnish_section = None
        self.part_of_speech = None
        self.kotus_type = None
        self.conjugation_md = ""
        self.table = None
        self.definition = None

    def fetch_page(self):
        response = requests.get(self.url)
        response.raise_for_status()
        self.soup = BeautifulSoup(response.content, 'html.parser')

    def find_finnish_section(self):
        finnish_span = self.soup.find('span', {'id': 'Finnish'})
        if not finnish_span:
            raise ValueError("Finnish section not found")
        self.finnish_section = finnish_span.find_parent(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

    def parse_part_of_speech(self):
        for sibling in self.finnish_section.next_siblings:
            if sibling.name == 'p':
                b_tag = sibling.find('b')
                if b_tag:
                    self.part_of_speech = b_tag.get_text().strip().lower()
                    break
            # Stop at next section
            if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                break

    def parse_kotus_info(self):
        for sibling in self.finnish_section.next_siblings:
            if sibling.name == 'table':
                caption = sibling.find('caption')
                if caption:
                    caption_text = caption.get_text()
                    match = re.search(r'Kotus type ([^,\s)]+)', caption_text)
                    if match:
                        kotus_full = match.group(1)
                        kotus_parts = kotus_full.split('/')
                        self.kotus_type = kotus_parts[-1]  # Take the last part after /
                        # Convert table to markdown
                        self.conjugation_md = html_table_to_markdown(sibling)
                        break
            # Stop at next section
            if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                break

    def parse_definitions(self):
        for sibling in self.finnish_section.next_siblings:
            if sibling.name in ['ol', 'ul']:
                items = sibling.find_all('li')
                self.definition = '\n'.join([f"{i+1}. {li.get_text().strip()}" for i, li in enumerate(items)])
                break
            # Stop at next section
            if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                break