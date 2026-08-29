from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LANDING = ROOT / "kiasumiles" / "static" / "kiasumiles" / "index.html"
README = ROOT / "README.md"

CURRENT_PALETTE = (
    "#061427",
    "#263a55",
    "#62728a",
    "#2bd6ad",
    "#003f37",
    "#f4f9ff",
)

MERCHANT_ASSETS = (
    "fairprice-real-crop.png",
    "grab-colour.svg",
    "watsons-crop.png",
    "shell-colour.svg",
    "Singapore_Airlines_Logo.svg",
    "din-tai-fung-logo.svg",
)

FORBIDDEN = (
    "data:image",
    "product-demo-60s",
    "MCC",
    "card_id",
    "UOB Preferred Platinum Visa",
    "Cap within limit",
    "Wallet stays client-side",
    "Service status",
    'href="/health"',
    "Codex and compatible agents",
    "assets/mascot/",
)


def test_landing_preserves_the_approved_visual_contract():
    landing = LANDING.read_text(encoding="utf-8")

    for colour in CURRENT_PALETTE:
        assert colour in landing
    for asset in MERCHANT_ASSETS:
        assert asset in landing

    assert "The right card, before you tap." in landing
    assert '<span class="brand-mark" aria-hidden="true">KM</span>' in landing
    for section_id in ("answer", "flow", "privacy", "start"):
        assert f'id="{section_id}"' in landing
    for heading in (
        "Your cards. One answer.",
        "Ask, and you're done.",
        "Set it up once, then just ask.",
    ):
        assert heading in landing


def test_landing_copy_is_truthful_and_accessible():
    landing = LANDING.read_text(encoding="utf-8")

    required_copy = (
        "Ask your AI agent which card to tap. KiasuMiles answers from the cards you actually own.",
        "Maximise your miles, without the guesswork.",
        "Copy this to your AI agent. It will either connect and verify the tools, or tell you plainly that it cannot.",
        "Connect KiasuMiles at https://kiasumiles.space/mcp.",
        "kiasumiles_data_version successfully",
        "Claude and other agents",
        "Read the setup guide on GitHub",
        "We never see your card numbers.",
        "does not store your card stack",
        "UOB Preferred Visa",
        "uob-preferred-platinum-visa-card.png",
        "Apple Pay",
        "Example · sample cards",
        "/kiasumiles/assets/proof/kiasumiles-cold-storage-chat.jpg",
        "A real KiasuMiles recommendation for Cold Storage.",
        "/privacy",
        "github.com/hosanxiv/kiasumiles",
        "t.me/kiasumilesbot",
        'aria-label="Copy KiasuMiles setup message"',
        'aria-live="polite"',
        "Copy didn't work. Select the message and copy it manually.",
    )
    for copy in required_copy:
        assert copy in landing


def test_landing_is_small_and_has_no_removed_or_internal_copy():
    landing_bytes = LANDING.read_bytes()
    landing = landing_bytes.decode("utf-8")

    assert len(landing_bytes) < 100_000
    for forbidden in FORBIDDEN:
        assert forbidden not in landing


def test_readme_does_not_promote_a_landing_page_video_demo():
    readme = README.read_text(encoding="utf-8")

    assert "live landing page and 60s demo" not in readme
