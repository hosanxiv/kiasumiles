from __future__ import annotations

from html import unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
LANDING = ROOT / "kiasumiles" / "static" / "kiasumiles" / "index.html"
def test_public_setup_prompts_are_present_on_github_and_website():
    readme = README.read_text(encoding="utf-8")
    landing = unescape(LANDING.read_text(encoding="utf-8"))

    assert "First verify the connection by calling kiasumiles_data_version." in readme
    assert "Use KiasuMiles. If its tools are already available, reuse them." in landing
    assert "connect to https://kiasumiles.space/mcp if you can manage remote MCP connections" in landing


def test_public_setup_is_client_neutral_and_nontechnical():
    public_copy = README.read_text(encoding="utf-8") + LANDING.read_text(encoding="utf-8")

    assert "uvx kiasumiles-mcp" not in public_copy
    assert "The Codex plugin" not in public_copy
    assert "### Codex plugin" not in public_copy
    assert "/api/chatgpt" not in public_copy


def test_public_setup_is_honest_about_connection_and_storage():
    readme = " ".join(README.read_text(encoding="utf-8").split())
    landing = " ".join(unescape(LANDING.read_text(encoding="utf-8")).split())

    assert "Do not claim KiasuMiles is connected until" in readme
    assert "the assistant must support external tools" in readme
    assert "does not retain them as a wallet" in readme

    assert "Do not claim KiasuMiles is connected until you can list its tools" in landing
    assert "kiasumiles_data_version successfully" in landing
    assert "If KiasuMiles tools aren’t available, stop and tell me." in landing
    assert "with its conditions and fallback" in landing
    assert "does not store your card stack" in landing

    assert "Install KiasuMiles MCP for me" not in readme
    assert "Install KiasuMiles MCP for me" not in landing
    assert "It remembers your cards" not in landing


def test_landing_keeps_setup_on_page_and_github_in_footer():
    readme = README.read_text(encoding="utf-8")
    landing = unescape(LANDING.read_text(encoding="utf-8"))

    assert "OpenClaw, Hermes, Zo and similar agents" in readme
    assert "### Codex desktop or CLI" in readme
    assert "### Claude" in readme
    assert "custom connector" in readme
    assert "ChatGPT Work on web and mobile" in readme
    assert "New Plugin" in readme
    assert "No Auth" in readme
    assert "ordinary ChatGPT Chat was not verified" in readme

    assert "setup-tab-claude" in landing
    assert "setup-tab-work" in landing
    assert "setup-tab-agents" in landing
    assert "Read the setup guide on GitHub" not in landing
    assert "github.com/hosanxiv/kiasumiles" in landing


def test_public_copy_is_mcp_only_and_lists_every_hosted_tool():
    readme = README.read_text(encoding="utf-8")
    landing = unescape(LANDING.read_text(encoding="utf-8"))

    assert "seven read-only MCP tools" in readme
    for tool in (
        "kiasumiles_list_cards",
        "kiasumiles_lookup",
        "kiasumiles_compare_payment_methods",
        "kiasumiles_changes_since",
        "kiasumiles_recommend_stack",
        "kiasumiles_data_version",
        "kiasumiles_agent_guide",
    ):
        assert tool in readme

    assert "public API" not in landing
    assert "We tested ChatGPT Work on mobile" in landing
    assert "using the same Pro account" in landing
    assert "KiasuMiles ONLY works with AI assistants that can use external tools." in landing
