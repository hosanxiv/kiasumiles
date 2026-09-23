from __future__ import annotations
import math
import re
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import replace
from datetime import date, datetime
from zoneinfo import ZoneInfo
from ..data.loader import CardRule


_PERIOD_LABELS = {
    "calendar_month": "calendar month",
    "statement_month": "statement month",
}

_PPS_CARDS = {"amex_pps", "amex_solitaire_pps"}
_RESERVE_LUXURY_BRANDS = (
    "a lange & so|aimer|alexander mcqueen|audemars piguet|balenciaga|bally|bao bao|berluti|"
    "blancpain|bottega veneta|breguet|breitling|burberry|bvlgari|cartier|celine|chanel|chaumet|"
    "chopard|christian dior|christian louboutin|cortina watch|chloe|club 21|coach|dior baby|"
    "dior homme|damiani|davidoff|dolce & gabbana|dover street|emporio armani|emperor watch|"
    "ermenegildo zegna|etro|fendi|flower diamond boutique|franck muller|giorgio armani|givenchy|"
    "goyard|graff diamond|gucci|harry winston|hermes|hermès|hublot|hugo boss|iwc schaffhausen|"
    "jaeger-lecoultre|jimmy choo|kee hing hung|kids 21|kwanpen|l'atelier by the hour glass|"
    "larry jewelry|loewe|longchamp|longines|louis vuitton|lvmh watch & jewellery|max mara|"
    "miu miu|montblanc|moschino|moynat|mulberry|off white|omega|on pedder|panerai|patek philippe|"
    "philipp plein|philip stein|piaget|prada|rimowa|richard mille|roger vivier|rolex|saint laurent|"
    "salvatore ferragamo|sincere fine watches|swiss watch gallery|tag heuer|the canary diamond|"
    "the hour glass|tiffany & co|tissot|tod's|valentino|van cleef & arpels|versace|"
    "watches of switzerland|watch palace|yuli inc. - fine jewellery|zenith"
).split("|")


def validate_payment_codes(transaction_currency: str | None, payment_gateway_country: str | None) -> None:
    for field, value, size in [("transaction_currency", transaction_currency, 3),
                               ("payment_gateway_country", payment_gateway_country, 2)]:
        if value is not None and (not isinstance(value, str) or not re.fullmatch(r"[A-Z]{" + str(size) + r"}", value)):
            raise ValueError(f"{field} must be an uppercase code or null.")


_HSBC_PREMIER_EDUCATION = set("8211 8220 8241 8244 8249 8299".split())
_UOB_PREFERRED_EXCLUDED_MCCS = set(
    "4829 4900 5199 5960 5965 5993 6012 6050 6051 6211 6300 6513 6529 6530 6534 6540 "
    "7349 7511 7523 7995 8062 8211 8220 8241 8244 8249 8299 8398 8661 8651 8699 8999 "
    "9211 9222 9223 9311 9402 9405 9399".split()
)
_HSBC_PREMIER_EXCLUDED = set(
    "4829 4900 5199 5960 6010 6011 6012 6050 6051 6211 6300 6513 "
    "6529 6530 6532 6533 6534 6536 6537 6538 6540 6555 7299 7349 "
    "7399 7511 7523 7801 7995 8062 8398 8651 8661 8999 9211 9222 "
    "9223 9311 9399 9402 9405 9754".split()
)
_AMEX_REWARDS_CARDS = {"amex_krisflyer", "amex_krisflyer_ascend", "amex_highflyer",
                       "amex_plat_charge", "amex_plat_credit", "amex_centurion"} | _PPS_CARDS
_AMEX_EDUCATION_CHARITY_MCCS = {"8211", "8220", "8241", "8244", "8249", "8299", "8398"}


def _pps_high_rate(card_id: str, channel: str | None, transaction_currency: str | None = None) -> float:
    foreign = transaction_currency != "SGD" if transaction_currency else channel == "fcy"
    return (2.4 if card_id == "amex_solitaire_pps" else 2) if foreign else (
        1.5 if card_id == "amex_solitaire_pps" else 1.4)


