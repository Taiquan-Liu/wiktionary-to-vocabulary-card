import click
from .config import load_config, update_config
from .parser import WiktionaryParser
from .processor import ContentProcessor
from .generator import MarkdownGenerator

@click.group()
def cli():
    """Wiktionary Vocabulary Card Generator"""
    pass

@cli.command()
@click.argument('url')
@click.option('-o', '--output', help='Output file path')
def generate(url, output):
    """Generate vocabulary card from Wiktionary URL"""
    config = load_config()
    parser = WiktionaryParser(url)
    parser.fetch_page()
    parser.find_finnish_section()
    parser.parse_part_of_speech()
    parser.parse_kotus_info()
    parser.parse_definitions()

    processor = ContentProcessor(parser, config)
    content = processor.process_content()

    generator = MarkdownGenerator(content, config)
    card = generator.generate_card()

    if output:
        with open(output, 'w') as f:
            f.write(card)
    else:
        click.echo(card)

@cli.command()
@click.option('--custom-text', help='Set custom text for cards')
def configure(custom_text):
    """Update configuration settings"""
    if custom_text:
        update_config({'custom_text': custom_text})
        click.echo("Configuration updated successfully!")
