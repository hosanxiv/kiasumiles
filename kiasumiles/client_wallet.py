from __future__ import annotations

from pathlib import Path

import yaml


WALLET_PATH = Path.home() / ".kiasumiles" / "wallet.yaml"


class WalletFileError(ValueError):
    pass


def _validated_cards(data: object) -> list[str]:
    if data is None:
        return []
    if not isinstance(data, dict):
        raise WalletFileError("The local KiasuMiles wallet must contain a cards list.")

    cards = data.get("cards")
    if cards is None:
        return []
    if not isinstance(cards, list) or any(not isinstance(card, str) for card in cards):
        raise WalletFileError("The local KiasuMiles wallet cards must be a list of names.")
    return cards


def load_wallet(path: Path | None = None) -> list[str]:
    wallet_path = path or WALLET_PATH
    if not wallet_path.exists():
        return []
    try:
        data = yaml.safe_load(wallet_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise WalletFileError("The local KiasuMiles wallet could not be read.") from exc
    return _validated_cards(data)


def save_wallet(cards: list[str], path: Path | None = None) -> Path:
    wallet_path = path or WALLET_PATH
    _validated_cards({"cards": cards})
    try:
        wallet_path.parent.mkdir(parents=True, exist_ok=True)
        wallet_path.write_text(
            yaml.safe_dump({"cards": cards}, sort_keys=False),
            encoding="utf-8",
        )
    except OSError as exc:
        raise WalletFileError("The local KiasuMiles wallet could not be saved.") from exc
    return wallet_path
