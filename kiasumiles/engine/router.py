from __future__ import annotations
from ..data.loader import CardRule


_PERIOD_LABELS = {
    "calendar_month": "calendar month",
    "statement_month": "statement month",
}


def _cap_summary(rule: CardRule) -> str:
    period = _PERIOD_LABELS.get(rule.cap_period, rule.cap_period)
    has_cap = rule.cap_sgd is not None
    has_blocks = rule.earn_block_sgd > 1
    block_str = f" · earns in S${rule.earn_block_sgd:g} blocks" if has_blocks else ""
    if has_cap:
        return f"S${rule.cap_sgd:,.0f} cap / {period}{block_str}"
    return f"No cap{block_str}"


def _merchant_eligible(rule: CardRule, merchant_name: str | None) -> bool:
    """Return False if card has merchant restrictions and this merchant doesn't qualify."""
    if not rule.eligible_merchants or not merchant_name:
        return True
    name_lower = merchant_name.lower()
    return any(m.lower() in name_lower or name_lower in m.lower() for m in rule.eligible_merchants)


def _channel_eligible(rule: CardRule, channel: str | None) -> bool:
    """Return False if card has channel restrictions and this merchant's channel doesn't qualify.

    Merchant channel "any" means the physical merchant accepts multiple payment methods.
    For cards that include "contactless", the user can tap and earn — treated as eligible.
    For cards restricted to "online" only (web/app payments), "any" physical merchants do
    NOT qualify: in-person POS is not an online transaction even with NFC.
    """
    if not rule.eligible_channels:
        return True
    eligible_lower = [c.lower() for c in rule.eligible_channels]
    if not channel or channel.lower() == "any":
        return "contactless" in eligible_lower
    return channel.lower() in eligible_lower


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
            "cap_summary": _cap_summary(rule),
            "min_spend_sgd": rule.min_spend if rule.min_spend else None,
            "caveat": rule.caveat or None,
            "last_verified": rule.last_verified or None,
            "earn_block_sgd": rule.earn_block_sgd,
        })

    scored.sort(key=lambda x: x["earn_rate_mpd"], reverse=True)
    return scored[:top_n]
