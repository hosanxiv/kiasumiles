from __future__ import annotations
from pathlib import Path
import yaml

WALLET_PATH = Path.home() / ".kiasumiles" / "wallet.yaml"


def load_wallet() -> list[str]:
    """Load card IDs from wallet.yaml. Returns empty list if file not found."""
    if not WALLET_PATH.exists():
        return []
    data = yaml.safe_load(WALLET_PATH.read_text(encoding="utf-8")) or {}
    return data.get("cards") or []


def save_wallet(card_ids: list[str]) -> Path:
    """Save card IDs to wallet.yaml. Creates parent dirs if needed."""
    WALLET_PATH.parent.mkdir(parents=True, exist_ok=True)
    content = "# KiasuMiles wallet - edit card IDs here or ask your agent to reconfigure\ncards:\n"
    content += "".join(f"  - {cid}\n" for cid in card_ids)
    WALLET_PATH.write_text(content, encoding="utf-8")
    return WALLET_PATH
