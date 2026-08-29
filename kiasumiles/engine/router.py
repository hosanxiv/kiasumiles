from __future__ import annotations
import math
from ..data.loader import CardRule


_PERIOD_LABELS = {
    "calendar_month": "calendar month",
    "statement_month": "statement month",
}

_CITI_REWARDS_OFFLINE_MCCS = {
    "5311",  # department stores
    "5331",  # variety stores
    "5399",  # miscellaneous general merchandise
    "5611",  # men's and boys' clothing
    "5621",  # women's ready-to-wear
    "5631",  # women's accessory and specialty shops
    "5641",  # children's and infants' wear
    "5651",  # family clothing stores
    "5655",  # sports apparel
    "5661",  # shoe stores
    "5691",  # men's and women's clothing stores
    "5697",  # alteration/tailor shops
    "5699",  # miscellaneous apparel and accessory shops
    "5948",  # luggage and leather goods
}


def _cap_summary(rule: CardRule) -> str:
    period = _PERIOD_LABELS.get(rule.cap_period, rule.cap_period)
    has_cap = rule.cap_sgd is not None
    has_blocks = rule.earn_block_sgd > 1
    block_str = f" · earns in S${rule.earn_block_sgd:g} blocks" if has_blocks else ""
    if has_cap:
        cap = f"{rule.cap_sgd:,.2f}".rstrip("0").rstrip(".")
        return f"S${cap} cap / {period}{block_str}"
    return f"No cap{block_str}"


def _merchant_eligible(rule: CardRule, merchant_name: str | None) -> bool:
    """Return False if card has merchant restrictions and this merchant doesn't qualify."""
    if not rule.eligible_merchants or not merchant_name:
        return True
    name_lower = merchant_name.lower()
    return any(m.lower() in name_lower or name_lower in m.lower() for m in rule.eligible_merchants)


def _channel_eligible(rule: CardRule, channel: str | None, mcc: str | None = None) -> bool:
    """Return False if card has channel restrictions and this merchant's channel doesn't qualify.

    Merchant channel "any" means the physical merchant accepts multiple payment methods.
    For cards that include "contactless", the user can tap and earn — treated as eligible.
    For cards restricted to "online" only (web/app payments), "any" physical merchants do
    NOT qualify: in-person POS is not an online transaction even with NFC.
    """
    if not rule.eligible_channels:
        return True
    eligible_lower = [c.lower() for c in rule.eligible_channels]
    channel_lower = channel.lower() if channel else None
    if (
        rule.card_id == "citi_rewards_mc"
        and channel_lower in {"any", "contactless", "mobile_contactless"}
        and mcc not in _CITI_REWARDS_OFFLINE_MCCS
    ):
        return False
    if not channel or channel.lower() == "any":
        return "contactless" in eligible_lower
    if channel.lower() == "mobile_contactless" and "contactless" in eligible_lower:
        return True
    return channel.lower() in eligible_lower


def _channel_label(channel: str) -> str:
    labels = {
        "mobile_contactless": "mobile contactless",
        "contactless": "contactless",
        "online": "online",
        "app": "in-app",
        "fcy": "foreign currency",
        "petrol": "petrol",
    }
    return labels.get(channel, channel.replace("_", " "))


def _rule_diagnostics(
    rule: CardRule,
    mcc: str,
    wallet_has_amaze: bool,
    merchant_name: str | None = None,
    channel: str | None = None,
) -> tuple[float, list[str], list[str], list[str]]:
    """Return effective mpd plus explainability fields for a rule."""
    if rule.card_id == "amaze":
        return 0.0, ["stored_value_card"], ["Amaze itself does not earn miles."], []

    reason_codes: list[str] = []
    reasons: list[str] = []
    gotchas: list[str] = []

    if rule.requires_amaze and not wallet_has_amaze:
        reason_codes.append("requires_amaze_missing")
        gotchas.append("Needs Amaze pairing to unlock this bonus rate.")
        return rule.base_rate_mpd, reason_codes, reasons, gotchas

    if rule.eligible_mccs:
        if mcc in rule.eligible_mccs:
            reason_codes.append("mcc_eligible")
            reasons.append("merchant category is eligible")
        else:
            reason_codes.append("mcc_not_eligible")
            gotchas.append("Merchant category is outside this card's bonus whitelist.")
            return rule.base_rate_mpd, reason_codes, reasons, gotchas
    else:
        reason_codes.append("no_mcc_restriction")
        reasons.append("card has no merchant-category restriction")

    if rule.eligible_merchants:
        if _merchant_eligible(rule, merchant_name):
            reason_codes.append("merchant_eligible")
            reasons.append("merchant is in this card's eligible merchant list")
        else:
            reason_codes.append("merchant_not_eligible")
            gotchas.append("Bonus rate only applies at this card's named partner merchants.")
            return rule.base_rate_mpd, reason_codes, reasons, gotchas

    if rule.eligible_channels:
        if _channel_eligible(rule, channel, mcc):
            reason_codes.append("channel_eligible")
            if channel and channel.lower() != "any":
                reasons.append(f"{_channel_label(channel.lower())} payment qualifies")
            else:
                reasons.append("payment channel qualifies")
        else:
            reason_codes.append("channel_not_eligible")
            if (
                rule.card_id == "citi_rewards_mc"
                and channel
                and channel.lower() in {"any", "contactless", "mobile_contactless"}
                and mcc not in _CITI_REWARDS_OFFLINE_MCCS
            ):
                gotchas.append("Offline Citi Rewards bonus is limited to shopping-like categories; this merchant may fall to base rate.")
            else:
                channel_list = ", ".join(_channel_label(c.lower()) for c in rule.eligible_channels)
                gotchas.append(f"Needs {channel_list}; this payment channel may fall to base rate.")
            return rule.base_rate_mpd, reason_codes, reasons, gotchas

    if rule.requires_amaze:
        reason_codes.append("amaze_pairing_applied")
        reasons.append("Amaze pairing is available")
        fee_multiplier = 1.0 - (rule.amaze_fee_pct / 100.0)
        mpd = rule.earn_rate_mpd * fee_multiplier
    else:
        mpd = rule.earn_rate_mpd

    reason_codes.append("bonus_rate_applied")
    if rule.cap_sgd is not None:
        reason_codes.append("monthly_cap_applies")
        reasons.append(_cap_summary(rule))
    if rule.min_spend:
        reason_codes.append("min_spend_applies")
        gotchas.append(f"Requires at least S${rule.min_spend:g} spend before the bonus is reliable.")

    return mpd, reason_codes, reasons, gotchas


