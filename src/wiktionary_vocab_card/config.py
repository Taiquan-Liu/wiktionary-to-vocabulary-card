from pathlib import Path
from typing import Dict, Any, Optional

import yaml
from appdirs import user_config_dir

CONFIG_DIR = Path(user_config_dir("wiktionary_vocab_card"))
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# Enhanced default configuration with new schema
DEFAULT_CONFIG = {
    # Existing settings (maintain compatibility)
    "custom_text": "{custom text}",
    "default_output": "vocabulary_cards",
    "table_folding": True,
    # New vault and file management settings
    "vault": {
        "path": "/Users/taiquanliu/Documents/1st remote/Suomi",
        "name": "1st remote",  # Actual Obsidian vault name
        "learning_stages": {
            "new": "New",
            "memorizing": "Memorizing",
            "remembered": "Remembered",
        },
    },
    "output": {
        "mode": "filesystem",  # or "clipboard" or "both"
        "create_directories": True,
        "backup_existing": False,
        "open_in_obsidian": True,  # Open generated files in Obsidian by default
    },
    "file_management": {
        "check_existing": True,
        "append_articles": True,
        "move_from_remembered": True,
    },
}


def load_config() -> Dict[str, Any]:
    """Load configuration from file, creating default if it doesn't exist.

    Ensures backward compatibility by merging with default config.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w") as f:
            yaml.safe_dump(DEFAULT_CONFIG, f)
        return DEFAULT_CONFIG.copy()

    with open(CONFIG_FILE) as f:
        user_config = yaml.safe_load(f) or {}

    # Merge with defaults to ensure all keys exist (backward compatibility)
    config = _merge_configs(DEFAULT_CONFIG, user_config)

    # Validate and fix any issues
    config = _validate_config(config)

    return config


def update_config(new_settings: Dict[str, Any]) -> None:
    """Update configuration settings with new values.

    Supports both flat updates (for backward compatibility) and nested updates.
    """
    config = load_config()

    # Handle nested updates properly
    config = _deep_update(config, new_settings)

    # Validate the updated config
    config = _validate_config(config)

    with open(CONFIG_FILE, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)


def get_vault_path() -> Optional[Path]:
    """Get the configured Obsidian vault path."""
    config = load_config()
    vault_path = config.get("vault", {}).get("path")
    if vault_path:
        return Path(vault_path)
    return None


def get_vault_name() -> Optional[str]:
    """Get the configured Obsidian vault name.

    Returns the explicitly configured vault name, or falls back to
    extracting from the vault path if no name is configured.
    """
    config = load_config()
    vault_config = config.get("vault", {})

    # First try explicit vault name
    vault_name = vault_config.get("name")
    if vault_name:
        return vault_name

    # Fallback to extracting from path (for backward compatibility)
    vault_path = vault_config.get("path")
    if vault_path:
        # Try to find the actual vault directory by looking for .obsidian folder
        path = Path(vault_path)
        while path.parent != path:  # While not at root
            if (path / ".obsidian").exists():
                return path.name
            path = path.parent

        # If no .obsidian folder found, use the configured path's name
        return Path(vault_path).name

    return None


def get_stage_directory(stage: str) -> Optional[Path]:
    """Get the directory path for a specific learning stage.

    Args:
        stage: One of 'new', 'memorizing', 'remembered'

    Returns:
        Path to the stage directory, or None if vault not configured
    """
    vault_path = get_vault_path()
    if not vault_path:
        return None

    config = load_config()
    stage_name = config.get("vault", {}).get("learning_stages", {}).get(stage)
    if stage_name:
        return vault_path / stage_name
    return None


def get_all_stage_directories() -> Dict[str, Path]:
    """Get all configured learning stage directories.

    Returns:
        Dictionary mapping stage keys to their directory paths
    """
    vault_path = get_vault_path()
    if not vault_path:
        return {}

    config = load_config()
    stages = config.get("vault", {}).get("learning_stages", {})

    return {
        stage_key: vault_path / stage_name for stage_key, stage_name in stages.items()
    }


def is_vault_configured() -> bool:
    """Check if Obsidian vault is properly configured."""
    vault_path = get_vault_path()
    return vault_path is not None and vault_path.exists()


def _merge_configs(default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge user config with default config."""
    result = default.copy()

    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value

    return result


def _deep_update(config: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively update nested dictionary."""
    result = config.copy()

    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_update(result[key], value)
        else:
            result[key] = value

    return result


def _validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and fix configuration values."""
    # Ensure vault path exists if specified
    if "vault" in config and "path" in config["vault"]:
        vault_path = Path(config["vault"]["path"])
        if not vault_path.exists():
            # Don't create the vault path automatically, just warn
            pass

    # Ensure output mode is valid
    valid_modes = {"filesystem", "clipboard", "both"}
    if config.get("output", {}).get("mode") not in valid_modes:
        config.setdefault("output", {})["mode"] = "filesystem"

    # Ensure boolean values are actually booleans
    bool_keys = [
        ("table_folding",),
        ("output", "create_directories"),
        ("output", "backup_existing"),
        ("output", "open_in_obsidian"),
        ("file_management", "check_existing"),
        ("file_management", "append_articles"),
        ("file_management", "move_from_remembered"),
    ]

    for key_path in bool_keys:
        current = config
        for key in key_path[:-1]:
            current = current.setdefault(key, {})

        final_key = key_path[-1]
        if final_key in current:
            current[final_key] = bool(current[final_key])

    return config
