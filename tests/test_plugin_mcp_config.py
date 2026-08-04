from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_MCP_CONFIG = REPO_ROOT / "plugins" / "kiasumiles" / ".mcp.json"
PLUGIN_MANIFEST = REPO_ROOT / "plugins" / "kiasumiles" / ".codex-plugin" / "plugin.json"
PLUGIN_SKILL = REPO_ROOT / "plugins" / "kiasumiles" / "skills" / "kiasumiles" / "SKILL.md"


def test_plugin_mcp_config_uses_hosted_server():
    payload = json.loads(PLUGIN_MCP_CONFIG.read_text(encoding="utf-8"))

    assert payload["mcpServers"]["kiasumiles"] == {
        "url": "https://kiasumiles.space/mcp",
    }


def test_plugin_manifest_describes_hosted_stateless_usage():
    payload = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))

    assert payload["version"] == "1.0.2"
    public_copy = " ".join(
        [
            payload["description"],
            payload["interface"]["longDescription"],
        ]
    ).lower()
    assert "hosted" in public_copy
    assert "does not store a wallet" in public_copy
    assert "local wallet" not in public_copy
    assert "saved on this device" not in public_copy


def test_plugin_skill_uses_only_hosted_tools():
    contents = PLUGIN_SKILL.read_text(encoding="utf-8")

    assert "kiasumiles_lookup" in contents
    assert "kiasumiles_recommend_stack" in contents
    assert "kiasumiles_configure" not in contents
    assert "kiasumiles_get_wallet" not in contents
    assert "persistent local" not in contents.lower()
