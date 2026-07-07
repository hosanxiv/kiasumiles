from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_MCP_CONFIG = REPO_ROOT / "plugins" / "kiasumiles" / ".mcp.json"
PLUGIN_MANIFEST = REPO_ROOT / "plugins" / "kiasumiles" / ".codex-plugin" / "plugin.json"
HOSTED_MCP_URL = "https://kiasumiles.space/mcp"


def test_plugin_mcp_config_uses_hosted_url():
    payload = json.loads(PLUGIN_MCP_CONFIG.read_text(encoding="utf-8"))

    assert payload["mcpServers"]["kiasumiles"] == {
        "url": HOSTED_MCP_URL,
    }


def test_plugin_manifest_describes_hosted_mcp():
    payload = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))

    assert payload["version"] == "1.0.1"
    assert payload["description"] == "Hosted Singapore credit-card miles optimizer for Codex via MCP."
    assert "hosted MCP server" in payload["interface"]["longDescription"]
    assert "offline" not in payload["interface"]["longDescription"].lower()
