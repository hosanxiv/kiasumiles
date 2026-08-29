from __future__ import annotations

import math
from datetime import date

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
    amount_sgd: float | None = None,
) -> dict:
    wallet_has_amaze = "amaze" in cards
    valid_ids = {c.card_id for c in _loader.cards()}
    skipped = [cid for cid in cards if cid not in valid_ids and cid != "amaze"]

    wallet_cards = [c for c in _loader.cards() if c.card_id in cards]
    if wallet_has_amaze and "citi_rewards_mc" in cards and "amaze_citi" not in cards:
        pairing = next((c for c in _loader.cards() if c.card_id == "amaze_citi"), None)
        if pairing:
            wallet_cards.append(pairing)
    top_n = 5

    record, is_exact = find_merchant(
        merchant, outlet, channel, _loader.merchants()
    )

    if record is None:
        fallback_mcc = infer_mcc_from_name(merchant) or CATEGORY_MCC.get((category or "").lower())
        if fallback_mcc:
            recommendations = rank_cards(
                fallback_mcc, wallet_cards, wallet_has_amaze, top_n,
                merchant_name=merchant, channel=channel,
                rate_mode="guaranteed", amount_sgd=amount_sgd,
            )
            conditional_recommendations = rank_cards(
                fallback_mcc, wallet_cards, wallet_has_amaze, top_n,
                merchant_name=merchant, channel=channel, amount_sgd=amount_sgd,
            )
            return {
                "merchant": merchant,
                "mcc": fallback_mcc,
                "merchant_matched": False,
                "routing_note": "No merchant data - routed by category inference. Verify before relying on this.",
                "recommendations": recommendations,
                "conditional_recommendations": conditional_recommendations,
                "recommendation_basis": "guaranteed_without_spend_progress",
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
    recommendations = rank_cards(
        record.mcc, wallet_cards, wallet_has_amaze, top_n, record.merchant_name,
        ranking_channel, rate_mode="guaranteed", amount_sgd=amount_sgd,
    )
    conditional_recommendations = rank_cards(
        record.mcc, wallet_cards, wallet_has_amaze, top_n, record.merchant_name,
        ranking_channel, amount_sgd=amount_sgd,
    )

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
        "conditional_recommendations": conditional_recommendations,
        "recommendation_basis": "guaranteed_without_spend_progress",
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
    amount_sgd: float | None = None,
) -> dict:
    if amount_sgd is not None and (
        not isinstance(amount_sgd, (int, float))
        or isinstance(amount_sgd, bool)
        or not math.isfinite(amount_sgd)
        or amount_sgd <= 0
    ):
        raise ValueError("amount_sgd must be a finite number greater than 0.")
    if not cards:
        return {
            "merchant": merchant,
            "merchant_matched": False,
            "message": "No cards were supplied. Ask which cards the user carries, then call this tool with those cards.",
            "recommendations": [],
            "wallet_configured": False,
            "wallet_stored": False,
            "skipped_cards": [],
            "data_version": data_version()["data_version"],
        }

    result = _lookup_for_cards(merchant, cards, outlet, channel, category, amount_sgd)
    result["wallet_stored"] = False
    result["data_version"] = data_version()["data_version"]
    return result


def compare_payment_methods(
    merchant: str,
    cards: list[str],
    amount_sgd: float | None = None,
    outlet: str | None = None,
    category: str | None = None,
) -> dict:
    direct_cards = [card for card in cards if card not in {"amaze", "amaze_citi"}]
    methods = []
    for payment_method in ("mobile_contactless", "contactless", "online"):
        result = lookup_hosted(
            merchant, direct_cards, outlet, payment_method, category, amount_sgd
        )
        methods.append({
            "payment_method": payment_method,
            "best_guaranteed": (result.get("recommendations") or [None])[0],
            "best_if_conditions_met": (result.get("conditional_recommendations") or [None])[0],
            "routing_note": result.get("routing_note"),
            "low_confidence_note": result.get("low_confidence_note"),
        })

    has_amaze_pair = "amaze" in cards and (
        "citi_rewards_mc" in cards or "amaze_citi" in cards
    )
    if has_amaze_pair:
        result = lookup_hosted(
            merchant, ["amaze", "amaze_citi"], outlet, "contactless", category, amount_sgd
        )
        methods.append({
            "payment_method": "amaze",
            "best_guaranteed": (result.get("recommendations") or [None])[0],
            "best_if_conditions_met": (result.get("conditional_recommendations") or [None])[0],
            "routing_note": result.get("routing_note"),
            "low_confidence_note": result.get("low_confidence_note"),
        })

    valid_ids = {c.card_id for c in _loader.cards()} | {"amaze"}
    return {
        "merchant": merchant,
        "amount_sgd": amount_sgd,
        "methods": methods,
        "wallet_stored": False,
        "skipped_cards": [card for card in cards if card not in valid_ids],
        "data_version": data_version()["data_version"],
    }


def changes_since(since: str, limit: int = 20) -> dict:
    try:
        date.fromisoformat(since)
    except (TypeError, ValueError) as exc:
        raise ValueError("since must be an ISO date in YYYY-MM-DD format.") from exc
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100.")
    changes = sorted(
        (change for change in _loader.changes() if change.changed_on >= since),
        key=lambda change: (change.changed_on, change.entity_name),
        reverse=True,
    )[:limit]
    return {
        "since": since,
        "changes": [
            {
                "changed_on": change.changed_on,
                "effective_on": change.effective_on or None,
                "entity_type": change.entity_type,
                "entity_name": change.entity_name,
                "change_type": change.change_type,
                "summary": change.summary,
            }
            for change in changes
        ],
        "data_version": data_version()["data_version"],
    }


def recommend_stack(cards: list[str], top_n: int = 3) -> dict:
    wallet_ids = cards
    valid_ids = {c.card_id for c in _loader.cards()}
    skipped = [cid for cid in wallet_ids if cid not in valid_ids]
    wallet_cards = [c for c in _loader.cards() if c.card_id in wallet_ids]
    wallet_has_amaze = "amaze" in wallet_ids

    if cards is not None and not wallet_ids:
        return {
            "wallet_configured": False,
            "wallet_cards": [],
            "skipped_cards": [],
            "coverage": [],
            "recommended_additions": [],
            "recommendation_scope": "supplied_cards_only",
            "message": "No cards were supplied. Ask which cards the user carries, then call this tool with those cards.",
        }

    coverage = []

    for category in _STACK_CATEGORIES:
        wallet_ranked = (
            rank_cards(
                category["mcc"],
                wallet_cards,
                wallet_has_amaze,
                1,
                merchant_name=category["sample_merchant"],
                channel=category["channel"],
            )
            if wallet_cards
            else []
        )

        current_best = wallet_ranked[0] if wallet_ranked else None
        current_rate = current_best["earn_rate_mpd"] if current_best else 0.0

        status = "covered"
        if not wallet_cards:
            status = "no_valid_cards"
        elif current_rate < 3.0:
            status = "weak"

        coverage.append({
            "category": category["category"],
            "sample_merchant": category["sample_merchant"],
            "mcc": category["mcc"],
            "channel": category["channel"],
            "status": status,
            "current_best": current_best,
            "mpd_gap": 0.0,
            "suggested_cards": [],
        })

    return {
        "wallet_configured": bool(wallet_ids),
        "wallet_cards": [
            c.card_name
            for c in wallet_cards
        ],
        "skipped_cards": skipped,
        "coverage": coverage,
        "recommended_additions": [],
        "recommendation_scope": "supplied_cards_only",
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
