from __future__ import annotations

from html import unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
LANDING = ROOT / "kiasumiles" / "static" / "kiasumiles" / "index.html"
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

    normalized_readme = " ".join(readme.split())
    assert "Connect me to KiasuMiles at https://kiasumiles.space/mcp" in normalized_readme
    assert "Ask before changing settings or running installation commands." in normalized_readme
    assert "Do not say KiasuMiles is connected until" in normalized_readme
    assert "show me the matching supported cards" in normalized_readme
    assert "whether my selections will persist" in normalized_readme
    assert "After confirming my cards, ask for a Singapore merchant" in normalized_readme

    assert f'data-copy="{WEBSITE_SETUP_PROMPT}"' in landing


def test_public_setup_is_client_neutral_and_nontechnical():
    public_copy = README.read_text(encoding="utf-8") + LANDING.read_text(encoding="utf-8")

    assert "uvx kiasumiles-mcp" not in public_copy
    assert "The Codex plugin" not in public_copy
    assert "### Codex plugin" not in public_copy


def test_public_setup_is_honest_about_connection_and_storage():
    readme = " ".join(README.read_text(encoding="utf-8").split())
    landing = " ".join(unescape(LANDING.read_text(encoding="utf-8")).split())

    assert "Do not say KiasuMiles is connected until" in readme
    assert "whether my selections will persist" in readme
    assert "hosted KiasuMiles server stores my card stack" in readme

    assert "don't claim it's connected until you can list its tools" in landing
    assert "kiasumiles_data_version successfully" in landing
    assert "fallback if the match is uncertain" in landing
    assert "does not store your card stack" in landing

    assert "Install KiasuMiles MCP for me" not in readme
    assert "Install KiasuMiles MCP for me" not in landing
    assert "It remembers your cards" not in landing


def test_landing_routes_detailed_agent_setup_to_github():
    readme = README.read_text(encoding="utf-8")
    landing = unescape(LANDING.read_text(encoding="utf-8"))

    assert "### OpenClaw or Hermes through Telegram" in readme
    assert "### Codex on desktop" in readme
    assert "### Claude" in readme
    assert "custom connector" in readme
    assert "Do not claim that this setup works in the ChatGPT mobile app." in readme

    assert "Claude and other agents" in landing
    assert "github.com/hosanxiv/kiasumiles#readme" in landing
