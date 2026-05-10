from __future__ import annotations
from ..data.loader import CardRule


def _merchant_eligible(rule: CardRule, merchant_name: str | None) -> bool:
    """Return False if card has merchant restrictions and this merchant doesn't qualify."""
    if not rule.eligible_merchants or not merchant_name:
        return True
    name_lower = merchant_name.lower()
    return any(m.lower() in name_lower or name_lower in m.lower() for m in rule.eligible_merchants)


def _channel_eligible(rule: CardRule, channel: str | None) -> bool:
    """Return False if card has channel restrictions and this merchant's channel doesn't qualify.

    Merchant channel "any" is treated as a wildcard — the merchant accepts multiple payment
    methods and the user can choose the qualifying one. Most SG physical merchants are
    tagged "any", so strict matching would under-recommend cards that only earn on
    online/contactless. Optimistic match aligns with how SG payments actually work.
    """
    if not rule.eligible_channels:
        return True
    if not channel or channel.lower() == "any":
        return True
    return channel.lower() in [c.lower() for c in rule.eligible_channels]


def effective_mpd(
    rule: CardRule,
    mcc: str,
    wallet_has_amaze: bool,
    merchant_name: str | None = None,
    channel: str | None = None,
) -> float:
    """Calculate net miles per dollar for this card at this MCC."""
    if rule.card_id == "amaze":
        return 0.0

    if rule.requires_amaze:
        if not wallet_has_amaze:
            return rule.base_rate_mpd
        if rule.eligible_mccs and mcc not in rule.eligible_mccs:
            return rule.base_rate_mpd
        if not _merchant_eligible(rule, merchant_name):
            return rule.base_rate_mpd
        if not _channel_eligible(rule, channel):
            return rule.base_rate_mpd
        fee_multiplier = 1.0 - (rule.amaze_fee_pct / 100.0)
        return rule.earn_rate_mpd * fee_multiplier

    if not rule.eligible_mccs or mcc in rule.eligible_mccs:
        if not _merchant_eligible(rule, merchant_name):
            return rule.base_rate_mpd
        if not _channel_eligible(rule, channel):
            return rule.base_rate_mpd
        return rule.earn_rate_mpd

    return rule.base_rate_mpd


def rank_cards(
    mcc: str,
    card_rules: list[CardRule],
    wallet_has_amaze: bool,
    top_n: int,
    merchant_name: str | None = None,
    channel: str | None = None,
) -> list[dict]:
    """Rank cards by effective mpd for a given MCC. Returns top_n results."""
    scored = []
    for rule in card_rules:
        if rule.card_id == "amaze":
            continue
        mpd = effective_mpd(rule, mcc, wallet_has_amaze, merchant_name, channel)
        scored.append({
            "card_id": rule.card_id,
            "card_name": rule.card_name,
            "earn_rate_mpd": round(mpd, 4),
            "cap_sgd": rule.cap_sgd,
            "cap_period": rule.cap_period,
            "caveat": rule.caveat or None,
            "last_verified": rule.last_verified or None,
            "earn_block_sgd": rule.earn_block_sgd,
        })

    scored.sort(key=lambda x: x["earn_rate_mpd"], reverse=True)
    return scored[:top_n]
