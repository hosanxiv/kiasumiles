from __future__ import annotations

from html import unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
LANDING = ROOT / "kiasumiles" / "static" / "kiasumiles" / "index.html"
PUBLIC_SETUP_PROMPT = (
    "Install KiasuMiles MCP for me: https://kiasumiles.space/mcp\n\n"
    "Use KiasuMiles. First help me set up my card stack. Ask me which banks I have cards "
    "with, show me the matching supported cards, then remember my selected cards for future "
    "KiasuMiles lookups."
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