def _reason_summary(card_name: str, mpd: float, reasons: list[str], gotchas: list[str]) -> str:
    if mpd <= 0:
        return f"{card_name} does not earn miles for this transaction."
    if gotchas and not reasons:
        return f"{card_name} falls back to base rate because {gotchas[0][0].lower() + gotchas[0][1:]}"
    if reasons:
        return f"{card_name} earns {mpd:g} mpd because " + " and ".join(reasons[:2]) + "."
    return f"{card_name} earns {mpd:g} mpd for this transaction."


def _condition_summary(rule: CardRule) -> str | None:
    conditions = []
    if rule.min_spend:
        conditions.append(f"S${rule.min_spend:g} minimum spend")
    if rule.cap_sgd is not None:
        conditions.append(_cap_summary(rule))
    return " · ".join(conditions) or None


def _rounded_miles(rule: CardRule, amount_sgd: float, rate_mpd: float) -> float:
    if amount_sgd <= 0:
        return 0.0
    if rule.card_id == "dbs_wwmc" and rate_mpd > rule.base_rate_mpd:
        base = math.floor(amount_sgd * rule.base_rate_mpd / 2) * 2
        bonus = math.floor(amount_sgd * (rate_mpd - rule.base_rate_mpd) / 2) * 2
        return float(base + bonus)
    if rule.bank == "DBS" and rule.card_id != "dbs_yuu_visa":
        return float(math.floor(amount_sgd * rate_mpd / 2) * 2)
    eligible_spend = math.floor(amount_sgd / rule.earn_block_sgd) * rule.earn_block_sgd
    return round(eligible_spend * rate_mpd, 2)


def _estimated_miles(rule: CardRule, amount_sgd: float, rate_mpd: float) -> float:
    if rate_mpd > rule.base_rate_mpd and rule.cap_sgd is not None:
        bonus_spend = min(amount_sgd, rule.cap_sgd)
        return round(
            _rounded_miles(rule, bonus_spend, rate_mpd)
            + _rounded_miles(rule, amount_sgd - bonus_spend, rule.base_rate_mpd),
            2,
        )
    return _rounded_miles(rule, amount_sgd, rate_mpd)


def effective_mpd(
    rule: CardRule,
    mcc: str,
    wallet_has_amaze: bool,
    merchant_name: str | None = None,
    channel: str | None = None,
) -> float:
    """Calculate net miles per dollar for this card at this MCC."""
    mpd, _, _, _ = _rule_diagnostics(rule, mcc, wallet_has_amaze, merchant_name, channel)
    return mpd


def rank_cards(
    mcc: str,
    card_rules: list[CardRule],
    wallet_has_amaze: bool,
    top_n: int,
    merchant_name: str | None = None,
    channel: str | None = None,
    rate_mode: str = "conditional",
    amount_sgd: float | None = None,
) -> list[dict]:
    """Rank cards by effective mpd for a given MCC. Returns top_n results."""
    if rate_mode not in {"conditional", "guaranteed"}:
        raise ValueError("rate_mode must be 'conditional' or 'guaranteed'.")
    scored = []
    for rule in card_rules:
        if rule.card_id == "amaze":
            continue
        mpd, reason_codes, reasons, gotchas = _rule_diagnostics(
            rule, mcc, wallet_has_amaze, merchant_name, channel
        )
        condition_summary = _condition_summary(rule)
        min_spend_unknown = bool(
            rule.min_spend and (amount_sgd is None or amount_sgd < rule.min_spend)
        )
        cap_unknown = rule.cap_sgd is not None
        conditional = bool(
            mpd > rule.base_rate_mpd and (min_spend_unknown or cap_unknown)
        )
        if rate_mode == "guaranteed" and conditional:
            mpd = rule.base_rate_mpd
            reason_codes.append("bonus_conditions_unknown")
            reasons = []
            gotchas.append("Bonus conditions or remaining cap were not confirmed.")
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
            "reason_summary": _reason_summary(rule.card_name, round(mpd, 4), reasons, gotchas),
            "reason_codes": reason_codes,
            "gotchas": gotchas,
            "rate_status": "conditional" if conditional and rate_mode == "conditional" else "guaranteed",
            "condition_summary": condition_summary,
            "amount_sgd": amount_sgd,
            "estimated_miles": _estimated_miles(rule, amount_sgd, mpd) if amount_sgd is not None else None,
        })

    scored.sort(
        key=lambda x: (
            x["estimated_miles"] if x["estimated_miles"] is not None else x["earn_rate_mpd"],
            x["earn_rate_mpd"],
        ),
        reverse=True,
    )
    return scored[:top_n]
