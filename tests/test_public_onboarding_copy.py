from __future__ import annotations

from html import unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
LANDING = ROOT / "kiasumiles" / "static" / "kiasumiles" / "index.html"
PUBLIC_SETUP_PROMPT = (
    "Connect me to KiasuMiles at https://kiasumiles.space/mcp if your environment supports "
    "remote MCP connections and its tools are not already available.\n\n"
    "Ask before changing any settings. Do not say KiasuMiles is connected until you can "
    "actually list and use its tools.\n\n"
    "If you cannot add the connection yourself, say so plainly and stop. Do not invent setup "
    "instructions.\n\n"
    "Once connected, help me set up my card stack. Ask which banks I use, show me the matching "
    "supported cards, and ask me to confirm my selections.\n\n"
    "Before saving anything, explain only what the available tools document about storage and "
    "whether my selections will persist. Do not guess.\n\n"
    "After confirming my cards, ask for a Singapore merchant and recommend my best card."
)


def test_public_setup_prompt_matches_on_github_and_website():
    readme = README.read_text(encoding="utf-8")
    landing = unescape(LANDING.read_text(encoding="utf-8"))

    assert PUBLIC_SETUP_PROMPT in readme
    assert f'data-copy="{PUBLIC_SETUP_PROMPT}"' in landing


def test_public_setup_is_client_neutral_and_nontechnical():
    public_copy = README.read_text(encoding="utf-8") + LANDING.read_text(encoding="utf-8")

    assert "uvx kiasumiles-mcp" not in public_copy
    assert "The Codex plugin" not in public_copy
    assert "### Codex plugin" not in public_copy


def test_public_setup_is_honest_about_connection_and_storage():
    readme = README.read_text(encoding="utf-8")
    landing = unescape(LANDING.read_text(encoding="utf-8"))

    for public_copy in (readme, landing):
        normalized_copy = " ".join(public_copy.split())
        assert "Do not say KiasuMiles is connected until you can actually list and use its tools." in normalized_copy
        assert "Do not invent setup instructions." in normalized_copy
        assert "whether my selections will persist" in normalized_copy
        assert "KiasuMiles" in normalized_copy
        assert "https://kiasumiles.space/mcp" in normalized_copy

    assert "Install KiasuMiles MCP for me" not in readme
    assert "Install KiasuMiles MCP for me" not in landing
    assert "It remembers your cards" not in landing


def test_public_setup_avoids_platform_specific_marketing_and_mobile_claims():
    readme = README.read_text(encoding="utf-8")
    landing = unescape(LANDING.read_text(encoding="utf-8"))

    assert "ChatGPT mobile" not in readme
    assert "### Supported agents" not in readme
    assert "**OpenClaw and Hermes via Telegram:**" in readme
    assert "Paste the setup prompt directly into your Telegram chat." in " ".join(readme.split())
    assert "Your AI agent handles your card list. KiasuMiles checks the rules." in landing
    for platform in ("ChatGPT", "Codex", "Claude", "OpenClaw", "Hermes"):
        assert platform not in landing
