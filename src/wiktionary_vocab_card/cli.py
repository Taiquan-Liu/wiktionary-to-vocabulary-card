import click

from .config import load_config, update_config
from .generator import MarkdownGenerator
from .parser import WiktionaryParser
from .processor import ContentProcessor


@click.group()
def cli():
    """Wiktionary Vocabulary Card Generator"""


@cli.command()
@click.argument("url")
@click.option("-o", "--output", help="Output file path")
@click.option(
    "-t", "--custom-text", help="Set custom text for cards. Overrides config."
)
def generate(url, output, custom_text):
    """Generate vocabulary card from Wiktionary URL"""
    config = load_config()
    if custom_text:
        config["custom_text"] = custom_text

    parser = WiktionaryParser(url)
    parser.parse()

    processor = ContentProcessor(parser, config)
    content = processor.process_content()

    generator = MarkdownGenerator(parser, content, config)
    card = generator.generate_card()

    if output:
        with open(output, "w") as f:
            f.write(card)
    else:
        click.echo(card)


@cli.command()
@click.option("--custom-text", help="Set custom text for cards")
def configure(custom_text):
    """Update configuration settings"""
    if custom_text:
        update_config({"custom_text": custom_text})
        click.echo("Configuration updated successfully!")
