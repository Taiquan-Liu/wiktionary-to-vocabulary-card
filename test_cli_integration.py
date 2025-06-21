#!/usr/bin/env python3
"""
Test script to verify CLI integration with enhanced systems
"""

from click.testing import CliRunner

from src.wiktionary_vocab_card.cli import cli
from src.wiktionary_vocab_card.config import is_vault_configured, load_config


def test_cli_integration():
    """Test the CLI integration with enhanced configuration and file management."""
    runner = CliRunner()

    print("=== CLI Integration Test ===\n")

    # Test 1: Status command
    print("1. Testing status command...")
    result = runner.invoke(cli, ["status"])
    print(f"Exit code: {result.exit_code}")
    if result.exit_code == 0:
        print("✓ Status command works")
        print("Status output:")
        print(result.output)
    else:
        print("✗ Status command failed")
        print(result.output)

    print("\n" + "=" * 50 + "\n")

    # Test 2: Configuration loading
    print("2. Testing configuration loading...")
    try:
        config = load_config()
        print("✓ Configuration loaded successfully")
        print(f"Vault configured: {is_vault_configured()}")
        print(f"Output mode: {config.get('output', {}).get('mode', 'clipboard')}")
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")

    print("\n" + "=" * 50 + "\n")

    # Test 3: Generate command help
    print("3. Testing generate command help...")
    result = runner.invoke(cli, ["generate", "--help"])
    print(f"Exit code: {result.exit_code}")
    if result.exit_code == 0:
        print("✓ Generate command help works")
    else:
        print("✗ Generate command help failed")
        print(result.output)

    print("\n" + "=" * 50 + "\n")

    # Test 4: Configure command help
    print("4. Testing configure command help...")
    result = runner.invoke(cli, ["configure", "--help"])
    print(f"Exit code: {result.exit_code}")
    if result.exit_code == 0:
        print("✓ Configure command help works")
    else:
        print("✗ Configure command help failed")
        print(result.output)

    print("\n" + "=" * 50 + "\n")

    # Test 5: Configuration update
    print("5. Testing configuration update...")
    result = runner.invoke(cli, ["configure", "--output-mode", "filesystem"])
    print(f"Exit code: {result.exit_code}")
    if result.exit_code == 0:
        print("✓ Configuration update works")
        print("Update output:")
        print(result.output)
    else:
        print("✗ Configuration update failed")
        print(result.output)

    print("\n=== Integration Test Complete ===")


if __name__ == "__main__":
    test_cli_integration()
