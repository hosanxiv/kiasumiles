from __future__ import annotations

from .agent_contract import CATEGORY_MCC, hosted_agent_guide
from .data.loader import DataLoader
from .engine.merchant import find_merchant, infer_mcc_from_name
from .engine.router import rank_cards

_loader = DataLoader()

_STACK_CATEGORIES: tuple[dict[str, str], ...] = (
    {"category": "dining", "mcc": "5812", "channel": "mobile_contactless", "sample_merchant": "restaurant"},
    {"category": "fast_food", "mcc": "5814", "channel": "mobile_contactless", "sample_merchant": "fast food"},
    {"category": "grocery", "mcc": "5411", "channel": "mobile_contactless", "sample_merchant": "supermarket"},
    {"category": "online_shopping", "mcc": "5311", "channel": "online", "sample_merchant": "online shopping"},
    {"category": "pharmacy", "mcc": "5912", "channel": "mobile_contactless", "sample_merchant": "pharmacy"},
    {"category": "transport", "mcc": "4121", "channel": "online", "sample_merchant": "ride-hailing"},
    {"category": "travel", "mcc": "4722", "channel": "online", "sample_merchant": "travel booking"},
    {"category": "airlines", "mcc": "4511", "channel": "online", "sample_merchant": "airline booking"},
    {"category": "petrol", "mcc": "5541", "channel": "contactless", "sample_merchant": "petrol"},
)


def list_cards(bank: str | None = None) -> dict:
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


def _lookup_for_cards(
    merchant: str,
    cards: list[str],
    outlet: str | None = None,
    channel: str | None = None,
    category: str | None = None,
) -> dict:
    wallet_has_amaze = "amaze" in cards
    valid_ids = {c.card_id for c in _loader.cards()}
    skipped = [cid for cid in cards if cid not in valid_ids]

    wallet_cards = (
        [c for c in _loader.cards() if c.card_id in cards]
        if cards
        else _loader.cards()
    )
    top_n = 5

    record, is_exact = find_merchant(
        merchant, outlet, channel, _loader.merchants()
    )

    if record is None:
        fallback_mcc = infer_mcc_from_name(merchant) or CATEGORY_MCC.get((category or "").lower())
        if fallback_mcc:
            recommendations = rank_cards(
                fallback_mcc, wallet_cards, wallet_has_amaze, top_n,
                merchant_name=merchant, channel=None,
            )
            return {
                "merchant": merchant,
                "mcc": fallback_mcc,
                "merchant_matched": False,
                "routing_note": "No merchant data - routed by category inference. Verify before relying on this.",
                "recommendations": recommendations,
                "wallet_configured": bool(cards),
                "skipped_cards": skipped,
            }
        return {
            "merchant": merchant,
            "merchant_matched": False,
            "message": f"No data found for '{merchant}'. Try passing category: dining, grocery, transport, petrol, pharmacy.",
            "wallet_configured": bool(cards),
            "skipped_cards": skipped,
        }

    low_confidence_note = (
        "Limited data - verify before relying on this."
        if record.confidence == "low"
        else None
    )

    ranking_channel = channel or record.channel
    recommendations = rank_cards(record.mcc, wallet_cards, wallet_has_amaze, top_n, record.merchant_name, ranking_channel)

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
        "wallet_configured": bool(cards),
        "merchant_matched": is_exact,
        "skipped_cards": skipped,
    }


def lookup_hosted(
    merchant: str,
    cards: list[str],
    outlet: str | None = None,
    channel: str | None = None,
    category: str | None = None,
) -> dict:
    result = _lookup_for_cards(merchant, cards, outlet, channel, category)
    result["wallet_stored"] = False
    result["data_version"] = data_version()["data_version"]
    return result


def recommend_stack(cards: list[str], top_n: int = 3) -> dict:
    wallet_ids = cards
    valid_ids = {c.card_id for c in _loader.cards()}
    skipped = [cid for cid in wallet_ids if cid not in valid_ids]
    wallet_cards = [c for c in _loader.cards() if c.card_id in wallet_ids]
    wallet_has_amaze = "amaze" in wallet_ids
    all_cards = _loader.cards()

    coverage = []
    additions_by_card: dict[str, dict] = {}

    for category in _STACK_CATEGORIES:
        wallet_ranked = rank_cards(
            category["mcc"],
            wallet_cards,
            wallet_has_amaze,
            1,
            merchant_name=category["sample_merchant"],
            channel=category["channel"],
        ) if wallet_cards else []
        market_ranked = rank_cards(
            category["mcc"],
            all_cards,
            wallet_has_amaze,
            8,
            merchant_name=category["sample_merchant"],
            channel=category["channel"],
        )

        current_best = wallet_ranked[0] if wallet_ranked else None
        market_best = market_ranked[0] if market_ranked else None
        current_rate = current_best["earn_rate_mpd"] if current_best else 0.0
        market_rate = market_best["earn_rate_mpd"] if market_best else 0.0
        gap = round(max(market_rate - current_rate, 0.0), 4)

        status = "covered"
        if not wallet_cards:
            status = "no_wallet"
        elif current_rate < 3.0 and market_rate >= 3.0:
            status = "weak"
        elif gap >= 1.0:
            status = "upgrade_available"

        suggested = [
            r for r in market_ranked
            if r["card_id"] not in wallet_ids and r["earn_rate_mpd"] > current_rate
        ][:top_n]

        coverage.append({
            "category": category["category"],
            "sample_merchant": category["sample_merchant"],
            "mcc": category["mcc"],
            "channel": category["channel"],
            "status": status,
            "current_best": current_best,
            "market_best": market_best,
            "mpd_gap": gap,
            "suggested_cards": suggested,
        })

        if status != "covered":
            for suggestion in suggested:
                entry = additions_by_card.setdefault(
                    suggestion["card_id"],
                    {
                        "card_id": suggestion["card_id"],
                        "card_name": suggestion["card_name"],
                        "helps_categories": [],
                        "best_earn_rate_mpd": suggestion["earn_rate_mpd"],
                        "reason_summary": suggestion["reason_summary"],
                    },
                )
                entry["helps_categories"].append(category["category"])
                entry["best_earn_rate_mpd"] = max(entry["best_earn_rate_mpd"], suggestion["earn_rate_mpd"])

    additions = sorted(
        additions_by_card.values(),
        key=lambda item: (len(item["helps_categories"]), item["best_earn_rate_mpd"]),
        reverse=True,
    )[:top_n]

    return {
        "wallet_configured": bool(wallet_ids),
        "wallet_cards": [
            c.card_name
            for c in wallet_cards
        ],
        "skipped_cards": skipped,
        "coverage": coverage,
        "recommended_additions": additions,
    }


def data_version() -> dict:
    card_dates = [c.last_verified for c in _loader.cards() if c.last_verified]
    merchant_dates = [m.last_verified for m in _loader.merchants() if m.last_verified]
    all_dates = card_dates + merchant_dates
    return {
        "data_version": max(all_dates) if all_dates else "unknown",
        "cards": len(_loader.cards()),
        "merchants": len(_loader.merchants()),
        "data_backend": _loader.backend_name(),
    }


def guide() -> dict:
    return hosted_agent_guide()
