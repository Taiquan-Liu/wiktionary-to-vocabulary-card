from pathlib import Path

import click

from .config import (get_vault_name, get_vault_path, is_vault_configured,
                     load_config, update_config)
from .generator import MarkdownGenerator
from .parser import WiktionaryParser
from .processor import ContentProcessor
from .utils import open_in_obsidian


@click.group()
def cli():
    """Wiktionary Vocabulary Card Generator"""


@cli.command()
@click.argument("url")
@click.option("-o", "--output", help="Output file path (overrides configuration)")
@click.option(
    "-t",
    "--custom-text",
    help="Article content for the wordcard. Replaces custom_text functionality.",
)
@click.option(
    "--no-open",
    is_flag=True,
    help="Don't open the generated file in Obsidian (opening is enabled by default)",
)
def generate(url, output, custom_text, no_open):
    """Generate vocabulary card from Wiktionary URL

    Uses intelligent file management when vault is configured, otherwise falls back
    to file output or clipboard based on configuration.
    """
    config = load_config()

    # Parse the Wiktionary page
    parser = WiktionaryParser(url)
    parser.parse()

    processor = ContentProcessor(parser, config)
    content = processor.process_content()

    generator = MarkdownGenerator(parser, content, config)

    # Handle article content (custom_text becomes article content)
    # If no -t option provided, use configured custom_text as article content
    configured_custom_text = config.get("custom_text", "")
    if configured_custom_text == "{custom text}":
        configured_custom_text = ""  # Ignore placeholder
    article_content = custom_text or configured_custom_text

    # Determine if we should open in Obsidian
    should_open = not no_open and config.get("output", {}).get("open_in_obsidian", True)

    # Handle output based on CLI options and configuration
    if output:
        # CLI output option overrides configuration
        card = generator.generate_card(article_content)
        try:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(card)
            click.echo(f"Wordcard saved to: {output_path}")

            # Open in Obsidian if requested and vault is configured
            if should_open and is_vault_configured():
                vault_path = get_vault_path()
                vault_name = get_vault_name()
                if vault_path:  # Additional check to satisfy type checker
                    try:
                        if open_in_obsidian(
                            output_path.resolve(), vault_path, vault_name
                        ):
                            click.echo("File opened in Obsidian")
                    except Exception as obsidian_error:
                        click.echo(
                            f"Warning: Could not open in Obsidian: {obsidian_error}"
                        )

        except Exception as e:
            click.echo(f"Error saving to {output}: {e}", err=True)
            click.echo("Falling back to console output:")
            click.echo(card)

    elif is_vault_configured():
        # Use intelligent file management system
        try:
            card, file_path = generator.generate_wordcard_with_file_management(
                article_content
            )

            if file_path:
                click.echo(f"Wordcard processed and saved to: {file_path}")

                # Open in Obsidian if requested
                if should_open:
                    vault_path = get_vault_path()
                    vault_name = get_vault_name()
                    if vault_path:  # Additional check to satisfy type checker
                        try:
                            if open_in_obsidian(file_path, vault_path, vault_name):
                                click.echo("File opened in Obsidian")
                        except Exception as obsidian_error:
                            click.echo(
                                f"Warning: Could not open in Obsidian: {obsidian_error}"
                            )

                # Also handle clipboard/console based on output mode
                output_mode = config.get("output", {}).get("mode", "filesystem")
                if output_mode == "clipboard":
                    click.echo("Content also copied to clipboard.")
                elif output_mode == "both":
                    click.echo("Content saved to file and copied to clipboard.")
            else:
                click.echo("File management disabled, showing content:")
                click.echo(card)

        except Exception as e:
            click.echo(f"Error with file management: {e}", err=True)
            click.echo("Falling back to simple generation:")
            card = generator.generate_card(article_content)
            click.echo(card)

    else:
        # Vault not configured, use legacy behavior
        card = generator.generate_card(article_content)

        output_mode = config.get("output", {}).get("mode", "clipboard")

        if output_mode in ["filesystem", "both"]:
            # Try to save to default location
            try:
                default_output = config.get("default_output", "vocabulary_cards")
                if not default_output.endswith(".md"):
                    # Extract word from URL for filename
                    word = url.split("/")[-1].replace("#", "_")
                    output_path = Path(f"{default_output}_{word}.md")
                else:
                    output_path = Path(default_output)

                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(card)
                click.echo(f"Wordcard saved to: {output_path}")

                # Open in Obsidian if requested and a basic vault is configured
                if should_open and is_vault_configured():
                    vault_path = get_vault_path()
                    vault_name = get_vault_name()
                    if vault_path:  # Additional check to satisfy type checker
                        try:
                            if open_in_obsidian(
                                output_path.resolve(), vault_path, vault_name
                            ):
                                click.echo("File opened in Obsidian")
                        except Exception as obsidian_error:
                            click.echo(
                                f"Warning: Could not open in Obsidian: {obsidian_error}"
                            )

                if output_mode == "clipboard":
                    click.echo("Content also copied to clipboard.")

            except Exception as e:
                click.echo(f"Error saving to default location: {e}", err=True)
                click.echo("Showing content instead:")
                click.echo(card)
        else:
            # Clipboard mode or fallback
            click.echo(card)
            if output_mode == "clipboard":
                click.echo("Content copied to clipboard.")


