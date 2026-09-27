from copy import deepcopy

import pytest
import yaml

from wiktionary_vocab_card.config import DEFAULT_CONFIG


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """No test may read or update the user's CLI configuration or vault."""
    config = deepcopy(DEFAULT_CONFIG)
    vault = tmp_path / "vault"
    vault.mkdir()
    config["vault"].update(path=str(vault), name="test-vault", organization="frequency")
    config["output"]["open_in_obsidian"] = False
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    monkeypatch.setenv("WIKT_VOCAB_CONFIG", str(path))
    return path, config
