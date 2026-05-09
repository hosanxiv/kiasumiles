import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from kiasumiles.setup import setup_json_config, find_binary


def test_setup_json_config_creates_new_file(tmp_path):
    config_path = tmp_path / "config.json"
    binary = "/usr/local/bin/kiasumiles-mcp"
    result = setup_json_config(config_path, "Test Agent", binary)
    assert result is True
    data = json.loads(config_path.read_text())
    assert data["mcpServers"]["kiasumiles"]["command"] == binary


def test_setup_json_config_merges_existing(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "mcpServers": {
            "other_tool": {"command": "/usr/bin/other"}
        }
    }))
    binary = "/usr/local/bin/kiasumiles-mcp"
    setup_json_config(config_path, "Test Agent", binary)
    data = json.loads(config_path.read_text())
    assert "other_tool" in data["mcpServers"]
    assert "kiasumiles" in data["mcpServers"]


def test_setup_json_config_handles_empty_file(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("{}")
    binary = "/usr/local/bin/kiasumiles-mcp"
    result = setup_json_config(config_path, "Test Agent", binary)
    assert result is True
    data = json.loads(config_path.read_text())
    assert data["mcpServers"]["kiasumiles"]["command"] == binary


def test_setup_json_config_creates_parent_dirs(tmp_path):
    config_path = tmp_path / "deep" / "nested" / "config.json"
    binary = "/usr/local/bin/kiasumiles-mcp"
    setup_json_config(config_path, "Test Agent", binary)
    assert config_path.exists()


def test_find_binary_returns_path_when_found():
    with patch("shutil.which", return_value="/usr/local/bin/kiasumiles-mcp"):
        result = find_binary()
    assert result == Path("/usr/local/bin/kiasumiles-mcp")


def test_find_binary_falls_back_to_venv(tmp_path):
    fake_binary = tmp_path / "kiasumiles-mcp"
    fake_binary.touch()
    fake_binary.chmod(0o755)
    with patch("shutil.which", return_value=None):
        with patch("sys.executable", str(tmp_path / "python")):
            result = find_binary()
    assert result == fake_binary
