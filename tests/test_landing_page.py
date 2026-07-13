from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LANDING = ROOT / "kiasumiles" / "static" / "kiasumiles" / "index.html"
README = ROOT / "README.md"

CURRENT_PALETTE = (
    "#061427",
    "#1168ff",
    "#2bd6ad",
    "#5fb43a",
    "#b7e76a",
    "#003f37",
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
    "It recognises the merchant, not just the category.",
    "Your cards. One answer.",
    "Ask. Get an answer.",
    "Two steps. Then just ask.",
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
    for asset in MERCHANT_ASSETS:
        assert asset in landing

    assert "The right card, before you tap." in landing
    for section_id in ("radar", "answer", "flow", "privacy", "start"):
        assert f'id="{section_id}"' in landing
    for heading in SIGNATURE_HEADINGS:
        assert heading in landing


def test_landing_copy_is_truthful_and_accessible():
    landing = LANDING.read_text(encoding="utf-8")

    required_copy = (
        "UOB Preferred Visa",
        "Apple Pay",
        "Example using a demo card stack",
        "kiasumiles-real-life-720.webp",
        "/privacy",
        "/health",
        "github.com/hosanxiv/kiasumiles",
        "t.me/kiasumilesbot",
        'aria-label="Copy KiasuMiles setup prompt"',
        'aria-live="polite"',
        "Copy failed. Select the prompt and copy it manually.",
    )
    for copy in required_copy:
        assert copy in landing


def test_landing_is_small_and_has_no_stale_or_internal_copy():
    landing_bytes = LANDING.read_bytes()
    landing = landing_bytes.decode("utf-8")

    assert len(landing_bytes) < 100_000
    for forbidden in FORBIDDEN:
        assert forbidden not in landing


def test_readme_does_not_promote_a_landing_page_video_demo():
    readme = README.read_text(encoding="utf-8")

    assert "live landing page and 60s demo" not in readme
