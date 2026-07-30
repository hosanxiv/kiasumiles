from __future__ import annotations

from html import unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
LANDING = ROOT / "kiasumiles" / "static" / "kiasumiles" / "index.html"
def test_public_setup_on_github_and_website_has_the_same_core_flow():
    readme = README.read_text(encoding="utf-8")
    landing = unescape(LANDING.read_text(encoding="utf-8"))

    for public_copy in (readme, landing):
        normalized_copy = " ".join(public_copy.split())
        assert "Connect me to KiasuMiles at https://kiasumiles.space/mcp" in normalized_copy
        assert "Ask before changing" in normalized_copy
        assert "Do not say KiasuMiles is connected until" in normalized_copy
        assert "which banks" in normalized_copy
        assert "show me the matching supported cards" in normalized_copy
        assert "whether my selections will persist" in normalized_copy
        assert "ask for a Singapore merchant and recommend my best card" in normalized_copy


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
        assert "Do not say KiasuMiles is connected until" in normalized_copy
        assert (
            "Do not invent setup instructions." in normalized_copy
            or "Do not guess." in normalized_copy
        )
        assert "whether my selections will persist" in normalized_copy
        assert "KiasuMiles" in normalized_copy
        assert "https://kiasumiles.space/mcp" in normalized_copy

    assert "Install KiasuMiles MCP for me" not in readme
    assert "Install KiasuMiles MCP for me" not in landing
    assert "It remembers your cards" not in landing


def test_public_setup_avoids_platform_specific_marketing_and_mobile_claims():
    readme = README.read_text(encoding="utf-8")
    landing = unescape(LANDING.read_text(encoding="utf-8"))

    assert "Do not claim that this setup works in the ChatGPT mobile app." in readme
    assert "### Supported agents" not in readme
    assert "### OpenClaw or Hermes through Telegram" in readme
    assert "Paste the quick-start message into your Telegram chat." in " ".join(readme.split())
    assert "Your AI agent handles your card list. KiasuMiles checks the rules." in landing
    for platform in ("ChatGPT", "Codex", "Claude", "OpenClaw", "Hermes"):
        assert platform not in landing
