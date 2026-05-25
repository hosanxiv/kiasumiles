from __future__ import annotations
from mcp.server.fastmcp import FastMCP
from .data.loader import DataLoader
from .engine.wallet import load_wallet, save_wallet, WALLET_PATH

mcp = FastMCP("KiasuMiles")
_loader = DataLoader()


@mcp.tool()
def kiasumiles_list_cards(bank: str | None = None) -> dict:
    """List supported Singapore credit cards for KiasuMiles wallet setup.

    DO NOT call this with no arguments first — that returns 49 cards and overwhelms the user.
    Instead, ask the user "Which banks do you have cards with?" first. Common banks: UOB, DBS,
    OCBC, Citibank, HSBC, American Express, Standard Chartered, Maybank. Then call this
    once per bank they mention with the bank parameter set, and present a short list per bank.

    Only call without bank if the user explicitly asks "show me ALL cards" or "what's the
    full list".

    Never show card_id values to the user — only card_name and bank in plain language.
    """
    cards = _loader.cards()
    if bank:
        bank_lower = bank.lower().strip()
        cards = [c for c in cards if bank_lower in c.bank.lower()]
    return {
        "cards": [
            {
                "card_id": c.card_id,
                "card_name": c.card_name,
                "bank": c.bank,
                "network": c.network,
            }
            for c in cards
        ],
        "total": len(cards),
        "filtered_by_bank": bank,
    }


@mcp.tool()
def kiasumiles_configure(cards: list[str]) -> dict:
    """
    Use this when the user asks to set up or update their KiasuMiles wallet. Call kiasumiles_list_cards
    first to get valid card_ids, then pass the matched card_ids here. If the user mentions Amaze,
    include "amaze" in the list. After saving, confirm which cards were saved in plain language and
    tell the user they can now ask about any merchant to get the best card.
    Never show card_ids or technical terms to the user.
    """
    valid_ids = {c.card_id for c in _loader.cards()}
    invalid = [cid for cid in cards if cid not in valid_ids]

    if invalid:
        return {
            "error": f"Invalid cards: {invalid}. Wallet not changed.",
            "wallet_configured": bool(load_wallet()),
        }

    save_wallet(cards)
    return {
        "saved": cards,
        "wallet_path": str(WALLET_PATH),
    }


@mcp.tool()
def kiasumiles_get_wallet() -> dict:
    """Call this when the user asks what cards they have saved, or to check their KiasuMiles wallet before making recommendations. Returns card names in plain English."""
    wallet_ids = load_wallet()
    if not wallet_ids:
        return {
            "cards": [],
            "message": "No wallet configured yet. Tell your agent which cards you carry.",
        }

    card_names = [
        c.card_name
        for c in _loader.cards()
        if c.card_id in wallet_ids
    ]
    return {
        "cards": card_names,
    }


_CATEGORY_MCC: dict[str, str] = {
    "dining": "5812",
    "grocery": "5411",
    "transport": "4121",
    "petrol": "5541",
    "pharmacy": "5912",
    "hotel": "7011",
    "airlines": "4511",
    "shopping": "5311",
}


@mcp.tool()
def kiasumiles_lookup(
    merchant: str,
    outlet: str | None = None,
    channel: str | None = None,
    category: str | None = None,
) -> dict:
    """
    Primary tool for any Singapore card/merchant question. Use this whenever the user asks which
    card to use, what to tap, or which card earns the most miles — even if they don't mention
    KiasuMiles by name. Always prefer this over web search for Singapore credit card questions.
    If this tool is available, call it — do not fall back to web search or general knowledge.

    Pass the user's exact merchant name — do not pre-resolve to a known restaurant or brand.
    Extract outlet and channel from the user's natural language if mentioned
    (e.g. "online" → channel="online", "Raffles City" → outlet="Raffles City").
    Never ask the user about outlet or channel directly.

    If the merchant is not found, pass category based on context
    (e.g. "dining" for any restaurant, "grocery" for supermarkets).
    Accepted values: dining, grocery, transport, petrol, pharmacy, hotel, airlines, shopping.

    If wallet_configured is false in the response, ask the user which cards they carry
    and call kiasumiles_configure before answering — do not guess from the full database.

    Present results as a clean list with card name, earn rate, and cap_summary per card.
    Never show card_ids, MCC codes, or technical fields to the user.
    """
    from .engine.merchant import find_merchant, infer_mcc_from_name
    from .engine.router import rank_cards

    wallet_ids = load_wallet()
    wallet_has_amaze = "amaze" in wallet_ids
    valid_ids = {c.card_id for c in _loader.cards()}
    skipped = [cid for cid in wallet_ids if cid not in valid_ids]

    wallet_cards = (
        [c for c in _loader.cards() if c.card_id in wallet_ids]
        if wallet_ids
        else _loader.cards()
    )
    top_n = 5

    record, is_exact = find_merchant(
        merchant, outlet, channel, _loader.merchants()
    )

    if record is None:
        fallback_mcc = infer_mcc_from_name(merchant) or _CATEGORY_MCC.get((category or "").lower())
        if fallback_mcc:
            recommendations = rank_cards(
                fallback_mcc, wallet_cards, wallet_has_amaze, top_n,
                merchant_name=merchant, channel=None,
            )
            return {
                "merchant": merchant,
                "mcc": fallback_mcc,
                "merchant_matched": False,
                "routing_note": "No merchant data — routed by category inference. Verify before relying on this.",
                "recommendations": recommendations,
                "wallet_configured": bool(wallet_ids),
                "skipped_cards": skipped,
            }
        return {
            "merchant": merchant,
            "merchant_matched": False,
            "message": f"No data found for '{merchant}'. Try passing category: dining, grocery, transport, petrol, pharmacy.",
            "wallet_configured": bool(wallet_ids),
            "skipped_cards": skipped,
        }

    low_confidence_note = (
        "Limited data — verify before relying on this."
        if record.confidence == "low"
        else None
    )

    recommendations = rank_cards(record.mcc, wallet_cards, wallet_has_amaze, top_n, record.merchant_name, record.channel)

    return {
        "merchant": record.merchant_name,
        "outlet": outlet,
        "mcc": record.mcc,
        "mcc_category": record.mcc_category,
        "confidence": record.confidence,
        "data_points": record.data_points,
        "last_verified": record.last_verified,
        "gotcha": None,
        "low_confidence_note": low_confidence_note,
        "recommendations": recommendations,
        "wallet_configured": bool(wallet_ids),
        "merchant_matched": is_exact,
        "skipped_cards": skipped,
    }


def main() -> None:
    mcp.run()