def _pps_adjust_result(row: dict, prior: float | None, sia_eligible: bool | None,
                       merchant: str | None, channel: str | None, mode: str,
                       transaction_currency: str | None = None) -> None:
    """Attribute the change in rounded monthly rewards, not transaction rounding."""
    row["cap_summary"] = "No cap; cumulative S$10 blocks / calendar month, with separate spending buckets"
    if "transaction_excluded" in row["reason_codes"]:
        return
    eligibility_unknown = "transaction_eligibility_unknown" in row["reason_codes"]
    if eligibility_unknown and mode == "guaranteed":
        row.update(earn_rate_mpd=0, estimated_miles=0 if row["amount_sgd"] is not None else None,
                   reason_summary="Transaction eligibility is unconfirmed; no miles are guaranteed.")
        return
    group_merchant = bool(re.search(r"\b(singapore airlines|scoot|krisshop|pelago)\b", merchant or "", re.I))
    foreign = transaction_currency != "SGD" if transaction_currency else channel == "fcy"
    group_unknown = group_merchant and not foreign and sia_eligible is None
    if group_unknown:
        prior = None  # The applicable bucket has not been established.
    high = 2 if sia_eligible else _pps_high_rate(row["card_id"], channel, transaction_currency)
    low = 2 if sia_eligible else 1.3
    if group_unknown:
        high = max(high, 2)
    amount = row["amount_sgd"]
    row["reason_codes"].append("monthly_spend_unknown" if prior is None else "monthly_spend_supplied")
    row["condition_summary"] = (
        "Use this card's prior eligible calendar-month spending in the same currency bucket, excluding this purchase and qualifying SIA Group purchases. "
        "Qualifying SIA Group purchases use their own bucket. SGD and foreign-currency totals cannot be combined."
    )
    row["gotchas"].append("Miles reflect the change in the rounded monthly total, including any earlier unrounded spending; later refunds can change the result.")
    if group_unknown:
        row["gotchas"].append("Confirm direct SGD booking and Singapore departure for airline tickets, or qualifying KrisShop/Pelago purchase; Pelago digital-wallet payments do not qualify for the 2 mpd rate.")
    if prior is None:
        rate = low if mode == "guaranteed" else high
        row["estimated_miles"] = (round((math.floor(amount / 10) if mode == "guaranteed" else math.ceil(amount / 10)) * 10 * rate, 2)
                                  if amount is not None else None)
        row["rate_status"] = "conditional" if mode == "conditional" else "guaranteed"
        row["reason_summary"] = "Monthly spending is unknown; this is a lower bound." if mode == "guaranteed" else "Monthly spending is unknown; this is an upper bound, not an exact transaction award."
    else:
        prior_decimal = Decimal(str(prior))
        def cumulative(total: Decimal) -> Decimal:
            rounded = (total // 10) * 10
            return (rounded * Decimal(str(low)) if sia_eligible else
                    min(rounded, Decimal(3800)) * Decimal("1.3")
                    + max(rounded - 3800, Decimal(0)) * Decimal(str(high)))
        row["estimated_miles"] = (float(cumulative(prior_decimal + Decimal(str(amount))) - cumulative(prior_decimal))
                                  if amount is not None else None)
        rate = high if prior >= 3800 or sia_eligible else low
        row["rate_status"] = "guaranteed"
        row["reason_summary"] = "Calculated from the supplied prior eligible spending in this card's applicable monthly bucket."
    row["earn_rate_mpd"] = rate
    if eligibility_unknown:
        row["rate_status"] = "conditional"
        row["reason_summary"] += " This also requires an eligible transaction."

_SMART_EXCLUDED_MCCS = set(
    "4829 4900 5047 5199 6012 6050 6051 6540 6211 6513 6529 6530 "
    "6534 7299 7349 7511 7523 8062 8211 8220 8241 8244 8249 8299 "
    "8398 8651 8661 8999 9211 9222 9223 9311 9399 9402 9405 6300 7995".split()
)

_HORIZON_LOCAL_MCCS = set(
    "5411 5441 5462 5499 5811 5812 5813 5814 4011 4111 4112 4121 4131 "
    "4214 4215 4789 5172 5541 5542 5552 4816 5045 5262 5331 5399 5611 "
    "5621 5631 5641 5651 5655 5661 5691 5699 5912 5942 5992 5977 5999 "
    "4511 7011 4411 4722".split()
) | {str(code) for low, high in ((3000, 3999), (5309, 5311), (5732, 5735),
                               (5944, 5949), (5964, 5970)) for code in range(low, high + 1)}
_HORIZON_SELECTED_MCCS = set(
    "6300 6513 7399 8999 8011 8021 8031 8041 8042 8043 8049 8050 8062 "
    "8071 8099 8211 8220 8241 8244 8249 8299".split()
)
_HORIZON_EXCLUDED_MCCS = set(
    "6012 6050 6051 6529 6530 6540 4829 6534 6010 6011 7511 4900 7349 "
    "7523 7995 6211 8398 8651 8661 9211 9222 9223 9311 9399 9402 9405".split()
)
_HORIZON_EXCLUDED_DESCRIPTORS = re.compile(
    r"(?<!\w)(?:axs|sam|youtrip|singtel\s*dash|razerpay|instarem|ez[ -]?link|"
    r"bagus|cantine|sedap|sgebiz|singapore e-business|banc ?de ?binary|"
    r"paypal\s*\*\s*(?:bizconsulta|capitalroya)|flashpay atu|nets vcashcard|"
    r"oanda asia pac|snack by income|skr\*(?:skrill|xglobalmarkets)\.com|"
    r"skyfx\.com|mb\*moneybookers\.com|www\.(?:igmarkets\.com\.sg|plus500\.co\.uk|myezlink\.com\.sg))(?!\w)",
    re.I,
)


def _maybank_rule(rule: CardRule, mcc: str, channel: str | None,
                  transaction_currency: str | None = None) -> CardRule:
    if rule.card_id == "maybank_vi":
        foreign = transaction_currency != "SGD" if transaction_currency else channel == "fcy"
        if mcc in {"6300", "6381", "6399"}:
            return replace(rule, eligible_mccs=[], earn_rate_mpd=0 if foreign else 1.2,
                           base_rate_mpd=0, cap_sgd=3000, min_spend=0)
        return replace(rule, eligible_mccs=[], earn_rate_mpd=3.2 if foreign else 1.2,
                       base_rate_mpd=2 if foreign else 1.2, cap_sgd=None,
                       min_spend=4000 if foreign else 0)
    if rule.card_id != "maybank_horizon":
        return rule
    foreign = transaction_currency != "SGD" if transaction_currency else channel == "fcy"
    if foreign:
        return replace(rule, eligible_mccs=[], cap_sgd=None)
    if mcc in _HORIZON_SELECTED_MCCS:
        return replace(rule, eligible_mccs=[], earn_rate_mpd=.16,
                       base_rate_mpd=0, cap_sgd=3000, min_spend=0)
    if mcc == "4511" or (mcc.isdigit() and 3000 <= int(mcc) <= 3350):
        return replace(rule, eligible_mccs=[mcc])
    rate = 1.2 if mcc in _HORIZON_LOCAL_MCCS else .4
    return replace(rule, eligible_mccs=[], earn_rate_mpd=rate,
                   base_rate_mpd=rate, cap_sgd=None, min_spend=0)

_OCBC_REWARDS_EXCLUDED_MCCS = set(
    "4784 4829 4900 5047 5199 5960 5993 6010 6012 6051 6211 6300 6513 "
    "6540 7349 7523 7995 8062 8211 8220 8241 8244 8249 8299 8398 8651 "
    "8661 8675 8699 9211 9222 9223 9311 9399 9402 9405".split()
)

_TRUST_FREEDOM_EXCLUDED_MCCS = set(
    "4900 6513 7349 4829 5960 6010 6011 6012 6051 6211 6300 6540 7995 "
    "8211 8220 8241 8244 8249 8299 8398 8651 8661 9211 9222 9223 9311 "
    "9399 9402 9405 7299 7399 8999".split()
)
_PRVI_EXCLUDED_MCCS = set(
    "4829 4900 5199 5960 5965 5993 6012 6050 6051 6211 6300 6513 6529 6530 6534 "
    "6540 7349 7511 7523 7995 8062 8211 8220 8241 8244 8249 8299 8398 8661 8651 "
    "8699 8999 9211 9222 9223 9311 9402 9405 9399".split()
)

_DBS_REWARDS_CARDS = {"dbs_altitude_visa", "dbs_altitude_amex", "dbs_insignia", "dbs_vantage", "dbs_wwmc", "dbs_chromo"}
_DBS_GENERAL_RATES = {"dbs_altitude_visa": (1.3, 2.2), "dbs_altitude_amex": (1.3, 2.2),
                      "dbs_insignia": (1.6, 2.0), "dbs_vantage": (1.5, 2.2)}
_BOC_EXCLUDED_MCCS = set("4829 4900 5199 5960 6010 6011 6012 6050 6051 6211 6300 6381 6399 "
    "6513 6529 6530 6534 6540 7511 7995 7349 7523 8211 8220 8241 8244 8249 8299 8062 "
    "8398 8651 8661 8699 8999 9211 9222 9223 9311 9399 9402 9405 5965 5993".split())
_BOC_EXCLUDED_NAMES = set((
    "helpling|sendhelper|institute of technical education|ntu|nus|sim|sit|smu|suss|sutd|"
    "axitrader|banc de binary|bancdebinary.com|city index|forex.com|moneybookers.com|ic markets|"
    "ig asia|www.igmarkets.com.sg|oanda|peppersone|plus500|revolut|saxo capital markets|"
    "saxo cap mkts pte ltd|skr*skrill.com|skr*xglobalmarkets.com|skyfx.com|"
    "acra|cpf|hdb season parking|ica|iras|lta|mom|town council|ura|"
    "farrer park hospital|gleneagles hospital|kk women's and children's hospital|"
    "mount alvernia hospital|mount elizabeth hospital|national university hospital|"
    "parkway shenton hospital|singapore general hospital|tan tock seng hospital|"
    "aia insurance|aig|aviva|axa|great eastern|manulife|msig insurance|ntuc income|"
    "prudential|qbe insurance|sompo insurance|tm life insurance|swiss money transfer|"
    "wise|transit|era singapore|mcst|sp services"
).split("|"))
_WWMC_ONLINE_EXCLUDED_NAMES = (
    "123bitcoin.dk:7310|bettercoins.dk|bitcoingaints|bitcointrade|bitit.io|bitpanda|bitstamp.net|"
    "bittylicious|buycoin|buysomebitcoins|cardup|casadelacrypto.com|cfscfsbitcoinromania|coinbase|"
    "coincorner|coinify|coinmama|coinstec.com|crvcoinbase|crypto5|cryptocapitals|cryptoeu.com|"
    "cryptopaywww.cryptopay|cryptoshop.com|easycoin.cz|fave ecard|favepay|flashpay atu|"
    "gpn_quicbit.eu|indacoin.com102z|indacoin_code:107z|instant bitcoin|ipaymy|iplmileslife.com|"
    "kashmi|kjc coins australia pt|matchmove pay|mb moneybookers.com|oanda asia pac|oandaasiapa|"
    "orangecoin.com|payeer.com|paypal bizconsulta|paypal capitalroya|paypal cmd bitcoin|"
    "paypal coinjolt|paypal oandaasiapa|paypal wmccoin|paypal xcoins|pspcoinsbank.com|"
    "saxo cap mkts pts ltd|seriescoin|simplex_bitstamp|simplex_bittylicious|simplex_paybis|"
    "simplex_x coins|simplex_xapo|skrskrill.com|smoov pte ltd|spectrocoin.com|toroption|"
    "transit|vipcoins.com|www.igmarkets.com.sg|wwwcointedcom|xcoins|xtrade|zeus-crypto.com"
).split("|")
_DBS_EXCLUDED_MCCS = set(
    "4784 4829 4900 5047 5199 5960 5993 6010 6011 6012 6050 6051 6211 "
    "6300 6381 6399 6513 6529 6530 6534 6540 7349 7511 7523 7995 8062 "
    "8211 8220 8241 8244 8249 8299 8398 8651 8661 8699 8999 9211 9222 "
    "9223 9311 9399 9402 9405".split()
)
_DBS_EXCLUDED_DESCRIPTORS = re.compile(
    r"(?<!\w)(?:amaze|axs|bagus|cantine|ez-?link|razerpay|sam payments|sedap|"
    r"sgebiz|singtel\s*dash|singapore e-business|shopeepay|smoove?pay|transit 3|youtrip)(?!\w)",
    re.I,
)

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
    if rule.card_id == "stanChart_beyond":
        return "No cap · rewards calculated on aggregated qualifying spending"
    if rule.card_id == "citi_ultima":
        return "No cap · ThankYou Points rounded to the nearest point per transaction"
    if rule.card_id == "dbs_wwmc":
        if rule.cap_sgd is None:
            return "No overseas-spend cap · base and overseas bonus points rounded separately per transaction"
        return "S$1,000 online cap / calendar month · base points rounded per transaction; online bonus rounded monthly"
    if rule.card_id == "ocbc_rewards":
        return "4,000 ordinary bonus miles / calendar month; earns in S$5 blocks"
    if rule.card_id == "dbs_yuu_visa":
        return "8,000 bonus miles / calendar month, shared across participating merchants"
    period = _PERIOD_LABELS.get(rule.cap_period, rule.cap_period)
    has_cap = rule.cap_sgd is not None
    has_blocks = rule.earn_block_sgd > 1
    block_str = f" · earns in S${rule.earn_block_sgd:g} blocks" if has_blocks else ""
    if rule.card_id in _DBS_GENERAL_RATES:
        block_str = " · DBS Points rounded down per transaction"
    if has_cap:
        cap = f"{rule.cap_sgd:,.2f}".rstrip("0").rstrip(".")
        return f"S${cap} cap / {period}{block_str}"
    return f"No cap{block_str}"


def _merchant_eligible(rule: CardRule, merchant_name: str | None) -> bool:
    """Return False if card has merchant restrictions and this merchant doesn't qualify."""
    if not rule.eligible_merchants:
        return True
    if not merchant_name:
        return False
    return any(re.search(r"(?<!\w)" + re.escape(m.strip()) + r"(?!\w)", merchant_name, re.IGNORECASE)
               for m in rule.eligible_merchants if m.strip())


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
    if channel.lower() == "app" and "online" in eligible_lower:
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
    as_of: date | None = None,
    is_recurring: bool | None = None,
    transaction_currency: str | None = None,
) -> tuple[float, list[str], list[str], list[str]]:
    """Return effective mpd plus explainability fields for a rule."""
    if rule.card_id == "dcs_imperium":
        if mcc in {
            "4784", "4829", "4900", "5199", "5960", "6010", "6011", "6012", "6050", "6051",
            "6211", "6300", "6513", "6535", "6540", "7349", "7523", "7800", "7801", "7802",
            "7995", "8062", "8211", "8220", "8241", "8244", "8249", "8299", "8398", "8651",
            "8661", "9211", "9222", "9223", "9311", "9399", "9402", "9405", "9406",
        } or re.search(r"ez-link|ipaymy|simplygo|skrill\.com|transit|amaze|\baxs\b|\blta\b|singapore post|singpost|road tax|esso fleet", merchant_name or "", re.I):
            return 0.0, ["transaction_excluded"], [], ["This payment is excluded from Imperium rewards."]
        foreign = transaction_currency != "SGD" if transaction_currency else channel == "fcy"
        return (2.4 if foreign else 1.6), [], [], ["Standard rewards only. The 4 mpd overseas tier is not included while its qualifying period remains unconfirmed. Corporate/commercial transactions do not qualify; the account may hold at most two million Imperium Points."]
    if rule.card_id == "amaze":
        return 0.0, ["stored_value_card"], ["Amaze itself does not earn miles."], []
    if rule.card_id in {"hsbc_premier_mc", "hsbc_travelone", "hsbc_revolution"}:
        posting_date = as_of or datetime.now(ZoneInfo("Asia/Singapore")).date()
        foreign = transaction_currency != "SGD" if transaction_currency else channel == "fcy"
        education_allowed = rule.card_id == "hsbc_premier_mc" and foreign and posting_date >= date(2026, 7, 23)
        named_exclusion = re.search(
            r"(?<!\w)(?:axs|cardup|ipaymy|smoovpay|forex\.com|google\s+ads|"
            r"facebook\s+ads|amazon\s+web\s+services|media\s+traffic\s+agency|"
            r"youtrip|skr\s+skrill\.com)(?!\w)", merchant_name or "", re.I)
        if named_exclusion or mcc in _HSBC_PREMIER_EXCLUDED or (mcc in _HSBC_PREMIER_EDUCATION and not education_allowed):
            return 0.0, ["transaction_excluded"], [], ["This transaction is excluded from this card's HSBC rewards programme."]
        if rule.card_id == "hsbc_travelone":
            return (2.0 if foreign else 1.0), [], [], ["Miles are expressed on the KrisFlyer basis of three HSBC points per mile."]
        if rule.card_id == "hsbc_premier_mc":
            return (2.3 if foreign else 1.4), [], [], ["Applies to the SGD-denominated Premier Mastercard, not the USD card."]
    if rule.card_id == "trust_freedom" and mcc in _TRUST_FREEDOM_EXCLUDED_MCCS:
        return 0.0, ["transaction_excluded"], [], ["This transaction category is excluded from Trust Freedom rewards."]
    name = " ".join((merchant_name or "").casefold().split())
    if rule.card_id == "uob_ppv":
        if (mcc in _UOB_PREFERRED_EXCLUDED_MCCS or re.match(
                r"(?:axs|amaze|ez[ -]?link|flashpay atu|nets vcashcard|transit(?!link)|ipaymy|"
                r"rws-levy|smoove pay|singpost-sam|razerpay|norwds|spc\b|shell\b)", name)):
            return 0.0, ["transaction_excluded"], [], ["This payment is excluded from UOB Preferred Visa rewards."]
        if name == "simplygo" and channel in {"contactless", "mobile_contactless"}:
            rule = replace(rule, eligible_mccs=[], eligible_channels=["contactless", "mobile_contactless"])
        elif channel == "online":
            if is_recurring is True:
                return rule.base_rate_mpd, ["bonus_excluded"], [], ["Recurring online payments do not qualify for this bonus."]
        elif channel == "mobile_contactless" and mcc not in rule.eligible_mccs:
            rule = replace(rule, eligible_mccs=[])
    if rule.card_id == "krisflyer_uob":
        if mcc in set("4829 4900 5199 5960 5965 5993 6012 6050 6051 6211 6300 6399 6513 6529 6530 6534 6540 7349 7511 7523 7995 8011 8062 8099 8211 8220 8241 8244 8249 8299 8398 8651 8661 8699 8999 9211 9222 9223 9311 9399 9402 9405".split()) or re.match(r"(?:axs|amaze|ez[ -]?link|flashpay atu|nets vcashcard|norwds|transit|youtrip|ipaymy|rws-levy|smoove pay|singpost-sam|razerpay)", name) or (mcc in {"5541", "5542"} and re.search(r"\bspc\b", name)):
            return 0.0, ["transaction_excluded"], [], ["This purchase is excluded from KrisFlyer UOB miles."]
        if name in {"singapore airlines", "scoot", "krisshop", "pelago"} or (name == "kris+" and channel == "app"):
            return 3.0, [], ["direct eligible merchant purchase"], []
    if rule.card_id in {"uob_reserve", "uob_vim"}:
        excluded_category = mcc in set(
            "4829 4900 5199 5960 5965 5993 6012 6050 6051 6211 6300 6513 "
            "6529 6530 6534 6540 7349 7511 7523 7995 8062 8398 8651 8661 "
            "8699 8999 9211 9222 9223 9311 9402 9405 9399".split())
        excluded_descriptor = bool(re.match(
            r"(?:ez[ -]?link|www\.myezlink\.com\.sg|flashpay\s*atu|mb\*\s*moneybookers\.com|"
            r"oanda\s*asia\s*pa[ c]*|paypal\s*\*\s*(?:plus500\.com|bizconsulta|oandaasiapa|capitalroya)|"
            r"plus500|skr\*\s*(?:plus500cy ltd|skrill\.com)|city index singapore|www\.plus500\.co\.uk|"
            r"saxo cap mkts pte ltd|www\.igmarkets\.com\.sg|transit|amaze|axs[ -]?payment|"
            r"nets vcashcard|razerpay|youtrip|smoove pay|rws-levy|norwds|singpost-sam)", name))
        fuel_excluded = mcc in {"5541", "5542"} and re.search(r"\b(?:shell|spc|singapore petroleum company)\b", name)
        if excluded_category or excluded_descriptor or fuel_excluded or (rule.card_id == "uob_vim" and name.startswith("ipaymy")):
            return 0.0, ["transaction_excluded"], [], ["This transaction is excluded from this UOB card's rewards."]
    if rule.card_id in {"citi_ultima", "citi_premiermiles", "citi_prestige"} and (
        (mcc == "8062" and rule.card_id != "citi_ultima")
        or mcc in {"4829", "4900", "5199", "5960", "5993", "6012", "6050", "6051",
                "6211", "6300", "6513", "7349", "7511", "7523", "7800", "7995", "8398"}
        or (mcc.isdigit() and any(low <= int(mcc) <= high for low, high in
                                 ((6529, 6540), (8211, 8299), (8651, 8661), (9000, 9999))))
        or re.search(r"(?<!\w)(?:axs|banc de binary|bus/mrt|ez[ -]?link|oanda asia pac|sam|"
                     r"saxo cap mkts pte ltd|simplygo|spl (?:auto|atu|online)|skyfx\.com|"
                     r"tl-abt|transit(?: link)?|youtrip)(?!\w)", name)
        or re.search(r"\*\s*(?:bus|mrt)(?!\w)", name)
    ):
        return 0.0, ["transaction_excluded"], [], ["This transaction is excluded from this Citi card's rewards."]
    if rule.card_id == "citi_premiermiles":
        foreign = transaction_currency != "SGD" if transaction_currency else channel == "fcy"
        return 2.2 if foreign else 1.2, [], [], []
    if rule.card_id == "citi_prestige":
        foreign = transaction_currency != "SGD" if transaction_currency else channel == "fcy"
        return 2.0 if foreign else 1.3, [], [], ["Relationship bonuses are not included. Points are accumulated daily before rounding."]
    if rule.card_id in {"uob_prvi_miles_visa", "uob_prvi_miles_amex"}:
        excluded_descriptor = name.startswith(("axs", "amaze", "banc de binary", "bancdebinary.com",
            "ez link", "ez-link", "ezlink", "flashpay atu", "nets vcashcard", "oanda asia pac",
            "oandaasiapa", "skyfx.com", "ipaymy", "rws-levy", "smoove pay", "singpost-sam",
            "razerpay", "norwds")) or bool(re.match(
                r"(?:mb .*moneybookers\.com|paypal \*? ?(?:bizconsulta|capitalroya|oandaasiapa)|"
                r"skr.*(?:skrill\.com|xglobalmarkets\.com)|www\.igmarkets\.com\.sg|saxo cap mkts pte ltd)", name))
        fuel_excluded = mcc in {"5541", "5542"} and (
            bool(re.search(r"\bshell\b", name)) or (rule.card_id.endswith("visa")
            and bool(re.search(r"\b(?:spc|singapore petroleum company)\b", name))))
        if mcc in _PRVI_EXCLUDED_MCCS or excluded_descriptor or fuel_excluded:
            return 0.0, ["transaction_excluded"], [], ["This transaction is excluded from UOB PRVI Miles rewards."]
    if rule.card_id in {"ocbc_90n_mc", "ocbc_90n_visa", "ocbc_voyage", "ocbc_voyage_premier", "ocbc_premier_vi"}:
        voyage = rule.card_id in {"ocbc_voyage", "ocbc_voyage_premier"}
        foreign = transaction_currency != "SGD" if transaction_currency else channel == "fcy"
        rate = (1.28 if rule.card_id == "ocbc_premier_vi"
                else (2.3 if foreign else 1.6) if rule.card_id == "ocbc_voyage_premier"
                else (2.2 if foreign else 1.3) if voyage
                else (2.1 if foreign else 1.3))
        if re.fullmatch(r"axs pay\s*(?:\+|and|&)\s*earn", name):
            return 1.0, [], [], ["AXS Pay+Earn earns one mile per dollar in complete S$5 blocks."]
        private_hospital = (voyage or rule.card_id == "ocbc_premier_vi") and mcc == "8062" and re.fullmatch(
            r"\*?(?:mount elizabeth (?:sing|hospital)|mount alvernia hospital|farrer park hospital|"
            r"gleneagles hospital|thomson medical (?:pte ltd|centre)|parkway east hospital|raffles hospital)\*?", name)
        transport_allowed = re.fullmatch(
            r"(?:grab transport|grab ride|gojek|comfort(?: taxi)?|citycab|transcab|"
            r"smrt taxi|premier taxi|prime taxi|hdt taxi)", name)
        if ((mcc in _OCBC_REWARDS_EXCLUDED_MCCS and not private_hospital)
                or (voyage and (mcc == "8099" or re.search(
                    r"(?<!\w)(?:singhealth|google ads|facebook ads|amazon web services|media traffic agency)(?!\w)", name)))
                or re.search(r"(?<!\w)(?:axs|ez[ -]?link|nets flashpay|enets|"
                             r"transit\s?link|grabpay|youtrip|shopee\s?pay|singtel dash)(?!\w)", name)
                or re.fullmatch(r"sam(?:\s*[*-].*|\s+payments.*)?", name)):
            return 0.0, ["transaction_excluded"], [], ["This transaction is excluded from this card's OCBC miles programme."]
        if mcc in {"4111", "4121", "4131"} and not transport_allowed:
            return rate, ["transaction_eligibility_unknown"], [], ["Transport earns miles only for Grab Transport, Gojek or a licensed taxi operator; confirm the operator before relying on these miles."]
        if voyage and mcc in {"4814", "4816"}:
            if is_recurring is True:
                return 0.0, ["transaction_excluded"], [], ["Recurring telecommunications payments are excluded from VOYAGE rewards."]
            if is_recurring is None:
                return rate, ["transaction_eligibility_unknown"], [], ["Recurring telecommunications payments are excluded; confirm this is not a recurring payment."]
        return rate, [], [], []
    if rule.card_id in _AMEX_REWARDS_CARDS:
        excluded = (
            mcc in {"4900", "6540"}
            or (mcc in _AMEX_EDUCATION_CHARITY_MCCS
                and rule.card_id not in {"amex_plat_charge", "amex_centurion"})
            or re.search(r"(?<!\w)(?:singpost|bus/mrt|simplygo)(?!\w)", name)
            or re.fullmatch(r"sam(?:\s*[*-].*|\s+payments.*)?", name)
            or (mcc in {"5541", "5542"}
                and re.search(r"(?<!\w)(?:spc|singapore petroleum company)(?!\w)", name))
            or re.search(r"(?<!\w)(?:grabpay|shopeepay)\s+(?:top[ -]?up|load)(?!\w)", name)
        )
        if excluded:
            return 0.0, ["transaction_excluded"], [], ["This transaction is excluded from this card's American Express rewards programme."]
        if rule.card_id not in _PPS_CARDS and (mcc in {"6300", "6381", "6399"}
                or (mcc.isdigit() and 8011 <= int(mcc) <= 8099)):
            return rule.base_rate_mpd, ["transaction_eligibility_unknown"], [], ["Insurance requires an Amex-authorized purchase channel; healthcare must not be a public/restructured institution. Eligibility has not been confirmed."]
    if rule.card_id in _PPS_CARDS:
        if mcc in {"6300", "6381", "6399"} or (mcc.isdigit() and 8011 <= int(mcc) <= 8099):
            return _pps_high_rate(rule.card_id, channel, transaction_currency), ["transaction_eligibility_unknown"], [], ["Insurance must be purchased through an Amex-authorized channel; public/restructured healthcare is excluded. The category alone cannot confirm eligibility."]
        return _pps_high_rate(rule.card_id, channel, transaction_currency), ["monthly_spend_unknown"], [], ["The rate depends on separate eligible monthly spending totals."]
    if rule.card_id in {"maybank_horizon", "maybank_vi"} and (
        mcc in _HORIZON_EXCLUDED_MCCS or _HORIZON_EXCLUDED_DESCRIPTORS.search(name)
    ):
        return 0.0, ["transaction_excluded"], [], ["This transaction is excluded from Maybank rewards."]
    if rule.card_id == "maybank_vi" and re.search(r"(?<!\w)(?:nets|enets|simplygo|transit|transitlink|transit link)(?!\w)", name):
        return 0.0, ["transaction_excluded"], [], ["This transaction is excluded from Maybank rewards."]
    if rule.card_id in {"stanChart_smart", "stanChart_beyond", "stanChart_journey"} and (
        mcc in _SMART_EXCLUDED_MCCS or re.search(r"(?<!\w)(?:axs|sam)(?!\w)", name)
    ):
        return 0.0, ["transaction_excluded"], [], ["This transaction is excluded from Standard Chartered rewards, including base points."]
    if rule.card_id in {"stanChart_beyond", "stanChart_journey"} and re.search(
            r"(?<!\w)(?:ez[ -]?link|ezlinks\.com|flashpay atu|simplygo|transit(?:\s*link)?|"
            r"paypal\s*\*\s*(?:bizconsulta|capitalroya))(?!\w)", name):
        return 0.0, ["transaction_excluded"], [], ["This payment service is excluded from Standard Chartered rewards."]
    if rule.card_id == "boc_elite" and (mcc in _BOC_EXCLUDED_MCCS
            or name.replace("’", "'") in _BOC_EXCLUDED_NAMES
            or re.search(r"(?<!\w)(?:axs|cardup|ipaymy|ez[ -]?link|enets|hellopay|matchmove pay|"
                         r"nets flashpay|sam payments|singtel dash|transitlink|youtrip|renthero|"
                         r"moneygram|western union|worldremit)(?!\w)", name)
            or re.fullmatch(r"sam(?:\s*[*-].*)?", name)
            or re.search(r"(?<!\w)(?:grab(?:pay)?|shopeepay)\s+(?:(?:mobile\s+)?wallet\s+)?top[ -]?up(?!\w)", name)):
        return 0.0, ["transaction_excluded"], [], ["This transaction is excluded from BOC Elite Miles rewards."]
    if rule.card_id == "dbs_chromo" and (transaction_currency != "SGD" if transaction_currency else (channel or "").lower() == "fcy"):
        return 0.0, ["transaction_excluded"], [], ["Chromo does not earn miles on foreign-currency transactions."]
    if rule.card_id in _DBS_REWARDS_CARDS or rule.card_id == "dbs_yuu_visa":
        if (mcc in _DBS_EXCLUDED_MCCS or _DBS_EXCLUDED_DESCRIPTORS.search(name)
                or (rule.card_id in _DBS_REWARDS_CARDS and re.search(r"\bsam\s*-", name))):
            return 0.0, ["transaction_excluded"], [], ["This transaction is excluded from this card's DBS rewards programme."]
    if rule.card_id in _DBS_GENERAL_RATES:
        foreign = transaction_currency != "SGD" if transaction_currency else channel == "fcy"
        return _DBS_GENERAL_RATES[rule.card_id][foreign], [], [], []
    if rule.card_id == "dbs_wwmc" and channel == "fcy":
        return 1.2, [], [], []
    if rule.card_id == "dbs_wwmc" and (mcc in {
            "0763", "7261", "7276", "7311", "7322", "7339", "7372", "7375",
            "7393", "7399", "8111", "8911", "8931"}
            or any(re.search(r"(?<!\w)" + re.escape(excluded) + r"(?!\w)", name)
                   for excluded in _WWMC_ONLINE_EXCLUDED_NAMES)):
        return rule.base_rate_mpd, ["bonus_excluded"], [], ["This transaction does not qualify for the Woman's World online bonus."]
    if rule.card_id == "dbs_yuu_visa":
        if "cold storage on the go" in name:
            return rule.base_rate_mpd, ["bonus_excluded"], [], ["Cold Storage On The Go does not qualify for the yuu bonus."]
        if re.search(r"\bchagee\b", name) and (channel or "").lower() != "app":
            return rule.base_rate_mpd, ["channel_not_eligible"], [], ["CHAGEE bonus requires an order placed through the CHAGEE app; that has not been confirmed."]

    reason_codes: list[str] = []
    reasons: list[str] = []
    gotchas: list[str] = []

    if rule.requires_amaze and not wallet_has_amaze:
        reason_codes.append("requires_amaze_missing")
        gotchas.append("Needs Amaze pairing to unlock this bonus rate.")
        return rule.base_rate_mpd, reason_codes, reasons, gotchas

    category_or_merchant = rule.card_id == "ocbc_rewards"
    if category_or_merchant:
        if mcc in _OCBC_REWARDS_EXCLUDED_MCCS or re.search(r"\baxs\b", name):
            return 0.0, ["transaction_excluded"], [], ["This transaction is excluded from OCBC Rewards points."]
        if mcc == "5262" and "shopeepay" in "".join((merchant_name or "").lower().split()):
            return 0.0, ["transaction_excluded"], [], ["Shopee Pay transactions do not earn rewards."]
        if mcc == "5411":
            posting_day = as_of or datetime.now(ZoneInfo("Asia/Singapore")).date()
            if re.search(r"\b(shopee|lazada)\b", name) and date(2026, 7, 1) <= posting_day <= date(2027, 3, 31):
                return 0.0, ["transaction_excluded"], [], ["The campaign excludes grocery-category Shopee and Lazada transactions from all OCBC$."]
            return rule.base_rate_mpd, ["bonus_excluded"], [], ["Grocery transactions do not qualify for the shopping bonus."]
        if mcc in rule.eligible_mccs:
            reason_codes.append("mcc_eligible")
            reasons.append("merchant category is eligible")
        elif merchant_name and rule.eligible_merchants and _merchant_eligible(rule, merchant_name):
            reason_codes.append("merchant_eligible")
            reasons.append("merchant is in this card's eligible merchant list")
        else:
            return rule.base_rate_mpd, ["bonus_not_eligible"], [], ["Neither a qualifying shopping category nor a named bonus merchant was confirmed."]

    if rule.eligible_mccs and not category_or_merchant:
        if mcc in rule.eligible_mccs:
            reason_codes.append("mcc_eligible")
            reasons.append("merchant category is eligible")
        else:
            reason_codes.append("mcc_not_eligible")
            gotchas.append("Merchant category is outside this card's bonus whitelist.")
            return rule.base_rate_mpd, reason_codes, reasons, gotchas
    elif not category_or_merchant:
        reason_codes.append("no_mcc_restriction")
        reasons.append("card has no merchant-category restriction")

    if rule.eligible_merchants and not category_or_merchant:
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

    if rule.card_id == "ocbc_rewards" and re.search(r"\b(watsons|shopee|lazada|tiktok shop|taobao)\b", name):
        posting_day = as_of or datetime.now(ZoneInfo("Asia/Singapore")).date()
        if date(2026, 7, 1) <= posting_day <= date(2027, 3, 31):
            mpd += 2
            gotchas.append("Promotional extra 2 mpd requires posting by 31 March 2027 and available promotional cap, shared with supplementary cards.")

    reason_codes.append("bonus_rate_applied")
    if rule.cap_sgd is not None:
        reason_codes.append("monthly_cap_applies")
        reasons.append(_cap_summary(rule))
    if rule.min_spend:
        reason_codes.append("min_spend_applies")
        gotchas.append(
            "Requires S$1,000 eligible Singapore Airlines Group spending in the card membership year."
            if rule.card_id == "krisflyer_uob"
            else f"Requires at least S${rule.min_spend:g} spend before the bonus is reliable."
        )

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
    if rule.card_id == "dbs_yuu_visa":
        return "S$800 eligible spend and four different participating merchant groups / calendar month; remaining shared bonus cap must be available. Link your yuu account and scan/link your yuu ID for partner base points; product exclusions apply."
    if rule.card_id == "krisflyer_uob" and rule.min_spend:
        return "S$1,000 eligible Singapore Airlines Group spending in the card membership year; accelerated miles are awarded after that year."
    conditions = []
    if rule.min_spend:
        conditions.append(f"S${rule.min_spend:g} minimum spend")
    if rule.cap_sgd is not None:
        conditions.append(_cap_summary(rule))
    return " · ".join(conditions) or None


