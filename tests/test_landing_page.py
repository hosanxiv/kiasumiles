from __future__ import annotations

from pathlib import Path
import re


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

REMOVED_SATURATED_COLOURS = (
    "#1168ff",
    "#5fb43a",
    "#b7e76a",
)

MERCHANT_ASSETS = (
    "fairprice-real-crop.png",
    "grab-colour.svg",
    "watsons-crop.png",
    "shell-colour.svg",
    "shopee-real-crop.png",
    "Singapore_Airlines_Logo.svg",
)

SIGNATURE_HEADINGS = (
    "Where you tap changes what you earn.",
    "Your cards. One answer.",
    "Ask, and you're done.",
    "Set it up once, then just ask.",
)

FORBIDDEN = (
    "data:image",
    "product-demo-60s",
    "MCC",
    "card_id",
    "UOB Preferred Platinum Visa",
    "Cap within limit",
    "Wallet stays client-side",
    "Screen blurred for privacy",
)


def test_landing_preserves_press_recognisable_visual_contract():
    landing = LANDING.read_text(encoding="utf-8")

    for colour in CURRENT_PALETTE:
        assert colour in landing
    for colour in REMOVED_SATURATED_COLOURS:
        assert colour not in landing
    for asset in MERCHANT_ASSETS:
        assert asset in landing
    for asset in MERCHANT_ASSETS[:5]:
        assert landing.count(asset) >= 2

    assert "The right card, before you tap." in landing
    for section_id in ("radar", "answer", "flow", "privacy", "start"):
        assert f'id="{section_id}"' in landing
    for heading in SIGNATURE_HEADINGS:
        assert heading in landing


def test_landing_copy_is_truthful_and_accessible():
    landing = LANDING.read_text(encoding="utf-8")

    required_copy = (
        "Ask your AI agent which card to tap. KiasuMiles answers from the cards you actually own.",
        "Your AI agent handles your card list. KiasuMiles checks the rules.",
        "What your agent needs",
        "KiasuMiles never needs your card number, expiry date or CVV.",
        "How those names are remembered depends on your AI agent.",
        "UOB Preferred Visa",
        "uob-preferred-platinum-visa-card.png",
        "Apple Pay",
        "Example · sample cards",
        "kiasumiles-cold-storage-chat.jpg",
        "A real KiasuMiles recommendation for Cold Storage.",
        'width="1320" height="1157"',
        "kiasumiles-real-life-720.webp",
        "/privacy",
        "/health",
        "github.com/hosanxiv/kiasumiles",
        "t.me/kiasumilesbot",
        'aria-label="Copy KiasuMiles setup message"',
        'aria-live="polite"',
        "Copy didn't work. Select the message and copy it manually.",
    )
    for copy in required_copy:
        assert copy in landing

    assert "chatbot" not in landing.lower()
    for platform in ("ChatGPT", "Codex", "Claude", "OpenClaw", "Hermes"):
        assert platform not in landing
    assert "Supported agents" not in landing
    assert "keeps nothing" not in landing.lower()
    assert "stores nothing" not in landing.lower()
    assert "Open full-size screenshot" not in landing
    assert "A card worth 4 mpd at NTUC can drop to 1.4 on Grab." not in landing
    assert "can earn far less on Grab" in landing


def test_core_proof_images_load_without_waiting_for_lazy_scroll_activation():
    landing = LANDING.read_text(encoding="utf-8")

    proof_sources = (
        "/kiasumiles/assets/proof/kiasumiles-cold-storage-chat.jpg",
        "/kiasumiles/assets/proof/kiasumiles-real-life-1460.jpg",
    )
    for source in proof_sources:
        image_tag = re.search(rf'<img[^>]+src="{re.escape(source)}"[^>]*>', landing)
        assert image_tag is not None
        assert 'loading="lazy"' not in image_tag.group(0)


def test_landing_is_small_and_has_no_stale_or_internal_copy():
    landing_bytes = LANDING.read_bytes()
    landing = landing_bytes.decode("utf-8")

    assert len(landing_bytes) < 100_000
    for forbidden in FORBIDDEN:
        assert forbidden not in landing
    assert "KiasuMiles —" not in landing
    assert "Ask your agent which card to use." not in landing
    assert "Your agent or local client holds" not in landing


def test_readme_does_not_promote_a_landing_page_video_demo():
    readme = README.read_text(encoding="utf-8")

    assert "live landing page and 60s demo" not in readme
