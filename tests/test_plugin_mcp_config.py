from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_MCP_CONFIG = REPO_ROOT / "plugins" / "kiasumiles" / ".mcp.json"
PLUGIN_MANIFEST = REPO_ROOT / "plugins" / "kiasumiles" / ".codex-plugin" / "plugin.json"
PYPROJECT = REPO_ROOT / "pyproject.toml"


def test_plugin_mcp_config_launches_local_wallet_server():
    payload = json.loads(PLUGIN_MCP_CONFIG.read_text(encoding="utf-8"))

    assert payload["mcpServers"]["kiasumiles"] == {
        "command": "uvx",
        "args": ["kiasumiles-mcp"],
    }


def test_plugin_manifest_describes_local_wallet_persistence():
    payload = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))

    assert payload["version"] == "1.0.2"
    assert "local wallet" in payload["description"].lower()
    assert "saved on this device" in payload["interface"]["longDescription"].lower()
    assert "hosted service" in payload["interface"]["longDescription"].lower()


def test_package_exposes_local_mcp_command():
    contents = PYPROJECT.read_text(encoding="utf-8")

    assert 'kiasumiles-mcp = "kiasumiles.local:main"' in contents
