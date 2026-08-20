from __future__ import annotations

from html import unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
LANDING = ROOT / "kiasumiles" / "static" / "kiasumiles" / "index.html"
PUBLIC_SETUP_PROMPT = (
    "Connect me to KiasuMiles at https://kiasumiles.space/mcp if its tools are not already "
    "available.\n\n"
    "Ask before changing any settings. Do not claim KiasuMiles is connected until you can "
    "use and list its tools.\n\n"
    "If this AI agent does not support adding remote MCP connections from our conversation, "
    "say that it is unsupported and stop. Do not invent menu paths or setup instructions.\n\n"
    "Once connected, check for a saved card stack if the available tools support it. Show me "
    "any saved cards and ask whether I want to keep or change them. Otherwise, ask which banks "
    "I use and show me their supported cards.\n\n"
    "Before saving my selections, tell me what the KiasuMiles tools say about where they will "
    "be stored and whether they will persist across new conversations. Do not guess.\n\n"
    "After confirming my cards, ask for a Singapore merchant and recommend my best card."
)
WEBSITE_SETUP_PROMPT = (
    "Connect KiasuMiles at https://kiasumiles.space/mcp. Ask before changing settings or "
    "installing anything, and don't claim it's connected until you can list its tools and call "
    "kiasumiles_data_version successfully. Then ask which banks I use, show their supported "
    "cards, and let me confirm mine. Finally, ask for a Singapore merchant and how I'm paying, "
    "then recommend the best confirmed card with its conditions, caveats, and fallback if the "
    "match is uncertain."
)


def test_public_setup_prompts_are_present_on_github_and_website():
    readme = README.read_text(encoding="utf-8")
    landing = unescape(LANDING.read_text(encoding="utf-8"))

    assert PUBLIC_SETUP_PROMPT in readme
    assert f'data-copy="{WEBSITE_SETUP_PROMPT}"' in landing


def test_public_setup_is_client_neutral_and_nontechnical():
    public_copy = README.read_text(encoding="utf-8") + LANDING.read_text(encoding="utf-8")

    assert "uvx kiasumiles-mcp" not in public_copy
    assert "The Codex plugin" not in public_copy
    assert "### Codex plugin" not in public_copy


def test_public_setup_is_honest_about_connection_and_storage():
    readme = README.read_text(encoding="utf-8")
    landing = unescape(LANDING.read_text(encoding="utf-8"))

    normalized_readme = " ".join(readme.split())
    assert "Do not claim KiasuMiles is connected until you can use and list its tools." in normalized_readme
    assert "Do not invent menu paths or setup instructions." in normalized_readme
    assert "whether they will persist across new conversations" in normalized_readme

    normalized_landing = " ".join(landing.split())
    assert "don't claim it's connected until you can list its tools" in normalized_landing
    assert "kiasumiles_data_version successfully" in normalized_landing
    assert "fallback if the match is uncertain" in normalized_landing

    assert "Install KiasuMiles MCP for me" not in readme
    assert "Install KiasuMiles MCP for me" not in landing
    assert "It remembers your cards" not in landing


def test_public_setup_routes_claude_instructions_to_github():
    readme = README.read_text(encoding="utf-8")
    landing = unescape(LANDING.read_text(encoding="utf-8"))

    assert "Claude cannot add KiasuMiles from a chat message" in readme
    assert "custom connector" in readme
    assert "Claude and other agents" in landing
    assert "github.com/hosanxiv/kiasumiles#readme" in landing
