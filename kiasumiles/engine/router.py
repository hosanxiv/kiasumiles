from __future__ import annotations
from ..data.loader import CardRule


def effective_mpd(rule: CardRule, mcc: str, wallet_has_amaze: bool) -> float:
    """Calculate net miles per dollar for this card at this MCC."""
    if rule.card_id == "amaze":
        return 0.0

    if rule.requires_amaze:
        if not wallet_has_amaze:
            return rule.base_rate_mpd
        if rule.eligible_mccs and mcc not in rule.eligible_mccs:
            return rule.base_rate_mpd
        fee_multiplier = 1.0 - (rule.amaze_fee_pct / 100.0)
        return rule.earn_rate_mpd * fee_multiplier

    if not rule.eligible_mccs or mcc in rule.eligible_mccs:
        return rule.earn_rate_mpd

    return rule.base_rate_mpd


def rank_cards(
    mcc: str,
    card_rules: list[CardRule],
    wallet_has_amaze: bool,
    top_n: int,
) -> list[dict]:
    """Rank cards by effective mpd for a given MCC. Returns top_n results."""
    scored = []
    for rule in card_rules:
        if rule.card_id == "amaze":
            continue
        mpd = effective_mpd(rule, mcc, wallet_has_amaze)
        scored.append({
            "card_id": rule.card_id,
            "card_name": rule.card_name,
            "earn_rate_mpd": round(mpd, 4),
            "cap_sgd": rule.cap_sgd,
            "cap_period": rule.cap_period,
        })

    scored.sort(key=lambda x: x["earn_rate_mpd"], reverse=True)
    return scored[:top_n]
