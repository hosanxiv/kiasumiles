from __future__ import annotations
import re
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
        if any(re.search(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", lower) for kw in keywords):
            return mcc
    return None

_FUZZY_THRESHOLD = 80


class AmbiguousMerchantError(ValueError):
    """Available records cannot establish the requested outlet/category."""


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
        best = _prefer_channel(candidates, channel, outlet)
        return best, True

    # fuzzy match
    names = [r.merchant_name for r in records]
    results = process.extract(
        merchant,
        names,
        scorer=fuzz.ratio,
        limit=None,
        score_cutoff=_FUZZY_THRESHOLD,
    )
    above_threshold = [
        records[idx]
        for name, score, idx in results
        if score >= _FUZZY_THRESHOLD
    ]
    if above_threshold:
        best = _prefer_channel(above_threshold, channel, outlet)
        return best, False

    return None, False


def _prefer_channel(
    candidates: list[MerchantRecord],
    channel: str | None,
    outlet: str | None = None,
) -> MerchantRecord:
    if outlet:
        exact_outlet = [r for r in candidates if (r.outlet or "").strip().casefold() == outlet.strip().casefold()]
        candidates = exact_outlet or [r for r in candidates if not r.outlet]
        if not candidates:
            raise AmbiguousMerchantError("No record confirms this outlet.")
    if channel:
        exact_channel = [r for r in candidates if r.channel == channel]
        compatible_channel = [r for r in candidates if
                              (channel == "mobile_contactless" and r.channel == "contactless") or
                              (channel == "app" and r.channel == "online")]
        any_channel = [r for r in candidates if r.channel == "any"]
        candidates = exact_channel or compatible_channel or any_channel
        if not candidates:
            raise AmbiguousMerchantError("No record confirms this payment method.")
    if len({r.mcc for r in candidates}) > 1:
        raise AmbiguousMerchantError("Multiple merchant categories remain possible.")
    return candidates[0]