def _rounded_miles(rule: CardRule, amount_sgd: float, rate_mpd: float) -> float:
    if amount_sgd <= 0:
        return 0.0
    if rule.card_id == "dcs_imperium":
        points = Decimal(str(amount_sgd)) * Decimal(str(rate_mpd)) * Decimal("2.5")
        return float((points // 1) / Decimal("2.5"))
    if rule.card_id in {"amex_plat_charge", "amex_plat_credit"}:
        if rate_mpd == 0:
            return 0.0
        points = (Decimal(str(amount_sgd)) / Decimal("1.6") // 1) * 2
        divisor = Decimal("2") if rule.card_id == "amex_plat_charge" else Decimal("2.2")
        return round(float(points / divisor), 2)
    if rule.card_id == "stanChart_beyond":
        return round(amount_sgd * rate_mpd, 2)
    if rule.card_id == "citi_premiermiles":
        return float(Decimal(str(amount_sgd)) * Decimal(str(rate_mpd)) // 1)
    if rule.card_id == "citi_prestige":
        return float(Decimal(str(amount_sgd)) * Decimal(str(rate_mpd)))
    if rule.card_id == "citi_ultima":
        points = Decimal(str(amount_sgd)) * Decimal(str(rate_mpd)) * Decimal("2.5")
        return float(points.quantize(Decimal("1"), rounding=ROUND_HALF_UP) / Decimal("2.5"))
    if rule.card_id in _DBS_GENERAL_RATES:
        points = Decimal(str(amount_sgd)) * Decimal(str(rate_mpd)) / 2
        return float((points // 1) * 2)
    if rule.card_id == "hsbc_travelone":
        if rate_mpd == 0:
            return 0.0
        amount = Decimal(str(amount_sgd))
        base = amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        additional = (amount * (5 if rate_mpd == 2.0 else 2)).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP)
        return round(float((base + additional) / 3), 2)
    if rule.card_id == "hsbc_premier_mc":
        points = (Decimal(str(amount_sgd)) * Decimal(str(rate_mpd)) * 3).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP)
        return round(float(points / 3), 2)
    if rule.card_id == "dbs_chromo":
        return float(math.floor(amount_sgd * rate_mpd / 2) * 2)
    if rule.card_id == "dbs_wwmc" and rate_mpd == 1.2:
        amount = Decimal(str(amount_sgd))
        return float(((amount / 5 // 1) + (amount * 2 / 5 // 1)) * 2)
    eligible_spend = math.floor(amount_sgd / rule.earn_block_sgd) * rule.earn_block_sgd
    if rule.card_id in {"ocbc_voyage", "ocbc_voyage_premier"}:
        return float(Decimal(str(eligible_spend)) * Decimal(str(rate_mpd)) // 1)
    if rule.card_id in {"uob_prvi_miles_visa", "uob_prvi_miles_amex", "uob_vim"}:
        points = Decimal(str(eligible_spend)) * Decimal(str(rate_mpd)) / 2
        return float((points // 1) * 2)
    if rule.card_id == "dbs_wwmc" and rate_mpd > rule.base_rate_mpd:
        amount = Decimal(str(amount_sgd))
        base_rate = Decimal(str(rule.base_rate_mpd))
        base = (amount * base_rate / 2 // 1) * 2
        bonus = (amount * (Decimal(str(rate_mpd)) - base_rate) / 2 // 1) * 2
        return float(base + bonus)
    if rule.bank == "DBS" and rule.card_id != "dbs_yuu_visa":
        return float(math.floor(eligible_spend * rate_mpd / 2) * 2)
    return round(eligible_spend * rate_mpd, 2)


def _estimated_miles(rule: CardRule, amount_sgd: float, rate_mpd: float) -> float:
    if rule.card_id == "ocbc_rewards" and rate_mpd > rule.base_rate_mpd:
        spend = math.floor(amount_sgd / rule.earn_block_sgd) * rule.earn_block_sgd
        ordinary = spend * rule.base_rate_mpd + min(4000, spend * (rule.earn_rate_mpd - rule.base_rate_mpd))
        return round(ordinary + min(2000, spend * max(0, rate_mpd - rule.earn_rate_mpd)), 2)
    if rule.card_id == "dbs_yuu_visa" and rate_mpd > rule.base_rate_mpd:
        eligible_spend = math.floor(amount_sgd / rule.earn_block_sgd) * rule.earn_block_sgd
        return round(eligible_spend * rule.base_rate_mpd
                     + min(8000, eligible_spend * (rate_mpd - rule.base_rate_mpd)), 2)
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
    as_of: date | None = None,
) -> float:
    """Calculate net miles per dollar for this card at this MCC."""
    rule = _maybank_rule(rule, mcc, channel)
    mpd, _, _, _ = _rule_diagnostics(rule, mcc, wallet_has_amaze, merchant_name, channel, as_of)
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
    chocolate_eligible: bool | None = None,
    as_of: date | None = None,
    smart_statement_spend_sgd: float | None = None,
    pps_prior_spend_sgd: dict[str, float] | None = None,
    pps_sia_group_eligible: bool | None = None,
    vantage_miles_selected: bool | None = None,
    transaction_currency: str | None = None,
    payment_gateway_country: str | None = None,
    is_recurring: bool | None = None,
    revolution_ega_eligible: bool | None = None,
    revolution_prior_eligible_spend_sgd: float | None = None,
) -> list[dict]:
    """Rank cards by effective mpd for a given MCC. Returns top_n results."""
    if rate_mode not in {"conditional", "guaranteed"}:
        raise ValueError("rate_mode must be 'conditional' or 'guaranteed'.")
    validate_payment_codes(transaction_currency, payment_gateway_country)
    if revolution_prior_eligible_spend_sgd is not None and (
        type(revolution_prior_eligible_spend_sgd) not in (int, float)
        or not math.isfinite(revolution_prior_eligible_spend_sgd)
        or revolution_prior_eligible_spend_sgd < 0
    ):
        raise ValueError("revolution_prior_eligible_spend_sgd must be a finite non-negative number.")
    if revolution_ega_eligible is not None and type(revolution_ega_eligible) is not bool:
        raise ValueError("revolution_ega_eligible must be true, false or null.")
    if is_recurring is not None and type(is_recurring) is not bool:
        raise ValueError("is_recurring must be true, false or null.")
    if vantage_miles_selected is not None and type(vantage_miles_selected) is not bool:
        raise ValueError("vantage_miles_selected must be true, false or null.")
    if pps_prior_spend_sgd is not None and (
        not isinstance(pps_prior_spend_sgd, dict) or any(
            cid not in _PPS_CARDS or type(value) not in (int, float) or not math.isfinite(value) or value < 0
            for cid, value in pps_prior_spend_sgd.items())):
        raise ValueError("pps_prior_spend_sgd must map PPS card IDs to finite non-negative spending totals.")
    if pps_sia_group_eligible is not None and type(pps_sia_group_eligible) is not bool:
        raise ValueError("pps_sia_group_eligible must be true, false or null.")
    foreign = transaction_currency != "SGD" if transaction_currency else channel == "fcy"
    if pps_sia_group_eligible and (foreign or not re.search(
            r"\b(singapore airlines|scoot|krisshop|pelago)\b", merchant_name or "", re.I)
            or (re.search(r"\bpelago\b", merchant_name or "", re.I) and channel == "mobile_contactless")):
        raise ValueError("The supplied merchant or payment does not qualify for the PPS SIA Group rate.")
    scored = []
    for rule in card_rules:
        if rule.card_id == "amaze":
            continue
        rule = _maybank_rule(rule, mcc, channel, transaction_currency)
        if rule.card_id == "krisflyer_uob" and ((merchant_name or "").casefold().strip() in {"singapore airlines", "scoot", "krisshop", "pelago"} or ((merchant_name or "").casefold().strip() == "kris+" and channel == "app")):
            rule = replace(rule, min_spend=0, earn_rate_mpd=3, base_rate_mpd=3)
        if rule.card_id == "stanChart_journey":
            rule = replace(rule, eligible_channels=["online"], base_rate_mpd=2 if foreign else 1.2,
                           earn_rate_mpd=2 if foreign else 3, cap_sgd=None if foreign else 1000,
                           cap_period="statement_month", min_spend=0)
        if rule.card_id == "dcs_imperium":
            rate = 2.4 if foreign else 1.6
            rule = replace(rule, earn_rate_mpd=rate, base_rate_mpd=rate, cap_sgd=None, min_spend=0)
        if rule.card_id == "hsbc_revolution" and revolution_ega_eligible is True:
            rule = replace(rule, earn_rate_mpd=8, base_rate_mpd=.4, cap_sgd=1200,
                           cap_period="calendar_month", earn_block_sgd=1)
        if rule.card_id == "citi_premiermiles":
            rate = 2.2 if foreign else 1.2
            rule = replace(rule, earn_rate_mpd=rate, base_rate_mpd=rate, cap_sgd=None, min_spend=0)
        if rule.card_id == "citi_prestige":
            rate = 2.0 if foreign else 1.3
            rule = replace(rule, earn_rate_mpd=rate, base_rate_mpd=rate, cap_sgd=None, min_spend=0)
        if rule.card_id in {"amex_plat_charge", "amex_plat_credit"}:
            rate = .625 if rule.card_id == "amex_plat_charge" else 1.25 / 2.2
            rule = replace(rule, earn_rate_mpd=rate, base_rate_mpd=rate, earn_block_sgd=1.6)
        if rule.card_id in {"citi_ultima", "stanChart_beyond"}:
            foreign = transaction_currency != "SGD" if transaction_currency else channel == "fcy"
            rate = (2.0 if foreign else 1.6) if rule.card_id == "citi_ultima" else (3.0 if foreign else 1.5)
            rule = replace(rule, earn_rate_mpd=rate, base_rate_mpd=rate, cap_sgd=None, min_spend=0)
        if rule.card_id == "dbs_wwmc" and channel == "fcy":
            rule = replace(rule, earn_rate_mpd=1.2, base_rate_mpd=1.2, cap_sgd=None)
        if rule.card_id in {"hsbc_premier_mc", "hsbc_travelone"}:
            foreign = transaction_currency != "SGD" if transaction_currency else channel == "fcy"
            rate = ((2.0 if foreign else 1.0) if rule.card_id == "hsbc_travelone"
                    else (2.3 if foreign else 1.4))
            rule = replace(rule, earn_rate_mpd=rate, base_rate_mpd=rate, cap_sgd=None, min_spend=0)
        if rule.card_id == "stanChart_smart" and smart_statement_spend_sgd is not None:
            base = rule.base_rate_mpd * (2 if smart_statement_spend_sgd >= 1500 else 1)
            rate = (rule.earn_rate_mpd if smart_statement_spend_sgd >= 1500 else
                    rule.earn_rate_mpd * .8 if smart_statement_spend_sgd >= 800 else base)
            rule = replace(rule, base_rate_mpd=base, earn_rate_mpd=rate, min_spend=0)
        mpd, reason_codes, reasons, gotchas = _rule_diagnostics(
            rule, mcc, wallet_has_amaze, merchant_name, channel, as_of, is_recurring, transaction_currency
        )
        if rule.card_id in {"amex_plat_charge", "amex_plat_credit"} and mpd > 0:
            gotchas.append("Base rewards only, expressed as KrisFlyer miles. Partner and promotional bonuses are not included; eligibility has not been confirmed.")
        if rule.card_id == "stanChart_beyond" and mpd > 0:
            gotchas.append("Single-purchase estimate before rounding of aggregated qualifying spending; the statement award can differ. Relationship bonuses are not included without confirmed eligibility.")
        if rule.card_id in {"uob_reserve", "uob_vim"} and mpd > 0:
            local_rate = 1.6 if rule.card_id == "uob_reserve" else 1.4
            rule = replace(rule, base_rate_mpd=local_rate, cap_sgd=None, min_spend=0)
            mpd = local_rate
            if transaction_currency != "SGD" and payment_gateway_country != "SG":
                if transaction_currency and payment_gateway_country:
                    mpd = 2.4
                elif channel == "fcy" or transaction_currency or payment_gateway_country:
                    mpd = 2.4
                    reason_codes.append("overseas_processing_unconfirmed")
                    gotchas.append("The overseas rate requires a foreign-currency charge processed outside Singapore; confirm both details.")
            if (rule.card_id == "uob_reserve" and transaction_currency == "SGD" and channel in {"contactless", "mobile_contactless"}
                    and (merchant_name or "").casefold().strip() in _RESERVE_LUXURY_BRANDS):
                mpd = 2.0
                rule = replace(rule, cap_sgd=20000, cap_period="calendar_month")
                gotchas.append("Luxury bonus requires this brand's standalone Singapore boutique, not a department store, and remaining allowance within S$20,000 monthly eligible luxury spend. Outlet eligibility is unconfirmed.")
        if rule.card_id == "ocbc_premier_vi" and mpd > 0:
            rule = replace(rule, earn_rate_mpd=2.24, base_rate_mpd=1.28)
            if transaction_currency != "SGD" and payment_gateway_country != "SG":
                if transaction_currency and payment_gateway_country:
                    mpd = 2.24
                elif channel == "fcy" or transaction_currency:
                    mpd = 2.24
                    reason_codes.append("overseas_processing_unconfirmed")
                    gotchas.append("The foreign-currency rate requires an overseas retail purchase; confirm the processing country.")
        if rule.card_id in {"uob_prvi_miles_visa", "uob_prvi_miles_amex", "boc_elite"} and mpd > 0:
            if transaction_currency == "SGD" or payment_gateway_country == "SG":
                mpd = 1.4
            elif transaction_currency and payment_gateway_country:
                mpd = 3.0 if {"MYR": "MY", "IDR": "ID", "THB": "TH", "VND": "VN"}.get(transaction_currency) == payment_gateway_country else 2.4
                if rule.card_id == "boc_elite":
                    mpd = 2.8
            elif channel == "fcy" or transaction_currency or payment_gateway_country:
                regional_possible = (transaction_currency is None or transaction_currency in {"MYR", "IDR", "THB", "VND"}) and (payment_gateway_country is None or payment_gateway_country in {"MY", "ID", "TH", "VN"})
                mpd = 3.0 if regional_possible else 2.4
                if rule.card_id == "boc_elite":
                    mpd = 2.8
                reason_codes.append("overseas_processing_unconfirmed")
                gotchas.append("Confirm charged currency and payment-gateway country. Singapore-processed payments earn the local rate." +
                               (" PRVI's regional bonus requires matching currency and country." if rule.card_id != "boc_elite" else ""))
        if rule.card_id in {"uob_prvi_miles_visa", "uob_prvi_miles_amex"} and mpd > 0:
            partner = (merchant_name or "").casefold().strip()
            today = as_of or datetime.now(ZoneInfo("Asia/Singapore")).date()
            if partner == "expedia" and today <= date(2027, 3, 31):
                gotchas.append("Expedia partner bonus is not included: book through expedia.com.sg/prvimiles and pay Expedia upfront. Eligible hotels can earn 8 mpd; participating flights can earn 3 mpd through 31 March 2027. Confirm the booking type and merchant of record.")
            elif partner == "agoda" and today <= date(2027, 8, 15):
                gotchas.append("Agoda partner bonus is not included: use agoda.com/prvimiles, select an eligible prepaid hotel displaying the bonus banner, and complete the stay by 15 November 2027. Japan stays do not qualify; local and overseas rates differ.")
        if (rule.card_id == "stanChart_smart" and smart_statement_spend_sgd is None
                and mpd == rule.base_rate_mpd and mpd > 0):
            mpd *= 2
            reason_codes.append("statement_tier_unconfirmed")
            gotchas.append("The higher base rate requires S$1,500 eligible statement-month spending.")
        if rule.card_id == "dbs_yuu_visa" and mpd > rule.base_rate_mpd:
            # Partner base points are twice the SimplyGo/non-partner base points.
            base = rule.base_rate_mpd if re.search(r"\bsimplygo\b", merchant_name or "", re.I) else rule.base_rate_mpd * 2
            rule = replace(rule, base_rate_mpd=base, cap_sgd=8000 / (mpd - base))
            gotchas.append("The top rate requires four different participating merchant groups and S$800 eligible spend in the calendar month.")
        if rule.card_id in {"stanChart_smart", "stanChart_beyond", "stanChart_journey"} and is_recurring is True:
            mpd, reasons = 0.0, []
            reason_codes.append("transaction_excluded")
            gotchas.append("Automatic recurring payments are excluded from Standard Chartered rewards.")
        condition_summary = _condition_summary(rule)
        revolution_bonus = rule.card_id == "hsbc_revolution" and mpd > rule.base_rate_mpd
        revolution_progress_known = revolution_bonus and revolution_prior_eligible_spend_sgd is not None
        if rule.card_id == "hsbc_revolution" and mpd > 0:
            gotchas.append("Enhanced rewards require at least S$50,000 average daily SGD deposits in your sole HSBC Everyday Global Account for the posting month; joint accounts do not qualify.")
            if revolution_progress_known:
                condition_summary = "Monthly rounding and remaining bonus allowance calculated using your supplied eligible spending before this purchase."
                if revolution_prior_eligible_spend_sgd >= rule.cap_sgd:
                    mpd = rule.base_rate_mpd
            else:
                gotchas.append("Monthly spending aggregation can affect rounding. This estimate treats the purchase on its own; remaining bonus allowance is unconfirmed.")
        if rule.card_id == "dbs_wwmc" and mpd > rule.base_rate_mpd:
            gotchas.append("Online bonus points are rounded after monthly accumulation; this estimate treats the purchase on its own and assumes the displayed cap is available.")
        ocbc_promo = rule.card_id == "ocbc_rewards" and mpd > rule.earn_rate_mpd
        chocolate_bill = rule.card_id == "chocolate_visa" and (
            mcc in {"6513", "6531"} or (len(mcc) == 4 and mcc.isdigit() and any(
                low <= int(mcc) <= high for low, high in
                ((8011, 8099), (9311, 9399), (4900, 4999), (6300, 6399), (7311, 7399)))))
        account_unknown = rule.card_id == "chocolate_visa" and chocolate_eligible is None
        account_ineligible = rule.card_id == "chocolate_visa" and chocolate_eligible is False
        if account_unknown:
            if rate_mode == "guaranteed":
                continue
            if (as_of or datetime.now(ZoneInfo("Asia/Singapore")).date()) < date(2026, 10, 1):
                gotchas.append("Confirm your Chocolate Visa card is linked and verified on HeyMax and both accounts use the same email before relying on any miles.")
            else:
                gotchas.append("Confirm your Chocolate Visa card is linked and verified on HeyMax, both accounts use the same email, and you had at least S$5,000 prior-month average daily SGD balance before relying on any miles.")
            reason_codes.append("account_eligibility_unknown")
        if account_ineligible:
            mpd = 0.0
            reasons = []
            gotchas.append("Account is not eligible for miles this month.")
            reason_codes.append("account_ineligible")
        min_spend_unknown = bool(rule.min_spend)
        cap_unknown = rule.cap_sgd is not None and not revolution_progress_known
        reward_mode_unknown = rule.card_id in {"trust_freedom", "dbs_chromo"} and mpd > 0
        vantage_choice_unknown = rule.card_id == "dbs_vantage" and vantage_miles_selected is not True and mpd > 0
        if vantage_choice_unknown:
            reason_codes.append("reward_choice_unconfirmed")
            gotchas.append("Confirm Miles is selected in digibank. With cashback selected, DBS Points automatically become cashback on the first working day of the next month; redeem points before then to retain their miles value.")
        transaction_unknown = "transaction_eligibility_unknown" in reason_codes
        if reward_mode_unknown and rule.card_id == "dbs_chromo":
            gotchas.append("Choose Miles by the 10th of the following month for this month's eligible SGD spending; the default preference is cashback.")
        elif reward_mode_unknown:
            gotchas.append("Requires Miles mode to be selected for this transaction; cashback and stockback modes do not earn miles.")
        conditional = bool(
            account_unknown or transaction_unknown or reward_mode_unknown or vantage_choice_unknown or "overseas_processing_unconfirmed" in reason_codes or (mpd > rule.base_rate_mpd and (min_spend_unknown or cap_unknown))
        )
        if chocolate_bill and mpd > 0:
            conditional = True
            reason_codes.append("remaining_bill_cap_unknown")
        if rate_mode == "guaranteed" and conditional and not transaction_unknown and not vantage_choice_unknown:
            mpd = rule.base_rate_mpd
            reason_codes.append("bonus_conditions_unknown")
            reasons = []
            gotchas.append("Bonus conditions or remaining cap were not confirmed.")
        if (transaction_unknown or vantage_choice_unknown) and rate_mode == "guaranteed":
            mpd = 0.0
            reasons = []
        if chocolate_bill:
            condition_summary = "Up to 300 miles / calendar month for eligible bill payments; remaining allowance unconfirmed."
            gotchas.append(condition_summary)
            if rate_mode == "guaranteed":
                mpd = 0.0
                reasons = []
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
            "estimated_miles": (
                _estimated_miles(
                    rule,
                    amount_sgd,
                    rule.earn_rate_mpd
                    if rule.requires_amaze and mpd > rule.base_rate_mpd
                    else mpd,
                )
                if amount_sgd is not None
                else None
            ),
        })
        if rule.card_id in {"uob_ppv", "uob_prvi_miles_visa", "uob_prvi_miles_amex"} and (merchant_name or "").casefold().strip() == "simplygo" and channel in {"contactless", "mobile_contactless"}:
            scored[-1]["estimated_miles"] = None
            scored[-1]["condition_summary"] = "SimplyGo rewards use accumulated monthly spending; an individual fare's exact miles cannot be calculated alone."
            scored[-1]["gotchas"].append("SimplyGo rewards are accumulated monthly, so an exact award needs that month's eligible fares.")
        if revolution_progress_known and amount_sgd is not None:
            prior = Decimal(str(revolution_prior_eligible_spend_sgd))
            before = prior // 1
            after = (prior + Decimal(str(amount_sgd))) // 1
            cap = Decimal(str(rule.cap_sgd))
            bonus = Decimal(str(rule.earn_rate_mpd)) - Decimal("0.4")
            scored[-1]["estimated_miles"] = float(
                (after - before) * Decimal("0.4")
                + (min(after, cap) - min(before, cap)) * bonus)
        if rule.card_id == "stanChart_journey" and amount_sgd is not None and mpd > 0:
            amount = Decimal(str(amount_sgd))
            base_points = amount * (Decimal("5") if foreign else Decimal("3"))
            bonus_points = min(amount, Decimal("1000")) * Decimal("4.5") if mpd > rule.base_rate_mpd else Decimal(0)
            if all(p == p.to_integral_value() for p in (base_points, bonus_points)):
                scored[-1]["estimated_miles"] = float((base_points + bonus_points) / Decimal("2.5"))
            else:
                scored[-1]["estimated_miles"] = None
                scored[-1]["reason_codes"].append("rounding_unconfirmed")
                scored[-1]["gotchas"].append("Journey credits base and statement-month bonus points separately. Exact rounding is unconfirmed; no exact miles total is shown.")
        if rule.card_id == "citi_prestige" and amount_sgd is not None and mpd > 0:
            points = Decimal(str(amount_sgd)) * Decimal(str(mpd)) * Decimal("2.5")
            if points != points.to_integral_value():
                scored[-1]["estimated_miles"] = None
                scored[-1]["reason_codes"].append("daily_rounding_unconfirmed")
                scored[-1]["gotchas"].append("An exact miles total requires the other points accumulated that day; no exact total is shown.")
        if rule.card_id == "citi_premiermiles" and amount_sgd is not None and mpd > 0:
            alternate = ((Decimal(str(amount_sgd)) // 1) * Decimal(str(mpd))).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP)
            if alternate != Decimal(str(scored[-1]["estimated_miles"])):
                scored[-1]["estimated_miles"] = None
                scored[-1]["reason_codes"].append("rounding_unconfirmed")
                scored[-1]["gotchas"].append("The earn rate is known, but purchase rounding is unconfirmed. An exact miles total is not shown; confirm the award with Citi.")
        if chocolate_bill:
            scored[-1]["cap_summary"] = condition_summary
            if mpd > 0:
                scored[-1]["estimated_miles"] = None
        if ocbc_promo:
            scored[-1]["cap_summary"] += "; separate 2,000 promotional bonus miles / calendar month through 31 March 2027"
        if rule.card_id in _PPS_CARDS:
            _pps_adjust_result(scored[-1], (pps_prior_spend_sgd or {}).get(rule.card_id),
                               pps_sia_group_eligible, merchant_name, channel, rate_mode, transaction_currency)

    scored.sort(
        key=lambda x: (
            x["estimated_miles"] if x["estimated_miles"] is not None else x["earn_rate_mpd"],
            x["earn_rate_mpd"],
        ),
        reverse=True,
    )
    return scored[:top_n]
