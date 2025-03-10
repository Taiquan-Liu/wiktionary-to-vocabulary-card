from pathlib import Path
import yaml
from appdirs import user_config_dir

CONFIG_DIR = Path(user_config_dir("wiktionary_vocab_card"))
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG = {
    "custom_text": "{custom text}",
    "default_output": "vocabulary_cards",
    "table_folding": True
}

def load_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w") as f:
            yaml.safe_dump(DEFAULT_CONFIG, f)

    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f)

def update_config(new_settings):
    config = load_config()
    config.update(new_settings)
    with open(CONFIG_FILE, "w") as f:
        yaml.safe_dump(config, f)
