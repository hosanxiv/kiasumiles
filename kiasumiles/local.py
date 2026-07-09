from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from . import client_wallet
from .agent_contract import LOCAL_TOOL_DESCRIPTIONS, local_agent_guide
from .hosted_client import HostedClient, HostedServiceError


mcp = FastMCP("KiasuMiles Local")
_client = HostedClient()


def _normalize_cards(cards: list[str]) -> list[str]:
    normalized = []
    for card in cards:
        value = card.strip()
        if value.lower() in {"amaze", "amaze (instarem)"}:
            value = "amaze"
        normalized.append(value)
    return normalized


def _display_cards(cards: list[str], resolved: list[str]) -> list[str]:
    display = list(resolved)
    if "amaze" in _normalize_cards(cards) and "Amaze (Instarem)" not in display:
        display.append("Amaze (Instarem)")
    return display


def _load_wallet_result() -> tuple[list[str], dict[str, Any] | None]:
    try:
        return client_wallet.load_wallet(), None
    except client_wallet.WalletFileError:
        return [], {
            "wallet_configured": False,
            "message": "Your local KiasuMiles wallet could not be read. Please configure it again.",
        }


def kiasumiles_list_cards(bank: str | None = None) -> dict[str, Any]:
    try:
        return _client.list_cards(bank)
    except HostedServiceError:
        return {"cards": [], "message": "KiasuMiles is temporarily unavailable. Try again shortly."}


def kiasumiles_configure(cards: list[str]) -> dict[str, Any]:
    wallet, _ = _load_wallet_result()
    if not cards:
        return {
            "wallet_configured": bool(wallet),
            "wallet_changed": False,
            "message": "No cards were supplied, so the local wallet was not changed.",
        }

    normalized = _normalize_cards(cards)
    try:
        inspection = _client.inspect_wallet(normalized)
    except HostedServiceError:
        return {
            "wallet_configured": bool(wallet),
            "wallet_changed": False,
            "message": "KiasuMiles is temporarily unavailable, so the local wallet was not changed.",
        }

    if inspection["unmatched_cards"]:
        return {
            "wallet_configured": bool(wallet),
            "wallet_changed": False,
            "message": "Some cards could not be matched. The existing local wallet was not changed.",
            "unmatched_cards": inspection["unmatched_cards"],
        }

    saved_cards = _display_cards(normalized, inspection["cards"])
    try:
        client_wallet.save_wallet(saved_cards)
    except client_wallet.WalletFileError:
        return {
            "wallet_configured": bool(wallet),
            "wallet_changed": False,
            "message": "The local KiasuMiles wallet could not be saved on this device.",
        }
    return {
        "saved_cards": saved_cards,
        "wallet_configured": True,
        "wallet_stored_locally": True,
    }


def kiasumiles_get_wallet() -> dict[str, Any]:
    wallet, error = _load_wallet_result()
    if error:
        return error
    if not wallet:
        return {
            "cards": [],
            "wallet_configured": False,
            "message": "No local wallet is configured yet.",
        }
    try:
        inspection = _client.inspect_wallet(_normalize_cards(wallet))
    except HostedServiceError:
        return {
            "cards": [],
            "card_count": len(wallet),
            "wallet_configured": True,
            "wallet_stored_locally": True,
            "message": "Your wallet is saved locally, but card names could not be refreshed right now.",
        }
    return {
        "cards": _display_cards(wallet, inspection["cards"]),
        "wallet_configured": True,
        "wallet_stored_locally": True,
    }


def kiasumiles_lookup(
    merchant: str,
    outlet: str | None = None,
    channel: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    wallet, error = _load_wallet_result()
    if error:
        return {**error, "recommendations": []}
    if not wallet:
        return {
            "merchant": merchant,
            "wallet_configured": False,
            "wallet_stored_locally": False,
            "recommendations": [],
            "message": "Set up your KiasuMiles wallet once before asking which card to use.",
        }
    try:
        result = _client.lookup(merchant, _normalize_cards(wallet), outlet, channel, category)
    except HostedServiceError:
        return {
            "merchant": merchant,
            "wallet_configured": True,
            "wallet_stored_locally": True,
            "recommendations": [],
            "message": "KiasuMiles is temporarily unavailable. Your local wallet is unchanged.",
        }
    result["wallet_configured"] = True
    result["wallet_stored_locally"] = True
    return result


def kiasumiles_recommend_stack(top_n: int = 3) -> dict[str, Any]:
    wallet, error = _load_wallet_result()
    if error:
        return error
    if not wallet:
        return {
            "wallet_configured": False,
            "coverage": [],
            "message": "Set up your KiasuMiles wallet before reviewing your card stack.",
        }
    try:
        result = _client.recommend_stack(_normalize_cards(wallet), top_n)
    except HostedServiceError:
        return {
            "wallet_configured": True,
            "wallet_stored_locally": True,
            "coverage": [],
            "message": "KiasuMiles is temporarily unavailable. Your local wallet is unchanged.",
        }
    result["wallet_configured"] = True
    result["wallet_stored_locally"] = True
    return result


def kiasumiles_data_version() -> dict[str, Any]:
    try:
        return _client.data_version()
    except HostedServiceError:
        return {"status": "unavailable", "message": "KiasuMiles is temporarily unavailable."}


def kiasumiles_agent_guide() -> dict[str, Any]:
    return local_agent_guide()


for _name, _description in LOCAL_TOOL_DESCRIPTIONS.items():
    _tool = globals()[_name]
    _tool.__doc__ = _description
    globals()[_name] = mcp.tool()(_tool)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
