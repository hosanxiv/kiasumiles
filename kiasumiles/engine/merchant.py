from __future__ import annotations
from rapidfuzz import fuzz, process
from ..data.loader import MerchantRecord


_KEYWORD_MCC: list[tuple[list[str], str]] = [
    (["ramen", "sushi", "noodle", "restaurant", "cafe", "kopitiam", "hawker", "bistro", "eatery", "dining", "coffee", "bak kut", "zi char", "cze char"], "5812"),
    (["supermarket", "fairprice", "cold storage", "sheng siong", "market", "grocery", "giant", "jasons", "little farms"], "5411"),
    (["grab", "gojek", "taxi", "mrt", "bus", "transit", "simplygo", "ez-link", "comfort", "premier cab"], "4121"),
    (["petrol", "shell", "esso", "caltex", "sinopec", "spc", "fuel", "chevron"], "5541"),
    (["pharmacy", "guardian", "watsons", "unity", "ntuc health", "caring"], "5912"),
    (["hotel", "airbnb", "resort", "inn", "lodge", "serviced apartment"], "7011"),
    (["airline", "airways", "scoot", "silkair", "jetstar", "airasia", "flight"], "4511"),
    (["shopping", "department store", "takashimaya", "robinsons", "isetan"], "5311"),
]


def infer_mcc_from_name(merchant: str) -> str | None:
    """Infer MCC from merchant name keywords. Returns None if no match."""
    lower = merchant.lower()
    for keywords, mcc in _KEYWORD_MCC:
        if any(kw in lower for kw in keywords):
            return mcc
    return None

_FUZZY_THRESHOLD = 80


def find_merchant(
    merchant: str,
    outlet: str | None,
    channel: str | None,
    records: list[MerchantRecord],
) -> tuple[MerchantRecord | None, bool]:
    """
    Returns (best_match, is_exact).
    Tries: exact name match → fuzzy name match → None.
    Channel filter: prefers records matching channel, falls back to 'any'.
    """
    needle = merchant.strip().lower()

    # exact match (case-insensitive)
    candidates = [r for r in records if r.merchant_name.lower() == needle]
    if candidates:
        best = _prefer_channel(candidates, channel)
        return best, True

    # fuzzy match
    names = [r.merchant_name for r in records]
    results = process.extract(
        merchant,
        names,
        scorer=fuzz.WRatio,
        limit=5,
    )
    above_threshold = [
        records[idx]
        for name, score, idx in results
        if score >= _FUZZY_THRESHOLD
    ]
    if above_threshold:
        best = _prefer_channel(above_threshold, channel)
        return best, False

    return None, False


def _prefer_channel(
    candidates: list[MerchantRecord],
    channel: str | None,
) -> MerchantRecord:
    if not channel:
        return candidates[0]
    exact_channel = [r for r in candidates if r.channel == channel]
    if exact_channel:
        return exact_channel[0]
    any_channel = [r for r in candidates if r.channel == "any"]
    if any_channel:
        return any_channel[0]
    return candidates[0]