@cli.command()
@click.option(
    "--custom-text",
    help="Set custom text for cards (deprecated, use article content instead)",
)
@click.option("--vault-path", help="Set Obsidian vault path")
@click.option("--vault-name", help="Set Obsidian vault name (if different from path)")
@click.option(
    "--output-mode",
    type=click.Choice(["filesystem", "clipboard", "both"]),
    help="Set output mode",
)
@click.option("--table-folding", type=bool, help="Enable/disable table folding")
@click.option(
    "--open-obsidian", type=bool, help="Enable/disable opening files in Obsidian"
)
def configure(
    custom_text, vault_path, vault_name, output_mode, table_folding, open_obsidian
):
    """Update configuration settings

    Configure vault path, output modes, and other settings for intelligent
    file management and wordcard generation.
    """
    updates = {}

    if custom_text:
        updates["custom_text"] = custom_text

    if vault_path:
        vault_path_obj = Path(vault_path)
        if not vault_path_obj.exists():
            click.echo(f"Warning: Vault path does not exist: {vault_path}", err=True)
        updates.setdefault("vault", {})["path"] = str(vault_path_obj)

    if vault_name:
        updates.setdefault("vault", {})["name"] = vault_name

    if output_mode:
        updates["output"] = {"mode": output_mode}

    if table_folding is not None:
        updates["table_folding"] = table_folding

    if open_obsidian is not None:
        updates.setdefault("output", {})["open_in_obsidian"] = open_obsidian

    if updates:
        try:
            update_config(updates)
            click.echo("Configuration updated successfully!")

            # Show current vault status
            if is_vault_configured():
                click.echo("✓ Vault is configured and accessible")
            else:
                click.echo("⚠ Vault is not configured or not accessible")

        except Exception as e:
            click.echo(f"Error updating configuration: {e}", err=True)
    else:
        click.echo("No configuration changes specified.")


@cli.command()
def status():
    """Show current configuration and vault status"""
    config = load_config()

    click.echo("=== Wiktionary Vocabulary Card Configuration ===")
    click.echo()

    # Vault configuration
    vault_path = config.get("vault", {}).get("path")
    vault_name = config.get("vault", {}).get("name")
    if vault_path:
        click.echo(f"Vault Path: {vault_path}")
        if vault_name:
            click.echo(f"Vault Name: {vault_name}")
        if is_vault_configured():
            click.echo("Vault Status: ✓ Configured and accessible")
        else:
            click.echo("Vault Status: ⚠ Path not accessible")
    else:
        click.echo("Vault Status: ✗ Not configured")

    click.echo()

    # Output configuration
    output_mode = config.get("output", {}).get("mode", "clipboard")
    click.echo(f"Output Mode: {output_mode}")

    open_obsidian = config.get("output", {}).get("open_in_obsidian", True)
    click.echo(f"Open in Obsidian: {open_obsidian}")

    # File management settings
    file_mgmt = config.get("file_management", {})
    click.echo(f"Check Existing Files: {file_mgmt.get('check_existing', True)}")
    click.echo(f"Append Articles: {file_mgmt.get('append_articles', True)}")
    click.echo(f"Move from Remembered: {file_mgmt.get('move_from_remembered', True)}")

    click.echo()

    # Other settings
    click.echo(f"Table Folding: {config.get('table_folding', True)}")
    click.echo(f"Default Output: {config.get('default_output', 'vocabulary_cards')}")

    if config.get("custom_text") and config["custom_text"] != "{custom text}":
        click.echo(f"Custom Text: {config['custom_text']}")
