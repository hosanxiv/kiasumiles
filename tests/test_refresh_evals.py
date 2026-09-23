"""Source-neutral regression scenarios for the September rule review."""
import pytest

from kiasumiles.data.loader import CardRule
from kiasumiles.engine.router import effective_mpd, rank_cards
from kiasumiles import tools
from kiasumiles.data.loader import MerchantRecord
from dataclasses import replace
from datetime import date, timedelta


def test_vim_currency_rounding_and_exclusions(ocbc_rewards):
    card = replace(ocbc_rewards, card_id="uob_vim", eligible_mccs=[], eligible_merchants=[],
                   earn_rate_mpd=1.4, base_rate_mpd=1.4, cap_sgd=None, min_spend=0)
    for currency, country, expected in [("SGD", "US", 6), ("USD", "US", 12), ("USD", "SG", 6)]:
        row = rank_cards("5411", [card], False, 1, "Grocer", "online", "guaranteed", 9.99,
                         transaction_currency=currency, payment_gateway_country=country)[0]
        assert row["estimated_miles"] == expected
    for mcc, name in [("8062", "Hospital"), ("5541", "Shell"), ("5411", "IPAYMY123")]:
        assert rank_cards(mcc, [card], False, 1, name, "online", "guaranteed", 10)[0]["estimated_miles"] == 0


@pytest.mark.parametrize("currency,country", [("USD", None), (None, "US"), (None, None)])
def test_vim_unknown_overseas_and_no_reserve_luxury(ocbc_rewards, currency, country):
    card = replace(ocbc_rewards, card_id="uob_vim", eligible_mccs=[], eligible_merchants=[],
                   earn_rate_mpd=1.4, base_rate_mpd=1.4, cap_sgd=None, min_spend=0)
    for mode, expected in [("guaranteed", 6), ("conditional", 12)]:
        row = rank_cards("5411", [card], False, 1, "Grocer", "fcy", mode, 9.99,
                         transaction_currency=currency, payment_gateway_country=country)[0]
        assert row["estimated_miles"] == expected
    row = rank_cards("5691", [card], False, 1, "Chanel", "contactless", "conditional", 10,
                     transaction_currency="SGD")[0]
    assert row["estimated_miles"] == 14
    assert row["cap_sgd"] is None


@pytest.mark.parametrize("merchant,channel,currency,potential", [
    ("Chanel", "contactless", "SGD", 20),
    ("Chanel", "online", "SGD", 16),
    ("Chanel", "contactless", "USD", 24),
    ("Chanel Takashimaya department store", "contactless", "SGD", 16),
    ("Chanelle Cafe", "contactless", "SGD", 16),
])
def test_reserve_luxury_candidate_not_guaranteed(ocbc_rewards, merchant, channel, currency, potential):
    card = replace(ocbc_rewards, card_id="uob_reserve", eligible_mccs=[], eligible_merchants=[],
                   earn_rate_mpd=1.6, base_rate_mpd=1.6, cap_sgd=None, min_spend=0)
    row = rank_cards("5691", [card], False, 1, merchant, channel, "conditional", 10,
                     transaction_currency=currency, payment_gateway_country="FR" if currency == "USD" else "SG")[0]
    assert row["estimated_miles"] == potential


@pytest.mark.parametrize("amount,base,potential", [(4.99, 0, 0), (5, 8, 10),
    (20000, 32000, 40000), (20005, 32008, 40008)])
def test_reserve_luxury_cap_and_guaranteed_fallback(ocbc_rewards, amount, base, potential):
    card = replace(ocbc_rewards, card_id="uob_reserve", eligible_mccs=[], eligible_merchants=[],
                   earn_rate_mpd=1.6, base_rate_mpd=1.6, cap_sgd=None, min_spend=0)
    for mode, expected in [("guaranteed", base), ("conditional", potential)]:
        row = rank_cards("5691", [card], False, 1, "Chanel", "contactless", mode, amount,
                         transaction_currency="SGD")[0]
        assert row["estimated_miles"] == expected
        assert row["cap_sgd"] == 20000
        assert any("Outlet eligibility is unconfirmed" in note for note in row["gotchas"])


@pytest.mark.parametrize("mcc,name,expected", [
    ("4900", "Utility", 0), ("8062", "Hospital", 0), ("6300", "Insurance", 0),
    ("5541", "Shell", 0), ("5542", "SPC", 0), ("5411", "AMAZE123", 0),
    ("5411", "AXS-PAYMENT123", 0), ("5411", "YOUTRIP.COM123", 0),
    ("5411", "PAYPAL *PLUS500.COM", 0), ("5411", "FlashPayATU123", 0),
    ("8220", "University", 16), ("5411", "Grocer", 16),
])
def test_reserve_product_exclusions(ocbc_rewards, mcc, name, expected):
    card = replace(ocbc_rewards, card_id="uob_reserve", eligible_mccs=[], eligible_merchants=[],
                   earn_rate_mpd=1.6, base_rate_mpd=1.6, cap_sgd=None, min_spend=0)
    for mode in ("guaranteed", "conditional"):
        row = rank_cards(mcc, [card], False, 1, name, "online", mode, 10, transaction_currency="SGD")[0]
        assert row["estimated_miles"] == expected


@pytest.mark.parametrize("currency,country,guaranteed,potential", [
    ("USD", "US", 24, 24), ("USD", "SG", 16, 16), ("SGD", "US", 16, 16),
    ("MYR", "MY", 24, 24), ("USD", None, 16, 24), (None, "US", 16, 24),
    (None, None, 16, 24),
])
def test_reserve_currency_gateway(ocbc_rewards, currency, country, guaranteed, potential):
    card = replace(ocbc_rewards, card_id="uob_reserve", eligible_mccs=[], eligible_merchants=[],
                   earn_rate_mpd=1.6, base_rate_mpd=1.6, cap_sgd=None, min_spend=0)
    for mode, expected in [("guaranteed", guaranteed), ("conditional", potential)]:
        row = rank_cards("5411", [card], False, 1, "Grocer", "fcy", mode, 10,
                         transaction_currency=currency, payment_gateway_country=country)[0]
        assert row["estimated_miles"] == expected


@pytest.mark.parametrize("recurring,expected", [(True, 0), (False, 150)])
def test_beyond_recurring_exclusion(ocbc_rewards, recurring, expected):
    card = replace(ocbc_rewards, card_id="stanChart_beyond", eligible_mccs=[],
                   eligible_merchants=[], cap_sgd=None, min_spend=0)
    row = rank_cards("5411", [card], False, 1, "Grocer", "online", "guaranteed", 100,
                     is_recurring=recurring)[0]
    assert row["estimated_miles"] == expected


@pytest.mark.parametrize("handler", [tools.lookup_hosted, tools.compare_payment_methods])
def test_recurring_input_rejects_non_boolean_before_wallet(handler):
    with pytest.raises(ValueError, match="is_recurring"):
        handler("Grocer", [], is_recurring="false")


@pytest.mark.parametrize("matched", [True, False])
def test_recurring_reaches_hosted_and_rest_lookup_and_compare(monkeypatch, ocbc_rewards, matched):
    from kiasumiles import hosted
    from starlette.testclient import TestClient
    card = replace(ocbc_rewards, card_id="stanChart_beyond", card_name="Beyond",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None, min_spend=0)
    monkeypatch.setattr(tools._loader, "_cards", [card])
    monkeypatch.setattr(tools._loader, "_merchants", [
        MerchantRecord("Grocer", None, "any", "5411", "Grocery", "medium", 1, "")
    ] if matched else [])
    arguments = dict(merchant="Grocer", cards=[card.card_id], category="grocery", amount_sgd=100)
    client = TestClient(hosted.app)
    for recurring, expected in [(True, 0), (False, 150), (True, 0)]:
        payload = {**arguments, "is_recurring": recurring}
        lookup = hosted.kiasumiles_lookup(**payload)
        comparison = hosted.kiasumiles_compare_payment_methods(**payload)
        assert lookup["recommendations"][0]["estimated_miles"] == expected
        assert lookup["wallet_stored"] is False
        assert all(method["best_guaranteed"]["estimated_miles"] == expected for method in comparison["methods"])
        for route, key in [("lookup", "recommendations"), ("compare-payment-methods", "methods")]:
            response = client.post("/api/chatgpt/" + route, json=payload)
            assert response.status_code == 200
            rows = response.json()[key]
            assert all((row if key == "recommendations" else row["best_guaranteed"])["estimated_miles"] == expected for row in rows)
            assert client.post("/api/chatgpt/" + route, json={**payload, "is_recurring": "false"}).status_code == 400


@pytest.mark.parametrize("mcc,name", [("4900", "Utilities"), ("8062", "Hospital"),
    ("6300", "Insurance"), ("8220", "University"), ("5411", "AXS"),
    ("5411", "EZ-LINK TOP-UP KIOSK"), ("5411", "PAYPAL * BIZCONSULTA")])
def test_beyond_exclusions(ocbc_rewards, mcc, name):
    card = replace(ocbc_rewards, card_id="stanChart_beyond", bank="Standard Chartered",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   min_spend=0, earn_rate_mpd=1.5, base_rate_mpd=1.5, earn_block_sgd=1)
    row = rank_cards(mcc, [card], False, 1, name, "online", "guaranteed", 100)[0]
    assert row["estimated_miles"] == 0


@pytest.mark.parametrize("currency,amount,expected", [("SGD", 100, 150), ("USD", 100, 300),
    ("SGD", 1.2, 1.8), ("USD", 1.2, 3.6)])
def test_beyond_ordinary_currency_rate(ocbc_rewards, currency, amount, expected):
    card = replace(ocbc_rewards, card_id="stanChart_beyond", bank="Standard Chartered",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   min_spend=0, earn_rate_mpd=1.5, base_rate_mpd=1.5, earn_block_sgd=1)
    row = rank_cards("5411", [card], False, 1, "Example", "online", "guaranteed", amount,
                     transaction_currency=currency)[0]
    assert row["estimated_miles"] == expected
    assert any("aggregated" in note for note in row["gotchas"])


@pytest.mark.parametrize("mcc,name,expected", [
    ("4900", "Utilities", 0), ("8220", "Education", 0),
    ("6300", "Insurance", 0), ("6532", "Stored value", 0),
    ("9399", "Government", 0), ("5411", "AMAZE* AXS", 0),
    ("4111", "BUS/MRT", 0), ("5411", "Youtrip Singapore SG", 0),
    ("8062", "Hospital", 16), ("5411", "Grocer", 16),
])
def test_ultima_exclusions_preserve_hospital_exception(ocbc_rewards, mcc, name, expected):
    card = replace(ocbc_rewards, card_id="citi_ultima", bank="Citibank",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   min_spend=0, earn_rate_mpd=1.6, base_rate_mpd=1.6, earn_block_sgd=1)
    row = rank_cards(mcc, [card], False, 1, name, "online", "guaranteed", 10)[0]
    assert row["estimated_miles"] == expected


@pytest.mark.parametrize("channel,currency,amount,expected", [
    ("online", None, 1.2, 2), ("online", None, 9.99, 16),
    ("fcy", None, 1.2, 2.4), ("fcy", None, 9.99, 20),
    ("online", "USD", 9.99, 20), ("fcy", "SGD", 9.99, 16),
])
def test_ultima_points_rounding_and_currency(ocbc_rewards, channel, currency, amount, expected):
    card = replace(ocbc_rewards, card_id="citi_ultima", bank="Citibank",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   min_spend=0, earn_rate_mpd=1.6, base_rate_mpd=1.6, earn_block_sgd=1)
    row = rank_cards("5411", [card], False, 1, "Example", channel, "guaranteed", amount,
                     transaction_currency=currency)[0]
    assert row["estimated_miles"] == expected
    assert "nearest point" in row["cap_summary"]


@pytest.mark.parametrize("channel,currency,mode,amount,expected", [
    ("online", None, "guaranteed", 9.99, 6),
    ("fcy", None, "guaranteed", 9.99, 10),
    ("fcy", None, "conditional", 9.99, 16),
    ("fcy", None, "guaranteed", 4.99, 0),
    ("online", "USD", "guaranteed", 9.99, 10),
    ("online", "USD", "conditional", 9.99, 16),
    ("fcy", "SGD", "conditional", 9.99, 6),
])
def test_maybank_vi_currency_rates(ocbc_rewards, channel, currency, mode, amount, expected):
    card = replace(ocbc_rewards, card_id="maybank_vi", bank="Maybank",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   min_spend=0, earn_rate_mpd=1.2, base_rate_mpd=1.2, earn_block_sgd=5)
    row = rank_cards("5411", [card], False, 1, "Example", channel, mode, amount,
                     transaction_currency=currency)[0]
    assert row["estimated_miles"] == expected


@pytest.mark.parametrize("mcc,merchant,channel,mode,expected", [
    ("4900", "Utility", "fcy", "conditional", 0),
    ("5411", "AXS", "online", "conditional", 0),
    ("4111", "SimplyGo", "online", "conditional", 0),
    ("6300", "Insurance", "online", "guaranteed", 0),
    ("6300", "Insurance", "online", "conditional", 3600),
    ("6300", "Insurance", "fcy", "conditional", 0),
    ("8220", "University", "online", "guaranteed", 4800),
])
def test_maybank_vi_exclusions_and_insurance_cap(ocbc_rewards, mcc, merchant, channel, mode, expected):
    card = replace(ocbc_rewards, card_id="maybank_vi", bank="Maybank",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   min_spend=0, earn_rate_mpd=1.2, base_rate_mpd=1.2, earn_block_sgd=5)
    row = rank_cards(mcc, [card], False, 1, merchant, channel, mode, 4000)[0]
    assert row["estimated_miles"] == expected


@pytest.mark.parametrize("card_id,channel,prior,amount,expected", [
    ("amex_pps", "online", 0, 3800, 4940),
    ("amex_pps", "online", 3790, 20, 27),
    ("amex_solitaire_pps", "online", 3790, 20, 28),
    ("amex_pps", "fcy", 3790, 20, 33),
    ("amex_solitaire_pps", "fcy", 3790, 20, 37),
    ("amex_pps", "online", 9.99, .01, 13),
    ("amex_pps", "online", 0, 9.99, 0),
])
def test_pps_monthly_increment(ocbc_rewards, card_id, channel, prior, amount, expected):
    card = replace(ocbc_rewards, card_id=card_id, bank="American Express",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   earn_rate_mpd=1.3, base_rate_mpd=1.3, earn_block_sgd=10)
    row = rank_cards("5411", [card], False, 1, "Example", channel, "guaranteed", amount,
                     pps_prior_spend_sgd={card_id: prior})[0]
    assert row["estimated_miles"] == expected
    assert "cumulative" in row["cap_summary"]


def test_pps_prior_spending_is_per_card(ocbc_rewards):
    cards = [replace(ocbc_rewards, card_id=cid, bank="American Express",
             eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
             earn_rate_mpd=1.3, base_rate_mpd=1.3, earn_block_sgd=10)
             for cid in ("amex_pps", "amex_solitaire_pps")]
    rows = {r["card_id"]: r for r in rank_cards("5411", cards, False, 2, "Example", "fcy",
            "guaranteed", 10, pps_prior_spend_sgd={"amex_pps": 3800})}
    assert rows["amex_pps"]["estimated_miles"] == 20
    assert rows["amex_solitaire_pps"]["estimated_miles"] == 13
    assert "monthly_spend_unknown" in rows["amex_solitaire_pps"]["reason_codes"]


@pytest.mark.parametrize("eligible,prior,mode,expected", [(True, 9.99, "guaranteed", 20),
    (None, 9.99, "guaranteed", 0), (None, 9.99, "conditional", 20),
    (False, 9.99, "guaranteed", 13)])
def test_pps_group_purchase_bucket(ocbc_rewards, eligible, prior, mode, expected):
    card = replace(ocbc_rewards, card_id="amex_pps", bank="American Express",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   earn_rate_mpd=1.3, base_rate_mpd=1.3, earn_block_sgd=10)
    row = rank_cards("4511", [card], False, 1, "Singapore Airlines", "online", mode, .01,
                     pps_prior_spend_sgd={"amex_pps": prior}, pps_sia_group_eligible=eligible)[0]
    assert row["estimated_miles"] == expected


@pytest.mark.parametrize("value", [{"amex_pps": -1}, {"amex_pps": True},
    {"amex_pps": float("nan")}, {"amex_pps": float("inf")}, {"other": 10}, []])
def test_pps_invalid_spending_rejected(value):
    with pytest.raises(ValueError):
        rank_cards("5411", [], False, 1, pps_prior_spend_sgd=value)


@pytest.mark.parametrize("merchant,channel", [("Pelago", "mobile_contactless"),
    ("Singapore Airlines", "fcy"), ("Other", "online")])
def test_pps_invalid_group_claim_rejected(merchant, channel):
    with pytest.raises(ValueError):
        rank_cards("4511", [], False, 1, merchant, channel, pps_sia_group_eligible=True)


def test_pps_hosted_and_rest_requests_are_stateless(monkeypatch, ocbc_rewards):
    from kiasumiles import hosted
    from starlette.testclient import TestClient
    card = replace(ocbc_rewards, card_id="amex_pps", card_name="Amex PPS Club", bank="American Express",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   earn_rate_mpd=1.3, base_rate_mpd=1.3, earn_block_sgd=10)
    monkeypatch.setattr(tools._loader, "_cards", [card])
    monkeypatch.setattr(tools._loader, "_merchants", [])
    arguments = dict(merchant="Example", cards=[card.card_id], category="grocery",
                     channel="fcy", amount_sgd=10)
    supplied = hosted.kiasumiles_lookup(**arguments, pps_prior_spend_sgd={card.card_id: 3800})
    assert supplied["recommendations"][0]["estimated_miles"] == 20
    assert supplied["wallet_stored"] is False
    assert hosted.kiasumiles_lookup(**arguments)["recommendations"][0]["estimated_miles"] == 13
    client = TestClient(hosted.app)
    response = client.post("/api/chatgpt/lookup", json={**arguments, "pps_prior_spend_sgd": {card.card_name: 3800}})
    assert response.status_code == 200
    assert response.json()["recommendations"][0]["estimated_miles"] == 20
    assert client.post("/api/chatgpt/lookup", json={**arguments, "pps_prior_spend_sgd": {card.card_id: -1}}).status_code == 400


@pytest.mark.parametrize("mcc", ["6300", "8062"])
def test_pps_insurance_healthcare_not_guaranteed(ocbc_rewards, mcc):
    card = replace(ocbc_rewards, card_id="amex_pps", bank="American Express",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   earn_rate_mpd=1.3, base_rate_mpd=1.3, earn_block_sgd=10)
    for mode in ("guaranteed", "conditional"):
        row = rank_cards(mcc, [card], False, 1, "Example", "online", mode, 30,
                         pps_prior_spend_sgd={card.card_id: 0})[0]
        assert row["estimated_miles"] == (0 if mode == "guaranteed" else 39)
        assert row["rate_status"] == mode


@pytest.mark.parametrize("card_id", ["amex_krisflyer", "amex_krisflyer_ascend", "amex_highflyer",
                                    "amex_plat_charge", "amex_plat_credit", "amex_centurion"])
@pytest.mark.parametrize("mcc,merchant", [("4900", "Utility"), ("6540", "Wallet load"),
    ("5541", "SPC Bukit Timah"), ("5999", "SingPost"), ("5999", "SAM"),
    ("4111", "BUS/MRT"), ("4111", "SimplyGo"), ("5999", "GrabPay top-up")])
def test_amex_shared_exclusions(ocbc_rewards, card_id, mcc, merchant):
    card = replace(ocbc_rewards, card_id=card_id, bank="American Express",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   earn_rate_mpd=1.2, base_rate_mpd=1.2)
    assert effective_mpd(card, mcc, False, merchant, "contactless") == 0
    for mode in ("guaranteed", "conditional"):
        assert rank_cards(mcc, [card], False, 1, merchant, "contactless", mode, 30)[0]["estimated_miles"] == 0


@pytest.mark.parametrize("card_id,expected", [("amex_krisflyer", 0), ("amex_highflyer", 0),
    ("amex_plat_credit", 0), ("amex_plat_charge", 1.2), ("amex_centurion", 1.2)])
@pytest.mark.parametrize("mcc", ["8211", "8299", "8398"])
def test_amex_education_charity_exception(ocbc_rewards, card_id, expected, mcc):
    card = replace(ocbc_rewards, card_id=card_id, bank="American Express",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   earn_rate_mpd=1.2, base_rate_mpd=1.2)
    assert effective_mpd(card, mcc, False, "Example", "online") == expected


@pytest.mark.parametrize("merchant,mcc", [("Esso", "5541"), ("Sam's Cafe", "5812"),
    ("Grab", "4121"), ("Private Clinic", "8011"), ("Private Hospital", "8062")])
def test_amex_exclusions_do_not_overmatch(ocbc_rewards, merchant, mcc):
    card = replace(ocbc_rewards, card_id="amex_plat_charge", bank="American Express",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   earn_rate_mpd=1.2, base_rate_mpd=1.2)
    assert effective_mpd(card, mcc, False, merchant, "contactless") == 1.2


@pytest.fixture
def ocbc_rewards():
    return CardRule(
        card_id="ocbc_rewards", card_name="OCBC Rewards Card", bank="OCBC",
        network="Mastercard", eligible_mccs=["5651", "5311"],
        eligible_merchants=["Amazon", "Shopee", "Guardian"],
        earn_rate_mpd=4, base_rate_mpd=.4, cap_sgd=1110,
        cap_period="calendar_month", min_spend=0, requires_amaze=False,
        amaze_fee_pct=0, earn_block_sgd=5,
    )


@pytest.mark.parametrize("mcc,channel,amount,expected", [
    ("3000", "online", 30, 84), ("3350", "online", 30, 84),
    ("3351", "online", 30, 36), ("5411", "contactless", 30, 36),
    ("7298", "contactless", 30, 12), ("4900", "contactless", 30, 0),
    ("6300", "contactless", 30, 4.8), ("8062", "contactless", 3005, 480),
    ("6300", "fcy", 30, 84), ("5411", "fcy", 10005, 28014),
])
def test_horizon_category_and_currency_rules(ocbc_rewards, mcc, channel, amount, expected):
    card = replace(ocbc_rewards, card_id="maybank_horizon", bank="Maybank",
                   eligible_mccs=["4511"], eligible_merchants=[],
                   earn_rate_mpd=2.8, base_rate_mpd=1.2, cap_sgd=10000, min_spend=800)
    row = rank_cards(mcc, [card], False, 1, "Example", channel, "conditional", amount)[0]
    assert row["estimated_miles"] == expected


@pytest.mark.parametrize("mcc,channel,amount,guaranteed,conditional", [
    ("8062", "contactless", 4.99, 0, 0),
    ("8062", "contactless", 5, 0, .8),
    ("8062", "contactless", 3000, 0, 480),
    ("4511", "online", 10005, 12006, 28006),
    ("4900", "fcy", 30, 0, 0),
])
def test_horizon_guarantees_and_caps(ocbc_rewards, mcc, channel, amount, guaranteed, conditional):
    card = replace(ocbc_rewards, card_id="maybank_horizon", bank="Maybank",
                   eligible_mccs=["4511"], eligible_merchants=[],
                   earn_rate_mpd=2.8, base_rate_mpd=1.2, cap_sgd=10000, min_spend=800)
    for mode, expected in [("guaranteed", guaranteed), ("conditional", conditional)]:
        row = rank_cards(mcc, [card], False, 1, "Example", channel, mode, amount)[0]
        assert row["estimated_miles"] == expected


@pytest.mark.parametrize("merchant", ["YouTrip", "SINGTEL DASH", "RAZERPAY*TOPUP", "Instarem", "EZ-LINK"])
def test_horizon_prepaid_payment_exclusions(ocbc_rewards, merchant):
    card = replace(ocbc_rewards, card_id="maybank_horizon", bank="Maybank",
                   eligible_mccs=["4511"], eligible_merchants=[],
                   earn_rate_mpd=2.8, base_rate_mpd=1.2, cap_sgd=10000, min_spend=800)
    for channel in ("contactless", "fcy"):
        assert effective_mpd(card, "5411", False, merchant, channel) == 0


@pytest.mark.parametrize("mcc,merchant", [
    ("4900", "Utilities"), ("8062", "Hospital"), ("6540", "Wallet top-up"),
    ("6300", "Insurance"), ("5814", "AXS*Starbucks"),
])
def test_smart_exclusions_do_not_earn_base_miles(ocbc_rewards, mcc, merchant):
    card = replace(ocbc_rewards, card_id="stanChart_smart", bank="Standard Chartered",
                   eligible_mccs=[], eligible_merchants=["Starbucks", "SimplyGo"],
                   earn_rate_mpd=32/3.45, base_rate_mpd=1.6/3.45, cap_sgd=None,
                   min_spend=1500, earn_block_sgd=1)
    for mode in ("guaranteed", "conditional"):
        row = rank_cards(mcc, [card], False, 1, merchant, "contactless", mode, 30)[0]
        assert row["estimated_miles"] == 0


def test_smart_simplygo_fare_is_not_a_wallet_topup(ocbc_rewards):
    card = replace(ocbc_rewards, card_id="stanChart_smart", bank="Standard Chartered",
                   eligible_mccs=[], eligible_merchants=["SimplyGo"],
                   earn_rate_mpd=32/3.45, base_rate_mpd=1.6/3.45, cap_sgd=None,
                   min_spend=1500, earn_block_sgd=1)
    assert effective_mpd(card, "4111", False, "SimplyGo", "contactless") == pytest.approx(9.27536231884)


@pytest.mark.parametrize("spend,merchant,expected", [
    (799.99, "Starbucks", .4638), (800, "Starbucks", 7.4203),
    (1499.99, "Starbucks", 7.4203), (1500, "Starbucks", 9.2754),
    (800, "Other Cafe", .4638), (1500, "Other Cafe", .9275),
    (1500, "AXS*Starbucks", 0),
])
def test_smart_confirmed_statement_tiers(monkeypatch, ocbc_rewards, spend, merchant, expected):
    card = replace(ocbc_rewards, card_id="stanChart_smart", bank="Standard Chartered",
                   eligible_mccs=[], eligible_merchants=["Starbucks"],
                   earn_rate_mpd=32/3.45, base_rate_mpd=1.6/3.45, cap_sgd=None,
                   min_spend=1500, earn_block_sgd=1)
    monkeypatch.setattr(tools._loader, "_cards", [card])
    monkeypatch.setattr(tools._loader, "_merchants", [])
    result = tools.lookup_hosted(merchant, [card.card_id], category="dining",
                                smart_statement_spend_sgd=spend)
    for key in ("recommendations", "conditional_recommendations"):
        assert result[key][0]["earn_rate_mpd"] == expected
    if merchant == "Starbucks":
        unknown = tools.lookup_hosted(merchant, [card.card_id], category="dining")
        assert unknown["recommendations"][0]["earn_rate_mpd"] == .4638
        assert unknown["conditional_recommendations"][0]["rate_status"] == "conditional"
        compared = tools.compare_payment_methods(merchant, [card.card_id], category="dining",
                                                  smart_statement_spend_sgd=spend)
        assert all(method["best_guaranteed"]["earn_rate_mpd"] == expected
                   for method in compared["methods"])
    if merchant == "Other Cafe":
        unknown = tools.lookup_hosted(merchant, [card.card_id], category="dining")
        assert unknown["recommendations"][0]["earn_rate_mpd"] == .4638
        assert unknown["conditional_recommendations"][0]["earn_rate_mpd"] == .9275
        assert unknown["conditional_recommendations"][0]["rate_status"] == "conditional"


@pytest.mark.parametrize("spend", [-1, True, "800", float("inf"), float("nan")])
def test_smart_statement_spend_validation(spend):
    with pytest.raises(ValueError):
        tools.lookup_hosted("Starbucks", [], smart_statement_spend_sgd=spend)


@pytest.mark.parametrize("merchant,channel,expected", [
    ("CHAGEE", "app", 10),
    ("CHAGEE", "online", .14),
    ("CHAGEE", "mobile_contactless", .14),
    ("CHAGEE", None, .14),
    ("Cold Storage On The Go", "contactless", .14),
    ("Cold Storage", "contactless", 10),
])
def test_yuu_partner_restrictions(ocbc_rewards, merchant, channel, expected):
    card = replace(ocbc_rewards, card_id="dbs_yuu_visa", bank="DBS",
                   eligible_mccs=[], eligible_merchants=["CHAGEE", "Cold Storage"],
                   earn_rate_mpd=10, base_rate_mpd=.14, min_spend=800)
    assert effective_mpd(card, "5812", False, merchant, channel) == expected


@pytest.mark.parametrize("merchant,amount,guaranteed,conditional", [
    ("Cold Storage", 3, .83, 30),
    ("SimplyGo", 3, .42, 30),
    ("Cold Storage", 1000, 277.78, 8277.78),
    ("SimplyGo", 1000, 138.89, 8138.89),
])
def test_yuu_base_and_shared_bonus_cap(ocbc_rewards, merchant, amount, guaranteed, conditional):
    card = replace(ocbc_rewards, card_id="dbs_yuu_visa", bank="DBS",
                   eligible_mccs=[], eligible_merchants=["Cold Storage", "SimplyGo"],
                   earn_rate_mpd=10, base_rate_mpd=0.1388888889,
                   min_spend=800, cap_sgd=822.86, earn_block_sgd=1)
    for mode, expected in [("guaranteed", guaranteed), ("conditional", conditional)]:
        row = rank_cards("5411", [card], False, 1, merchant, "contactless", mode, amount)[0]
        assert row["estimated_miles"] == expected
        assert "four" in row["condition_summary"]
        assert "8,000 bonus miles" in row["cap_summary"]


def test_yuu_outlet_exclusion_survives_lookup(monkeypatch, ocbc_rewards):
    card = replace(ocbc_rewards, card_id="dbs_yuu_visa", bank="DBS",
                   eligible_mccs=[], eligible_merchants=["Cold Storage"],
                   earn_rate_mpd=10, base_rate_mpd=.14, min_spend=800)
    monkeypatch.setattr(tools._loader, "_cards", [card])
    monkeypatch.setattr(tools._loader, "_merchants", [
        MerchantRecord("Cold Storage", "On The Go", "any", "5411", "Grocery", "medium", 1, "")])
    row = tools.lookup_hosted("Cold Storage", ["dbs_yuu_visa"], outlet="On The Go",
                              channel="contactless")["conditional_recommendations"][0]
    assert row["earn_rate_mpd"] == .14


def test_yuu_app_route_is_reachable(monkeypatch, ocbc_rewards):
    card = replace(ocbc_rewards, card_id="dbs_yuu_visa", bank="DBS",
                   eligible_mccs=[], eligible_merchants=["CHAGEE"],
                   earn_rate_mpd=10, base_rate_mpd=.14, min_spend=800)
    monkeypatch.setattr(tools._loader, "_cards", [card])
    monkeypatch.setattr(tools._loader, "_merchants", [
        MerchantRecord("CHAGEE", None, "online", "5812", "Dining", "medium", 1, "")])
    result = tools.lookup_hosted("CHAGEE", ["dbs_yuu_visa"], channel="in-app")
    assert result["conditional_recommendations"][0]["earn_rate_mpd"] == 10
    methods = tools.compare_payment_methods("CHAGEE", ["dbs_yuu_visa"])["methods"]
    app = next(row for row in methods if row["payment_method"] == "app")
    assert app["best_if_conditions_met"]["earn_rate_mpd"] == 10


@pytest.mark.parametrize("mcc", "4784 4829 4900 5047 5199 5960 5993 6010 6011 6012 6050 6051 6211 6300 6381 6399 6513 6529 6530 6534 6540 7349 7511 7523 7995 8062 8211 8220 8241 8244 8249 8299 8398 8651 8661 8699 8999 9211 9222 9223 9311 9399 9402 9405".split())
def test_yuu_excluded_categories_do_not_earn_base(ocbc_rewards, mcc):
    card = replace(ocbc_rewards, card_id="dbs_yuu_visa", bank="DBS",
                   base_rate_mpd=.1388888889, eligible_mccs=[], eligible_merchants=["Guardian"])
    for mode in ("guaranteed", "conditional"):
        row = rank_cards(mcc, [card], False, 1, "Guardian", "contactless", mode, 30)[0]
        assert row["estimated_miles"] == 0
        assert "transaction_excluded" in row["reason_codes"]


@pytest.mark.parametrize("merchant", ["AXS", "PAYPAL AXS PTE LTD", "Singtel Dash", "AMAZE*Guardian", "SHOPEEPAY", "EZ-LINK", "YouTrip"])
def test_yuu_excluded_descriptors(ocbc_rewards, merchant):
    card = replace(ocbc_rewards, card_id="dbs_yuu_visa", bank="DBS", eligible_mccs=[])
    assert effective_mpd(card, "5411", False, merchant, "online") == 0


def test_yuu_exclusions_do_not_extend_to_adjacent_categories_or_other_cards(ocbc_rewards):
    card = replace(ocbc_rewards, card_id="dbs_yuu_visa", bank="DBS", eligible_mccs=[])
    assert effective_mpd(card, "8061", False, "Sample", "online") == .4
    assert effective_mpd(ocbc_rewards, "6381", False, "Guardian", "online") == 4


@pytest.mark.parametrize("card_id", ["dbs_altitude_visa", "dbs_altitude_amex", "dbs_insignia", "dbs_vantage", "dbs_wwmc"])
def test_dbs_rewards_exclusions(ocbc_rewards, card_id):
    card = replace(ocbc_rewards, card_id=card_id, bank="DBS", eligible_mccs=[],
                   eligible_merchants=[], earn_rate_mpd=1.3, base_rate_mpd=1.3)
    for merchant, mcc in [("Utility", "4900"), ("Hospital", "8062"), ("SAM - BILL", "5411"), ("AMAZE*SHOP", "5411")]:
        row = rank_cards(mcc, [card], False, 1, merchant, "online", "guaranteed", 30)[0]
        assert row["estimated_miles"] == 0
    assert effective_mpd(card, "5411", False, "Supermarket", "contactless") == {"dbs_insignia": 1.6, "dbs_vantage": 1.5}.get(card_id, 1.3)


@pytest.mark.parametrize("amount,miles", [(4.99, 6), (5, 6), (9.99, 12), (30, 38)])
def test_chromo_miles_choice_and_rounding(ocbc_rewards, amount, miles):
    card = replace(ocbc_rewards, card_id="dbs_chromo", bank="DBS", eligible_mccs=[],
                   eligible_merchants=[], earn_rate_mpd=1.3, base_rate_mpd=0,
                   cap_sgd=None, earn_block_sgd=1)
    row = rank_cards("5411", [card], False, 1, "Supermarket", "contactless", amount_sgd=amount)[0]
    assert row["estimated_miles"] == miles
    assert row["rate_status"] == "conditional"
    assert "10th" in " ".join(row["gotchas"])
    guaranteed = rank_cards("5411", [card], False, 1, "Supermarket", "contactless", "guaranteed", amount)[0]
    assert guaranteed["estimated_miles"] == 0
    assert effective_mpd(card, "5411", False, "Supermarket", "fcy") == 0
    assert effective_mpd(card, "4900", False, "Utility", "online") == 0
    assert effective_mpd(card, "5411", False, "SINGTELDASH", "online") == 0
    assert effective_mpd(card, "5411", False, "SMOOVEPAY", "online") == 0


@pytest.mark.parametrize("merchant,mcc,expected", [
    ("Uniqlo", "5651", 4),
    ("Guardian", "5912", 4),
    ("Unlisted merchant", "5812", .4),
    ("Amazon", "5411", .4),
    ("Shopee Pay", "5262", 0),
    (None, "5912", .4),
])
def test_ocbc_eligibility_routes(ocbc_rewards, merchant, mcc, expected):
    assert effective_mpd(ocbc_rewards, mcc, False, merchant, "online") == expected


def test_ocbc_cap_and_unknown_progress(ocbc_rewards):
    conditional = rank_cards("5651", [ocbc_rewards], False, 1,
                             "Uniqlo", "contactless", amount_sgd=1120)[0]
    assert conditional["estimated_miles"] == 4448
    assert conditional["rate_status"] == "conditional"
    guaranteed = rank_cards("5651", [ocbc_rewards], False, 1,
                            "Uniqlo", "contactless", "guaranteed", 1120)[0]
    assert guaranteed["estimated_miles"] == 448


@pytest.mark.parametrize("day,rate", [(date(2026,6,30),4), (date(2026,7,1),6), (date(2027,3,31),6), (date(2027,4,1),4)])
def test_ocbc_promotion_dates(ocbc_rewards, day, rate):
    row = rank_cards("5311", [ocbc_rewards], False, 1, "Shopee", "online", as_of=day)[0]
    assert row["earn_rate_mpd"] == rate


@pytest.mark.parametrize("amount,miles", [(4.99,0), (5,30), (1000,6000), (1005,6020), (1115,6446), (1120,6448)])
def test_ocbc_promotion_separate_caps(ocbc_rewards, amount, miles):
    row = rank_cards("5311", [ocbc_rewards], False, 1, "Shopee", "online", amount_sgd=amount, as_of=date(2026,9,22))[0]
    assert row["estimated_miles"] == miles
    assert "2,000" in row["cap_summary"]
    fallback = rank_cards("5311", [ocbc_rewards], False, 1, "Shopee", "online", "guaranteed", amount, as_of=date(2026,9,22))[0]
    assert fallback["earn_rate_mpd"] == .4


@pytest.mark.parametrize("merchant,mcc", [("Shopee Pay","6540"), ("Shopee","5411"), ("Lazada","5411"), ("Watsons","8062"), ("AXS","5311")])
def test_ocbc_promotion_does_not_override_exclusions(ocbc_rewards, merchant, mcc):
    row = rank_cards(mcc, [ocbc_rewards], False, 1, merchant, "online", as_of=date(2026,9,22))[0]
    assert row["earn_rate_mpd"] == 0


@pytest.mark.parametrize("outlet,expected", [(None, None), ("East", "5651"), ("West", "5812"), ("Other", None)])
def test_outlet_ambiguity_requires_clarification(monkeypatch, ocbc_rewards, outlet, expected):
    monkeypatch.setattr(tools._loader, "_cards", [ocbc_rewards])
    monkeypatch.setattr(tools._loader, "_merchants", [
        MerchantRecord("Sample Shop", "East", "any", "5651", "Clothing", "medium", 1, ""),
        MerchantRecord("Sample Shop", "West", "any", "5812", "Dining", "medium", 1, ""),
    ])
    result = tools.lookup_hosted("Sample Shop", ["ocbc_rewards"], outlet=outlet)
    if expected:
        assert result["mcc"] == expected
    else:
        assert result["requires_clarification"] is True
        assert result["recommendations"] == []


@pytest.mark.parametrize("eligibility,guaranteed,conditional", [(None, None, 1), (False, 0, 0), (True, .4, 1)])
def test_chocolate_account_eligibility(monkeypatch, ocbc_rewards, eligibility, guaranteed, conditional):
    card = replace(ocbc_rewards, card_id="chocolate_visa", card_name="Chocolate Visa",
                   bank="Chocolate", eligible_mccs=[], eligible_merchants=[],
                   earn_rate_mpd=1, cap_sgd=2000, earn_block_sgd=1)
    monkeypatch.setattr(tools._loader, "_cards", [card])
    monkeypatch.setattr(tools._loader, "_merchants", [
        MerchantRecord("Sample Grocer", None, "any", "5411", "Grocery", "medium", 1, "")])
    result = tools.lookup_hosted("Sample Grocer", ["chocolate_visa"], amount_sgd=30,
                                 chocolate_eligible=eligibility)
    if guaranteed is None:
        assert result["recommendations"] == []
    else:
        assert result["recommendations"][0]["earn_rate_mpd"] == guaranteed
    assert result["conditional_recommendations"][0]["earn_rate_mpd"] == conditional


@pytest.mark.parametrize("as_of,expected", [
    (date(2026, 9, 23), "card is linked and verified on HeyMax"),
    (date(2026, 10, 1), "S$5,000 prior-month average daily SGD balance"),
])
def test_chocolate_balance_requirement_starts_in_october(ocbc_rewards, as_of, expected):
    card = replace(ocbc_rewards, card_id="chocolate_visa", eligible_mccs=[],
                   eligible_merchants=[], earn_rate_mpd=1, base_rate_mpd=.4,
                   cap_sgd=2000, earn_block_sgd=1)
    row = rank_cards("5411", [card], False, 1, amount_sgd=30, as_of=as_of)[0]
    assert any(expected in note for note in row["gotchas"])
    if as_of.month == 9:
        assert not any("S$5,000" in note for note in row["gotchas"])


@pytest.mark.parametrize("value", ["true", 1, {}, []])
def test_account_eligibility_requires_boolean(value):
    with pytest.raises(ValueError, match="chocolate_eligible"):
        tools.lookup_hosted("Sample", [], chocolate_eligible=value)


@pytest.mark.parametrize("channel,matched", [("apple_pay", True), ("contactless", True), ("online", False)])
def test_contactless_merchant_accepts_mobile_wallet(monkeypatch, ocbc_rewards, channel, matched):
    monkeypatch.setattr(tools._loader, "_cards", [ocbc_rewards])
    monkeypatch.setattr(tools._loader, "_merchants", [
        MerchantRecord("Sample Shop", None, "contactless", "5651", "Clothing", "medium", 1, "")])
    result = tools.lookup_hosted("Sample Shop", ["ocbc_rewards"], channel=channel)
    assert result["merchant_matched"] is matched
    if not matched:
        assert result["requires_clarification"] is True


@pytest.mark.parametrize("endpoint", ["lookup", "compare-payment-methods"])
def test_api_eligibility_is_request_scoped(monkeypatch, ocbc_rewards, endpoint):
    from starlette.testclient import TestClient
    from kiasumiles import hosted

    card = replace(ocbc_rewards, card_id="chocolate_visa", card_name="Chocolate Visa",
                   eligible_mccs=[], eligible_merchants=[], earn_rate_mpd=1, cap_sgd=2000)
    monkeypatch.setattr(tools._loader, "_cards", [card])
    monkeypatch.setattr(tools._loader, "_merchants", [
        MerchantRecord("Sample Grocer", None, "any", "5411", "Grocery", "medium", 1, "")])
    client = TestClient(hosted.app)
    body = {"merchant": "Sample Grocer", "cards": ["Chocolate Visa"], "amount_sgd": 30}
    for eligibility, expected in [(True, .4), (False, 0), (None, None)]:
        request_body = dict(body)
        if eligibility is not None:
            request_body["chocolate_eligible"] = eligibility
        response = client.post(f"/api/chatgpt/{endpoint}", json=request_body)
        assert response.status_code == 200
        payload = response.json()
        rows = ([m["best_guaranteed"] for m in payload["methods"]] if endpoint != "lookup"
                else [next(iter(payload["recommendations"]), None)])
        assert all((row["earn_rate_mpd"] if row else None) == expected for row in rows)
    response = client.post(f"/api/chatgpt/{endpoint}", json={**body, "chocolate_eligible": "true"})
    assert response.status_code == 400


@pytest.mark.parametrize("name,expected", [(None, .4), ("", .4), ("Guard", .4),
    ("Guardian", 4), ("Guardian @ East", 4), ("Guardiania", .4)])
def test_named_bonus_requires_whole_merchant_name(ocbc_rewards, name, expected):
    card = replace(ocbc_rewards, card_id="partner_card", eligible_mccs=[])
    assert effective_mpd(card, "5912", False, name, "online") == expected


def test_freshness_does_not_claim_whole_database_verified(monkeypatch, ocbc_rewards):
    monkeypatch.setattr(tools._loader, "_cards", [replace(ocbc_rewards, last_verified="2026-08-29")])
    monkeypatch.setattr(tools._loader, "_merchants", [
        MerchantRecord("Sample", None, "any", "5411", "Grocery", "medium", 1, "2026-01")])
    result = tools.data_version()
    assert result["data_version"] == "2026-08-29"
    assert result["oldest_record_verification"] == "2026-01"
    assert result["verification_scope"] == "individual_records_not_full_database"


@pytest.mark.parametrize("mcc", ["8011", "8099", "9311", "9399", "4900", "4999", "6513", "6531", "6300", "6399", "7311", "7399"])
def test_chocolate_bill_miles_never_exceed_ceiling(ocbc_rewards, mcc):
    card = replace(ocbc_rewards, card_id="chocolate_visa", eligible_mccs=[],
                   eligible_merchants=[], earn_rate_mpd=1, cap_sgd=2000)
    result = rank_cards(mcc, [card], False, 1, amount_sgd=800, chocolate_eligible=True)[0]
    assert result["estimated_miles"] is None
    assert result["rate_status"] == "conditional"
    assert "300 miles" in result["cap_summary"]
    guaranteed = rank_cards(mcc, [card], False, 1, rate_mode="guaranteed",
                             amount_sgd=800, chocolate_eligible=True)[0]
    assert guaranteed["estimated_miles"] == 0


@pytest.mark.parametrize("mcc", ["8010", "8100", "9310", "9400", "4899", "5000", "6512", "6532", "6299", "6400", "7310", "7400", "5411"])
def test_chocolate_bill_ceiling_does_not_apply_to_other_categories(ocbc_rewards, mcc):
    card = replace(ocbc_rewards, card_id="chocolate_visa", eligible_mccs=[],
                   eligible_merchants=[], earn_rate_mpd=1, cap_sgd=2000)
    result = rank_cards(mcc, [card], False, 1, amount_sgd=800, chocolate_eligible=True)[0]
    assert result["estimated_miles"] == 800


@pytest.mark.parametrize("amount", [100, 300, 305])
def test_chocolate_bill_ceiling_amount_boundaries(ocbc_rewards, amount):
    card = replace(ocbc_rewards, card_id="chocolate_visa", eligible_mccs=[],
                   eligible_merchants=[], earn_rate_mpd=1, cap_sgd=2000)
    result = rank_cards("4900", [card], False, 1, amount_sgd=amount, chocolate_eligible=True)[0]
    assert result["estimated_miles"] is None
    assert result["rate_status"] == "conditional"
    assert "300 miles" in result["cap_summary"]


@pytest.mark.parametrize("mcc", "4900 6513 7349 4829 5960 6010 6011 6012 6051 6211 6300 6540 7995 8211 8220 8241 8244 8249 8299 8398 8651 8661 9211 9222 9223 9311 9399 9402 9405 7299 7399 8999".split())
def test_trust_freedom_excluded_categories(ocbc_rewards, mcc):
    card = replace(ocbc_rewards, card_id="trust_freedom", eligible_mccs=[], eligible_merchants=[],
                   earn_rate_mpd=1.3, base_rate_mpd=0, cap_sgd=None, earn_block_sgd=5)
    assert effective_mpd(card, mcc, False, "Sample", "online") == 0


@pytest.mark.parametrize("amount,expected", [(4.99, 0), (5, 6.5), (9.99, 6.5), (30, 39)])
def test_trust_freedom_miles_mode_and_blocks(ocbc_rewards, amount, expected):
    card = replace(ocbc_rewards, card_id="trust_freedom", eligible_mccs=[], eligible_merchants=[],
                   earn_rate_mpd=1.3, base_rate_mpd=0, cap_sgd=None, earn_block_sgd=5)
    row = rank_cards("5411", [card], False, 1, amount_sgd=amount)[0]
    assert row["estimated_miles"] == expected
    assert row["rate_status"] == "conditional"
    assert "Miles mode" in " ".join(row["gotchas"])


@pytest.mark.parametrize("mcc,channel,day,expected", [
    ("5411", "online", date(2026, 9, 23), 1.4),
    ("5411", "fcy", date(2026, 9, 23), 2.3),
    ("8220", "online", date(2026, 9, 23), 0),
    ("8220", "fcy", date(2026, 7, 22), 0),
    ("8220", "fcy", date(2026, 7, 23), 2.3),
    ("4900", "fcy", date(2026, 9, 23), 0),
    ("8062", "online", date(2026, 9, 23), 0),
    ("8011", "online", date(2026, 9, 23), 1.4),
])
def test_hsbc_premier_currency_and_education(ocbc_rewards, mcc, channel, day, expected):
    card = replace(ocbc_rewards, card_id="hsbc_premier_mc", bank="HSBC",
                   eligible_mccs=[], eligible_merchants=[], earn_rate_mpd=1.4,
                   base_rate_mpd=1.4, cap_sgd=None, min_spend=0, earn_block_sgd=1)
    assert effective_mpd(card, mcc, False, "Sample", channel, as_of=day) == expected
    row = rank_cards(mcc, [card], False, 1, channel=channel, as_of=day,
                     rate_mode="guaranteed", amount_sgd=100)[0]
    assert row["earn_rate_mpd"] == expected
    assert row["estimated_miles"] == round(expected * 100, 2)


@pytest.mark.parametrize("channel,amount,expected", [
    ("online", .10, 0), ("online", .20, .33),
    ("online", 4.99, 7), ("fcy", 4.99, 11.33),
])
def test_hsbc_premier_rounds_points_not_spend(ocbc_rewards, channel, amount, expected):
    card = replace(ocbc_rewards, card_id="hsbc_premier_mc", bank="HSBC",
                   eligible_mccs=[], eligible_merchants=[], earn_rate_mpd=1.4,
                   base_rate_mpd=1.4, cap_sgd=None, min_spend=0, earn_block_sgd=1)
    row = rank_cards("5411", [card], False, 1, channel=channel,
                     rate_mode="guaranteed", amount_sgd=amount)[0]
    assert row["estimated_miles"] == expected


@pytest.mark.parametrize("merchant,expected", [
    ("AXS Pay+Earn", 0), ("CardUp", 0), ("iPayMy", 0),
    ("Google Ads", 0), ("Facebook Ads", 0), ("Amazon Web Services", 0),
    ("YouTrip top-up", 0), ("Forex.com", 0), ("SmoovPay", 0),
    ("Amazon", 1.4), ("Google Store", 1.4), ("Maxs Cafe", 1.4),
])
def test_hsbc_premier_named_exclusions(ocbc_rewards, merchant, expected):
    card = replace(ocbc_rewards, card_id="hsbc_premier_mc", bank="HSBC",
                   eligible_mccs=[], eligible_merchants=[], earn_rate_mpd=1.4,
                   base_rate_mpd=1.4, cap_sgd=None, min_spend=0)
    assert effective_mpd(card, "5999", False, merchant, "online") == expected


@pytest.mark.parametrize("card_id", ["amex_krisflyer", "amex_krisflyer_ascend",
    "amex_highflyer", "amex_plat_charge", "amex_plat_credit", "amex_centurion"])
@pytest.mark.parametrize("mcc", ["6300", "8062"])
def test_amex_unconfirmed_insurance_healthcare(ocbc_rewards, card_id, mcc):
    card = replace(ocbc_rewards, card_id=card_id, bank="American Express",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   earn_rate_mpd=1.2, base_rate_mpd=1.2, earn_block_sgd=1)
    potential = {"amex_plat_charge": 18, "amex_plat_credit": 16.36}.get(card_id, 36)
    for mode, expected in [("guaranteed", 0), ("conditional", potential)]:
        row = rank_cards(mcc, [card], False, 1, "Example", "online", mode, 30)[0]
        assert row["estimated_miles"] == expected
        assert row["rate_status"] == mode
        assert "transaction_eligibility_unknown" in row["reason_codes"]


@pytest.mark.parametrize("mcc,channel,amount,expected", [
    ("5411", "online", 100, 100), ("5411", "fcy", 100, 200),
    ("5411", "online", .49, .33), ("5411", "fcy", .49, .67),
    ("5411", "online", .50, .67), ("5411", "fcy", .50, 1.33),
    ("8220", "fcy", 100, 0), ("4900", "online", 100, 0),
])
def test_travelone_rewards(ocbc_rewards, mcc, channel, amount, expected):
    card = replace(ocbc_rewards, card_id="hsbc_travelone", bank="HSBC",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   earn_rate_mpd=1.2, base_rate_mpd=1.2, earn_block_sgd=1)
    row = rank_cards(mcc, [card], False, 1, channel=channel,
                     rate_mode="guaranteed", amount_sgd=amount)[0]
    assert row["estimated_miles"] == expected


@pytest.mark.parametrize("card_id", ["dbs_altitude_visa", "dbs_altitude_amex"])
@pytest.mark.parametrize("channel,expected", [("online", 1.3), ("fcy", 2.2)])
def test_altitude_currency_rate(ocbc_rewards, card_id, channel, expected):
    card = replace(ocbc_rewards, card_id=card_id, bank="DBS", eligible_mccs=[],
                   eligible_merchants=[], earn_rate_mpd=1.3, base_rate_mpd=1.3, cap_sgd=None)
    assert effective_mpd(card, "5411", False, channel=channel) == expected
    row = rank_cards("5411", [card], False, 1, channel=channel, rate_mode="guaranteed")[0]
    assert row["earn_rate_mpd"] == expected
    assert effective_mpd(card, "4900", False, channel=channel) == 0


@pytest.mark.parametrize("channel,amount,expected", [("online", 1.53, 0),
    ("online", 1.54, 2), ("online", 9.99, 12), ("fcy", .90, 0), ("fcy", .91, 2)])
def test_altitude_rounds_points_not_spend(ocbc_rewards, channel, amount, expected):
    card = replace(ocbc_rewards, card_id="dbs_altitude_visa", bank="DBS",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   earn_rate_mpd=1.3, base_rate_mpd=1.3, earn_block_sgd=5)
    assert rank_cards("5411", [card], False, 1, channel=channel,
                      amount_sgd=amount)[0]["estimated_miles"] == expected


@pytest.mark.parametrize("card_id,local,fcy", [("dbs_insignia", 1.6, 2), ("dbs_vantage", 1.5, 2.2)])
def test_dbs_general_cards_currency_and_rounding(ocbc_rewards, card_id, local, fcy):
    card = replace(ocbc_rewards, card_id=card_id, bank="DBS", eligible_mccs=[],
                   eligible_merchants=[], cap_sgd=None, earn_rate_mpd=local,
                   base_rate_mpd=local, earn_block_sgd=5)
    for channel, rate in [("online", local), ("fcy", fcy)]:
        row = rank_cards("5411", [card], False, 1, channel=channel, amount_sgd=100)[0]
        assert row["earn_rate_mpd"] == rate
        assert row["estimated_miles"] == pytest.approx(rate * 100)
    assert rank_cards("5411", [card], False, 1, channel="online", amount_sgd=2)[0]["estimated_miles"] == 2


@pytest.mark.parametrize("card_id", ["dbs_altitude_visa", "dbs_altitude_amex", "dbs_insignia", "dbs_vantage"])
def test_dbs_general_rounding_label(ocbc_rewards, card_id):
    card = replace(ocbc_rewards, card_id=card_id, bank="DBS", eligible_mccs=[],
                   eligible_merchants=[], cap_sgd=None, earn_block_sgd=5)
    row = rank_cards("5411", [card], False, 1, channel="online", amount_sgd=2)[0]
    assert row["cap_summary"] == "No cap · DBS Points rounded down per transaction"


@pytest.mark.parametrize("selected,mode,expected", [(True, "guaranteed", 150),
    (None, "guaranteed", 0), (False, "guaranteed", 0),
    (None, "conditional", 150), (False, "conditional", 150)])
def test_vantage_reward_choice(ocbc_rewards, selected, mode, expected):
    card = replace(ocbc_rewards, card_id="dbs_vantage", bank="DBS", eligible_mccs=[],
                   eligible_merchants=[], cap_sgd=None, min_spend=0,
                   earn_rate_mpd=1.5, base_rate_mpd=1.5, earn_block_sgd=5)
    row = rank_cards("5411", [card], False, 1, channel="online", amount_sgd=100,
                     rate_mode=mode, vantage_miles_selected=selected)[0]
    assert row["estimated_miles"] == expected
    if selected is not True:
        assert "reward_choice_unconfirmed" in row["reason_codes"]
        assert any("cashback" in note for note in row["gotchas"])
    excluded = rank_cards("4900", [card], False, 1, channel="online", amount_sgd=100,
                          vantage_miles_selected=selected)[0]
    assert excluded["estimated_miles"] == 0


@pytest.mark.parametrize("endpoint", ["lookup", "compare-payment-methods"])
def test_vantage_choice_api_is_request_scoped(monkeypatch, ocbc_rewards, endpoint):
    from starlette.testclient import TestClient
    from kiasumiles import hosted

    card = replace(ocbc_rewards, card_id="dbs_vantage", card_name="DBS Vantage", bank="DBS",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None, min_spend=0,
                   earn_rate_mpd=1.5, base_rate_mpd=1.5, earn_block_sgd=5)
    monkeypatch.setattr(tools._loader, "_cards", [card])
    monkeypatch.setattr(tools._loader, "_merchants", [
        MerchantRecord("Sample Grocer", None, "any", "5411", "Grocery", "medium", 1, "")])
    client = TestClient(hosted.app)
    body = {"merchant": "Sample Grocer", "cards": ["DBS Vantage"], "amount_sgd": 100}
    for selected, expected in [(True, 150), (False, 0), (None, 0)]:
        response = client.post(f"/api/chatgpt/{endpoint}", json={**body, "vantage_miles_selected": selected})
        assert response.status_code == 200
        payload = response.json()
        rows = ([m["best_guaranteed"] for m in payload["methods"]] if endpoint != "lookup"
                else payload["recommendations"])
        assert rows and all(row["estimated_miles"] == expected for row in rows)
    response = client.post(f"/api/chatgpt/{endpoint}", json={**body, "vantage_miles_selected": "true"})
    assert response.status_code == 400


@pytest.mark.parametrize("mcc", "4829 4900 5199 5960 6010 6011 6012 6050 6051 6211 6300 6381 6399 6513 6529 6530 6534 6540 7511 7995 7349 7523 8211 8220 8241 8244 8249 8299 8062 8398 8651 8661 8699 8999 9211 9222 9223 9311 9399 9402 9405 5965 5993".split())
def test_boc_excluded_categories(ocbc_rewards, mcc):
    card = replace(ocbc_rewards, card_id="boc_elite", bank="BOC", eligible_mccs=[],
                   eligible_merchants=[], cap_sgd=None, earn_rate_mpd=1.4, base_rate_mpd=1.4)
    assert effective_mpd(card, mcc, False, "Example", "online") == 0
    assert effective_mpd(card, "5411", False, "Example", "online") == 1.4


@pytest.mark.parametrize("name,expected", [("AXS Pay+Earn", 0), ("CardUp", 0),
    ("ipaymy", 0), ("EZ-Link", 0), ("NETS FlashPay", 0), ("SAM payments", 0),
    ("YouTrip", 0), ("Grab wallet top-up", 0), ("ShopeePay wallet top up", 0),
    ("Helpling", 0), ("Sendhelper", 0), ("Revolut", 0), ("Wise", 0),
    ("AxiTrader", 0), ("SP Services", 0), ("Farrer Park Hospital", 0),
    ("NUS", 0), ("IRAS", 0), ("Manulife", 0), ("ERA Singapore", 0),
    ("Wise Owl Cafe", 1.4), ("NUS Bookshop", 1.4), ("Mom's Kitchen", 1.4),
    ("Grab", 1.4), ("Shopee", 1.4), ("Sam's Cafe", 1.4), ("Maxs Restaurant", 1.4)])
def test_boc_payment_service_exclusions(ocbc_rewards, name, expected):
    card = replace(ocbc_rewards, card_id="boc_elite", bank="BOC", eligible_mccs=[],
                   eligible_merchants=[], cap_sgd=None, earn_rate_mpd=1.4, base_rate_mpd=1.4)
    assert effective_mpd(card, "5411", False, name, "online") == expected


@pytest.mark.parametrize("amount,expected", [(4.99,16), (5,20), (9,34), (9.99,36)])
def test_wwmc_online_full_amount_rounding(ocbc_rewards, amount, expected):
    card = replace(ocbc_rewards, card_id="dbs_wwmc", bank="DBS", eligible_mccs=[],
                   eligible_merchants=[], eligible_channels=["online"], cap_sgd=1000,
                   earn_rate_mpd=4, base_rate_mpd=.4, earn_block_sgd=5)
    row = rank_cards("5411", [card], False, 1, channel="online", amount_sgd=amount)[0]
    assert row["estimated_miles"] == expected
    assert "calendar month" in row["cap_summary"]


@pytest.mark.parametrize("mcc", "0763 7261 7276 7311 7322 7339 7372 7375 7393 7399 8111 8911 8931".split())
def test_wwmc_online_only_exclusions_keep_base(ocbc_rewards, mcc):
    card = replace(ocbc_rewards, card_id="dbs_wwmc", bank="DBS", eligible_mccs=[],
                   eligible_merchants=[], eligible_channels=["online"], cap_sgd=1000,
                   earn_rate_mpd=4, base_rate_mpd=.4, earn_block_sgd=5)
    assert effective_mpd(card, mcc, False, "Example", "online") == .4
    assert effective_mpd(card, "4900", False, "Example", "online") == 0


@pytest.mark.parametrize("amount,miles", [(2.49,0), (2.5,2), (4.99,2), (5,6), (100,120)])
def test_wwmc_foreign_currency_base(ocbc_rewards, amount, miles):
    card = replace(ocbc_rewards, card_id="dbs_wwmc", bank="DBS", eligible_mccs=[],
                   eligible_merchants=[], eligible_channels=["online"], cap_sgd=1000,
                   earn_rate_mpd=4, base_rate_mpd=.4, earn_block_sgd=5)
    row = rank_cards("5411", [card], False, 1, channel="fcy", amount_sgd=amount,
                     rate_mode="guaranteed")[0]
    assert row["estimated_miles"] == miles
    assert row["earn_rate_mpd"] == 1.2


@pytest.mark.parametrize("name,rate", [("FavePay", .4), ("CardUp", .4), ("IPAYMY", .4),
    ("PAYPAL BIZCONSULTA", .4), ("FAVE ECARD", .4), ("AXS", 0),
    ("Fave Restaurant", 4), ("PAYPAL SHOP", 4)])
def test_wwmc_named_online_bonus_exclusions(ocbc_rewards, name, rate):
    card = replace(ocbc_rewards, card_id="dbs_wwmc", bank="DBS", eligible_mccs=[],
                   eligible_merchants=[], eligible_channels=["online"], cap_sgd=1000,
                   earn_rate_mpd=4, base_rate_mpd=.4, earn_block_sgd=5)
    assert effective_mpd(card, "5411", False, name, "online") == rate


@pytest.mark.parametrize("card_id", ["ocbc_90n_mc", "ocbc_90n_visa"])
@pytest.mark.parametrize("channel,mcc,name,amount,miles", [
    ("online", "5411", "Grocer", 4.99, 0),
    ("online", "5411", "Grocer", 5, 6.5),
    ("fcy", "5411", "Grocer", 9.99, 10.5),
    ("fcy", "5411", "Grocer", 100, 210),
    ("online", "4900", "Utilities", 100, 0),
    ("online", "5411", "AXS", 100, 0),
    ("online", "5411", "AXS Pay+Earn", 100, 100),
    ("online", "5411", "YouTrip", 100, 0),
    ("online", "4111", "Public transit", 100, 0),
    ("online", "4121", "Gojek", 100, 130),
])
def test_ocbc_90n_base_rewards(ocbc_rewards, card_id, channel, mcc, name, amount, miles):
    card = replace(ocbc_rewards, card_id=card_id, eligible_mccs=[],
                   eligible_merchants=[], eligible_channels=[], cap_sgd=None,
                   earn_rate_mpd=1.3, base_rate_mpd=1.3, earn_block_sgd=5)
    row = rank_cards(mcc, [card], False, 1, merchant_name=name, channel=channel,
                     amount_sgd=amount, rate_mode="guaranteed")[0]
    assert row["estimated_miles"] == miles


@pytest.mark.parametrize("name", ["Independent Taxi", "Comfort Bus Charter"])
def test_ocbc_90n_unconfirmed_transport_is_not_definitively_excluded(ocbc_rewards, name):
    card = replace(ocbc_rewards, card_id="ocbc_90n_mc", eligible_mccs=[],
                   eligible_merchants=[], cap_sgd=None, earn_rate_mpd=1.3, base_rate_mpd=1.3)
    row = rank_cards("4121", [card], False, 1, merchant_name=name,
                     amount_sgd=100, rate_mode="conditional")[0]
    assert row["estimated_miles"] == 130
    assert "transaction_eligibility_unknown" in row["reason_codes"]
    guaranteed = rank_cards("4121", [card], False, 1, merchant_name=name,
                            amount_sgd=100, rate_mode="guaranteed")[0]
    assert guaranteed["estimated_miles"] == 0


@pytest.mark.parametrize("card_id,local,foreign", [("ocbc_voyage", 1.3, 2.2),
                                                  ("ocbc_voyage_premier", 1.6, 2.3)])
def test_voyage_rates_and_exceptions(ocbc_rewards, card_id, local, foreign):
    card = replace(ocbc_rewards, card_id=card_id, eligible_mccs=[],
                   eligible_merchants=[], cap_sgd=None, earn_rate_mpd=local, base_rate_mpd=local)
    for mcc, name, channel, expected in [
        ("5411", "Grocer", "fcy", foreign * 10),
        ("5411", "Grocer", "online", local * 10),
        ("5411", "AXS Pay+Earn", "online", 10),
        ("4900", "Utilities", "online", 0),
        ("8062", "Public Hospital", "online", 0),
        ("8062", "RAFFLES HOSPITAL", "online", local * 10),
        ("8099", "Singhealth", "online", 0),
        ("7311", "Google Ads", "online", 0),
    ]:
        row = rank_cards(mcc, [card], False, 1, merchant_name=name, channel=channel,
                         amount_sgd=10, rate_mode="guaranteed")[0]
        assert row["estimated_miles"] == expected


@pytest.mark.parametrize("card_id,rate", [("ocbc_voyage", 1.3), ("ocbc_voyage_premier", 1.6)])
@pytest.mark.parametrize("mcc", ["4814", "4816"])
def test_voyage_telecom_requires_recurring_payment_confirmation(ocbc_rewards, card_id, rate, mcc):
    card = replace(ocbc_rewards, card_id=card_id, eligible_mccs=[],
                   eligible_merchants=[], cap_sgd=None, earn_rate_mpd=1.3, base_rate_mpd=1.3)
    for recurring in (None, True, False):
        for mode in ("guaranteed", "conditional"):
            row = rank_cards(mcc, [card], False, 1, merchant_name="Telecom provider",
                             amount_sgd=10, rate_mode=mode, is_recurring=recurring)[0]
            expected = 0 if recurring is True or (recurring is None and mode == "guaranteed") else 10 * rate
            assert row["estimated_miles"] == expected
            assert ("transaction_eligibility_unknown" in row["reason_codes"]) == (recurring is None)


@pytest.mark.parametrize("card_id,local,foreign", [("ocbc_voyage", 13, 22), ("ocbc_voyage_premier", 16, 23)])
def test_voyage_explicit_currency_overrides_channel(ocbc_rewards, card_id, local, foreign):
    card = replace(ocbc_rewards, card_id=card_id, eligible_mccs=[], eligible_merchants=[], cap_sgd=None)
    for currency, channel, expected in [("SGD", "fcy", local), ("USD", "online", foreign)]:
        row = rank_cards("5411", [card], False, 1, "Grocer", channel, "guaranteed", 10,
                         transaction_currency=currency)[0]
        assert row["estimated_miles"] == expected


@pytest.mark.parametrize("card_id,currency,expected", [
    ("ocbc_voyage", "SGD", [0, 6, 6, 13, 19]),
    ("ocbc_voyage", "USD", [0, 11, 11, 22, 33]),
    ("ocbc_voyage_premier", "SGD", [0, 8, 8, 16, 24]),
    ("ocbc_voyage_premier", "USD", [0, 11, 11, 23, 34]),
])
def test_voyage_whole_miles_per_purchase(ocbc_rewards, card_id, currency, expected):
    card = replace(ocbc_rewards, card_id=card_id, eligible_mccs=[],
                   eligible_merchants=[], cap_sgd=None, earn_block_sgd=5)
    for amount, miles in zip([4.99, 5, 9.99, 10, 15], expected):
        for mode in ("guaranteed", "conditional"):
            row = rank_cards("5411", [card], False, 1, "Grocer", "online", mode,
                             amount, transaction_currency=currency)[0]
            assert row["estimated_miles"] == miles


@pytest.mark.parametrize("card_id", ["uob_prvi_miles_visa", "uob_prvi_miles_amex"])
def test_prvi_exclusions_and_fuel_network_exception(ocbc_rewards, card_id):
    card = replace(ocbc_rewards, card_id=card_id, bank="UOB", eligible_mccs=[],
                   eligible_merchants=[], cap_sgd=None, earn_rate_mpd=1.4, base_rate_mpd=1.4)
    for mcc in "4829 4900 5199 5960 5965 5993 6012 6050 6051 6211 6300 6513 6529 6530 6534 6540 7349 7511 7523 7995 8062 8211 8220 8241 8244 8249 8299 8398 8661 8651 8699 8999 9211 9222 9223 9311 9402 9405 9399".split():
        assert effective_mpd(card, mcc, False, "Example", "online") == 0
    for name in ["AMAZE12345", "AXS Pay+Earn", "IPAYMY payments", "NORWDS123"]:
        assert effective_mpd(card, "5411", False, name, "online") == 0
    assert effective_mpd(card, "5541", False, "Shell", "contactless") == 0
    assert effective_mpd(card, "5541", False, "SPC", "contactless") == (1.4 if card_id.endswith("amex") else 0)
    assert effective_mpd(card, "5812", False, "Shellfish Restaurant", "online") == 1.4


@pytest.mark.parametrize("amount,miles", [(4.99, 0), (5, 6), (9.99, 6), (10, 14), (15, 20)])
@pytest.mark.parametrize("card_id", ["uob_prvi_miles_visa", "uob_prvi_miles_amex"])
def test_prvi_whole_points_rounding(ocbc_rewards, card_id, amount, miles):
    card = replace(ocbc_rewards, card_id=card_id, bank="UOB", eligible_mccs=[],
                   eligible_merchants=[], cap_sgd=None, earn_rate_mpd=1.4, base_rate_mpd=1.4)
    row = rank_cards("5411", [card], False, 1, amount_sgd=amount)[0]
    assert row["estimated_miles"] == miles


@pytest.mark.parametrize("card_id", ["uob_prvi_miles_visa", "uob_prvi_miles_amex"])
def test_prvi_simplygo_fare_needs_monthly_total(ocbc_rewards, card_id):
    card = replace(ocbc_rewards, card_id=card_id, bank="UOB",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   earn_rate_mpd=1.4, base_rate_mpd=1.4)
    row = rank_cards("4111", [card], False, 1, "SimplyGo", "contactless",
                     amount_sgd=3)[0]
    assert row["earn_rate_mpd"] == 1.4
    assert row["estimated_miles"] is None
    assert "accumulated monthly" in row["condition_summary"]


@pytest.mark.parametrize("merchant,fragment,expiry", [
    ("Expedia", "expedia.com.sg/prvimiles", date(2027, 3, 31)),
    ("Agoda", "agoda.com/prvimiles", date(2027, 8, 15)),
])
def test_prvi_partner_bonus_requires_booking_details(ocbc_rewards, merchant, fragment, expiry):
    card = replace(ocbc_rewards, card_id="uob_prvi_miles_visa", bank="UOB",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   earn_rate_mpd=1.4, base_rate_mpd=1.4)
    row = rank_cards("4722", [card], False, 1, merchant, "online", amount_sgd=100,
                     as_of=expiry)[0]
    assert row["earn_rate_mpd"] == 1.4
    assert any(fragment in note and "not included" in note for note in row["gotchas"])
    expired = rank_cards("4722", [card], False, 1, merchant, "online",
                         amount_sgd=100, as_of=expiry + timedelta(days=1))[0]
    assert not any(fragment in note for note in expired["gotchas"])


@pytest.mark.parametrize("currency,country,mode,miles", [
    ("MYR", "MY", "guaranteed", 30), ("MYR", "SG", "guaranteed", 14),
    ("MYR", "US", "guaranteed", 24), ("USD", "US", "guaranteed", 24),
    ("SGD", "US", "guaranteed", 14), (None, None, "guaranteed", 14),
    (None, None, "conditional", 30),
    ("USD", None, "conditional", 24),
    ("MYR", None, "conditional", 30),
    (None, "US", "conditional", 24),
])
def test_prvi_currency_and_gateway(ocbc_rewards, currency, country, mode, miles):
    card = replace(ocbc_rewards, card_id="uob_prvi_miles_visa", bank="UOB",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   earn_rate_mpd=1.4, base_rate_mpd=1.4)
    row = rank_cards("5411", [card], False, 1, channel="fcy", amount_sgd=10,
                     rate_mode=mode, transaction_currency=currency,
                     payment_gateway_country=country)[0]
    assert row["estimated_miles"] == miles


@pytest.mark.parametrize("endpoint", ["lookup", "compare-payment-methods"])
@pytest.mark.parametrize("card_id,expected", [("uob_prvi_miles_visa", 30), ("boc_elite", 28)])
def test_payment_details_api(monkeypatch, ocbc_rewards, endpoint, card_id, expected):
    from starlette.testclient import TestClient
    from kiasumiles import hosted
    card = replace(ocbc_rewards, card_id=card_id, card_name=card_id,
                   bank="UOB", eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   earn_rate_mpd=1.4, base_rate_mpd=1.4)
    monkeypatch.setattr(tools._loader, "_cards", [card])
    monkeypatch.setattr(tools._loader, "_merchants", [
        MerchantRecord("Sample Grocer", None, "any", "5411", "Grocery", "medium", 1, "")])
    client = TestClient(hosted.app)
    body = {"merchant": "Sample Grocer", "cards": [card.card_id], "amount_sgd": 10,
            "transaction_currency": "MYR", "payment_gateway_country": "MY"}
    response = client.post(f"/api/chatgpt/{endpoint}", json=body)
    assert response.status_code == 200
    payload = response.json()
    rows = ([m["best_guaranteed"] for m in payload["methods"]] if endpoint != "lookup"
            else payload["recommendations"])
    assert rows and all(row["estimated_miles"] == expected for row in rows)
    response = client.post(f"/api/chatgpt/{endpoint}", json={**body, "transaction_currency": 123})
    assert response.status_code == 400


@pytest.mark.parametrize("currency,country,mode,miles", [
    ("USD", "US", "guaranteed", 25.2), ("USD", "SG", "guaranteed", 12.6),
    ("SGD", "US", "guaranteed", 12.6), (None, None, "guaranteed", 12.6),
    (None, None, "conditional", 25.2),
])
def test_boc_gateway_and_dollar_rounding(ocbc_rewards, currency, country, mode, miles):
    card = replace(ocbc_rewards, card_id="boc_elite", bank="BOC", eligible_mccs=[],
                   eligible_merchants=[], cap_sgd=None, earn_rate_mpd=1.4,
                   base_rate_mpd=1.4, earn_block_sgd=1)
    row = rank_cards("5411", [card], False, 1, channel="fcy", amount_sgd=9.99,
                     rate_mode=mode, transaction_currency=currency,
                     payment_gateway_country=country)[0]
    assert row["estimated_miles"] == miles
    assert rank_cards("4900", [card], False, 1, channel="fcy", amount_sgd=9.99,
                      transaction_currency=currency, payment_gateway_country=country)[0]["estimated_miles"] == 0


@pytest.mark.parametrize("card_id,expected", [
    ("amex_plat_charge", [0, 1, 1, 2, 6]),
    ("amex_plat_credit", [0, .91, .91, 1.82, 5.45]),
])
def test_platinum_complete_reward_blocks(ocbc_rewards, card_id, expected):
    card = replace(ocbc_rewards, card_id=card_id, bank="Amex", eligible_mccs=[],
                   eligible_merchants=[], cap_sgd=None, earn_block_sgd=1,
                   earn_rate_mpd=.63, base_rate_mpd=.63)
    for amount, miles in zip([1.59, 1.6, 3.19, 3.2, 9.99], expected):
        row = rank_cards("5411", [card], False, 1, "Grocer", "online", "guaranteed", amount)[0]
        assert row["estimated_miles"] == miles
        assert row["earn_block_sgd"] == 1.6
    assert rank_cards("4900", [card], False, 1, amount_sgd=10)[0]["estimated_miles"] == 0


@pytest.mark.parametrize("card_id,mcc,currency,channel,miles", [
    ("hsbc_travelone", "5411", "USD", "online", 20),
    ("hsbc_travelone", "5411", "SGD", "fcy", 10),
    ("hsbc_premier_mc", "5411", "USD", "online", 23),
    ("hsbc_premier_mc", "5411", "SGD", "fcy", 14),
    ("hsbc_premier_mc", "8220", "USD", "online", 23),
    ("hsbc_premier_mc", "8220", "SGD", "fcy", 0),
    ("hsbc_travelone", "8220", "USD", "online", 0),
])
def test_hsbc_explicit_currency_overrides_legacy_channel(ocbc_rewards, card_id, mcc, currency, channel, miles):
    card = replace(ocbc_rewards, card_id=card_id, bank="HSBC", eligible_mccs=[],
                   eligible_merchants=[], cap_sgd=None, earn_block_sgd=1)
    row = rank_cards(mcc, [card], False, 1, "Example", channel, "guaranteed", 10,
                     transaction_currency=currency, as_of=date(2026, 9, 23))[0]
    assert row["estimated_miles"] == miles


@pytest.mark.parametrize("card_id,local,foreign", [
    ("dbs_altitude_visa", 12, 22), ("dbs_altitude_amex", 12, 22),
    ("dbs_insignia", 16, 20), ("dbs_vantage", 14, 22),
])
def test_dbs_explicit_currency_overrides_channel(ocbc_rewards, card_id, local, foreign):
    card = replace(ocbc_rewards, card_id=card_id, bank="DBS", eligible_mccs=[],
                   eligible_merchants=[], cap_sgd=None, earn_block_sgd=1)
    for currency, channel, expected in [("USD", "online", foreign), ("SGD", "fcy", local)]:
        row = rank_cards("5411", [card], False, 1, "Example", channel, "guaranteed", 10,
                         transaction_currency=currency, vantage_miles_selected=True)[0]
        assert row["estimated_miles"] == expected


def test_chromo_explicit_foreign_currency_excluded(ocbc_rewards):
    card = replace(ocbc_rewards, card_id="dbs_chromo", bank="DBS", eligible_mccs=[],
                   eligible_merchants=[], cap_sgd=None, earn_rate_mpd=.4, base_rate_mpd=.4)
    row = rank_cards("5411", [card], False, 1, "Example", "online", "conditional", 10,
                     transaction_currency="USD")[0]
    assert row["estimated_miles"] == 0
    assert "transaction_excluded" in row["reason_codes"]


@pytest.mark.parametrize("card_id", ["ocbc_90n_mc", "ocbc_90n_visa"])
def test_90n_explicit_currency_overrides_channel(ocbc_rewards, card_id):
    card = replace(ocbc_rewards, card_id=card_id, eligible_mccs=[],
                   eligible_merchants=[], cap_sgd=None, earn_block_sgd=5)
    for currency, channel, miles in [("USD", "online", 21), ("SGD", "fcy", 13)]:
        row = rank_cards("5411", [card], False, 1, "Example", channel, "guaranteed", 10,
                         transaction_currency=currency)[0]
        assert row["estimated_miles"] == miles


def test_horizon_explicit_currency_overrides_channel(ocbc_rewards):
    card = replace(ocbc_rewards, card_id="maybank_horizon", bank="Maybank",
                   eligible_mccs=["4511"], eligible_merchants=[], cap_sgd=10000,
                   earn_rate_mpd=2.8, base_rate_mpd=1.2, min_spend=800, earn_block_sgd=5)
    for currency, channel, expected in [("USD", "online", 28), ("SGD", "fcy", 12)]:
        row = rank_cards("5999", [card], False, 1, "Example", channel, "conditional", 10,
                         transaction_currency=currency)[0]
        assert row["estimated_miles"] == expected


@pytest.mark.parametrize("currency,channel,amount,expected", [
    ("SGD", "fcy", 10, 12), ("USD", "online", 10, 22),
    ("SGD", "online", 1.25, 1), ("USD", "online", 1.25, 2),
    ("SGD", "online", 9.99, 11), ("USD", "online", 9.99, None),
    ("SGD", "online", 3, None)])
def test_premiermiles_currency_and_whole_miles(ocbc_rewards, currency, channel, amount, expected):
    card = replace(ocbc_rewards, card_id="citi_premiermiles", bank="Citi",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   earn_rate_mpd=1.2, base_rate_mpd=1.2, earn_block_sgd=1)
    row = rank_cards("5411", [card], False, 1, "Example", channel, "guaranteed", amount,
                     transaction_currency=currency)[0]
    assert row["estimated_miles"] == expected
    if expected is None:
        assert "rounding_unconfirmed" in row["reason_codes"]


@pytest.mark.parametrize("card_id", ["citi_premiermiles", "citi_prestige", "citi_ultima"])
def test_citi_general_cards_shared_exclusions(ocbc_rewards, card_id):
    card = replace(ocbc_rewards, card_id=card_id, eligible_mccs=[], eligible_merchants=[])
    for mcc, merchant in [("4900", "Utility"), ("8220", "School"),
                          ("5411", "AMAZE* AXS"), ("5411", "SimplyGo"),
                          ("5411", "AMAZE*BUS"), ("5411", "COMPANY*MRT")]:
        assert effective_mpd(card, mcc, False, merchant, "online") == 0
    assert effective_mpd(card, "5812", False, "Bus Stop Cafe", "online") > 0
    hospital = effective_mpd(card, "8062", False, "Hospital", "online")
    assert (hospital > 0) if card_id == "citi_ultima" else (hospital == 0)


def test_premiermiles_exclusion_overrides_foreign_rate(ocbc_rewards):
    card = replace(ocbc_rewards, card_id="citi_premiermiles", eligible_mccs=[], eligible_merchants=[])
    assert effective_mpd(card, "5411", False, "Grocer", "fcy") == 2.2
    for mcc, merchant in [("8062", "Hospital"), ("5411", "AMAZE*BUS")]:
        row = rank_cards(mcc, [card], False, 1, merchant, "online", "guaranteed", 10,
                         transaction_currency="USD")[0]
        assert row["estimated_miles"] == 0
        assert "transaction_excluded" in row["reason_codes"]


@pytest.mark.parametrize("eligible,mode,amount,expected", [
    (None, "conditional", 10, 40), (False, "conditional", 10, 40),
    (True, "conditional", 10, 80), (True, "guaranteed", 10, 4),
    (True, "conditional", 1201, 9600.4)])
def test_revolution_deposit_tier(ocbc_rewards, eligible, mode, amount, expected):
    card = replace(ocbc_rewards, card_id="hsbc_revolution", eligible_mccs=["5812"],
                   eligible_merchants=[], earn_rate_mpd=4, base_rate_mpd=.4,
                   cap_sgd=1000, cap_period="calendar_month", earn_block_sgd=1)
    row = rank_cards("5812", [card], False, 1, "Restaurant", "online", mode, amount,
                     revolution_ega_eligible=eligible)[0]
    assert row["estimated_miles"] == pytest.approx(expected)
    assert row["cap_sgd"] == (1200 if eligible else 1000)
    excluded = rank_cards("8062", [card], False, 1, "Hospital", "online", mode, amount,
                          revolution_ega_eligible=eligible)[0]
    assert excluded["estimated_miles"] == 0


def test_revolution_deposit_tier_rejects_non_boolean(ocbc_rewards):
    with pytest.raises(ValueError, match="revolution_ega_eligible"):
        rank_cards("5812", [ocbc_rewards], False, 1, revolution_ega_eligible="true")


@pytest.mark.parametrize("enhanced,prior,amount,expected", [
    (False, .6, .6, 4), (True, .6, .6, 8),
    (False, 999.5, 1, 4), (False, 999, 2, 4.4),
    (True, 1199, 2, 8.4), (True, 1200, 10, 4),
    (False, 1000, 10, 4), (False, 0, .99, 0)])
def test_revolution_monthly_increment(ocbc_rewards, enhanced, prior, amount, expected):
    card = replace(ocbc_rewards, card_id="hsbc_revolution", eligible_mccs=["5812"],
                   eligible_merchants=[], earn_rate_mpd=4, base_rate_mpd=.4,
                   cap_sgd=1000, cap_period="calendar_month", earn_block_sgd=1)
    for mode in ("guaranteed", "conditional"):
        row = rank_cards("5812", [card], False, 1, "Restaurant", "online", mode, amount,
                         revolution_ega_eligible=enhanced,
                         revolution_prior_eligible_spend_sgd=prior)[0]
        assert row["estimated_miles"] == pytest.approx(expected)
        assert row["rate_status"] == "guaranteed"


@pytest.mark.parametrize("prior", [-1, True, "10", float("nan"), float("inf")])
def test_revolution_prior_spend_validation(ocbc_rewards, prior):
    with pytest.raises(ValueError, match="revolution_prior_eligible_spend_sgd"):
        rank_cards("5812", [ocbc_rewards], False, 1, revolution_prior_eligible_spend_sgd=prior)


def test_revolution_issuer_exclusions(ocbc_rewards):
    card = replace(ocbc_rewards, card_id="hsbc_revolution", eligible_mccs=["5812"], eligible_merchants=[])
    for mcc, merchant in [("8062", "Hospital"), ("8220", "School"),
                          ("5812", "CardUp"), ("5812", "Google Ads")]:
        assert effective_mpd(card, mcc, False, merchant, "online") == 0
    assert effective_mpd(card, "5812", False, "Restaurant", "online") == 4


@pytest.mark.parametrize("mcc,merchant", [
    ("6535", "Example"), ("5812", "EZ-LINK*123"), ("5812", "IPAYMY*123"),
    ("5812", "SIMPLYGO*123"), ("5812", "skrill.com*123"), ("5812", "TRANSIT*123")])
def test_imperium_published_exclusion_updates(ocbc_rewards, mcc, merchant):
    card = replace(ocbc_rewards, card_id="dcs_imperium", eligible_mccs=[], eligible_merchants=[],
                   earn_rate_mpd=1.6, base_rate_mpd=1.6, cap_sgd=None)
    row = rank_cards(mcc, [card], False, 1, merchant, "online", "guaranteed", 10)[0]
    assert row["estimated_miles"] == 0
    assert "transaction_excluded" in row["reason_codes"]


@pytest.mark.parametrize("mcc", "4784 4829 4900 5199 5960 6010 6011 6012 6050 6051 6211 6300 6513 6540 7349 7523 7800 7801 7802 7995 8062 8211 8220 8241 8244 8249 8299 8398 8651 8661 9211 9222 9223 9311 9399 9402 9405 9406".split())
def test_imperium_agreement_excluded_categories(ocbc_rewards, mcc):
    card = replace(ocbc_rewards, card_id="dcs_imperium", eligible_mccs=[], eligible_merchants=[])
    assert effective_mpd(card, mcc, False, "Example", "online") == 0


@pytest.mark.parametrize("currency,amount,expected", [("SGD", .99, 1.2), ("USD", .99, 2),
                                                       ("SGD", 1.25, 2), ("USD", 1.25, 2.8)])
def test_imperium_currency_and_point_rounding(ocbc_rewards, currency, amount, expected):
    card = replace(ocbc_rewards, card_id="dcs_imperium", eligible_mccs=[], eligible_merchants=[],
                   earn_rate_mpd=1.6, base_rate_mpd=1.6, cap_sgd=None)
    row = rank_cards("5812", [card], False, 1, "Restaurant", "online", "guaranteed", amount,
                     transaction_currency=currency)[0]
    assert row["estimated_miles"] == expected


@pytest.mark.parametrize("merchant", ["AXS", "LTA", "Singapore Post", "SingPost",
                                       "AMAZE*Restaurant", "Road Tax", "Esso Fleet"])
def test_imperium_named_exclusions_override_foreign_rate(ocbc_rewards, merchant):
    card = replace(ocbc_rewards, card_id="dcs_imperium", eligible_mccs=[], eligible_merchants=[])
    row = rank_cards("5812", [card], False, 1, merchant, "online", "guaranteed", 10,
                     transaction_currency="USD")[0]
    assert row["estimated_miles"] == 0


def test_imperium_ordinary_purchase_and_currency_override(ocbc_rewards):
    card = replace(ocbc_rewards, card_id="dcs_imperium", eligible_mccs=[], eligible_merchants=[])
    for currency, channel, expected in [("SGD", "fcy", 16), ("USD", "online", 24)]:
        row = rank_cards("5541", [card], False, 1, "Esso", channel, "guaranteed", 10,
                         transaction_currency=currency)[0]
        assert row["estimated_miles"] == expected


@pytest.mark.parametrize("currency,channel,rate", [("USD", "online", 2),
    ("SGD", "online", 3), ("SGD", "mobile_contactless", 1.2), ("SGD", "fcy", 1.2)])
def test_journey_bonus_requires_sgd_online(ocbc_rewards, currency, channel, rate):
    card = replace(ocbc_rewards, card_id="stanChart_journey", eligible_mccs=["4121"],
                   eligible_merchants=[], eligible_channels=[], earn_rate_mpd=3, base_rate_mpd=1.2,
                   cap_sgd=1000, cap_period="statement_month", earn_block_sgd=1)
    row = rank_cards("4121", [card], False, 1, "Taxi", channel, "conditional", 10,
                     transaction_currency=currency)[0]
    assert row["earn_rate_mpd"] == rate


@pytest.mark.parametrize("currency,amount,miles", [("SGD", 1, None), ("SGD", 2, 6),
    ("USD", .99, None), ("USD", 1.2, 2.4)])
def test_journey_separate_points_rounding(ocbc_rewards, currency, amount, miles):
    card = replace(ocbc_rewards, card_id="stanChart_journey", eligible_mccs=["5411"],
                   eligible_merchants=[], earn_block_sgd=1)
    row = rank_cards("5411", [card], False, 1, "Grocer", "online", "conditional", amount,
                     transaction_currency=currency)[0]
    assert row["estimated_miles"] == miles
    if miles is None:
        assert "rounding_unconfirmed" in row["reason_codes"]


@pytest.mark.parametrize("amount,miles", [(1000, 3000), (1200, 3240)])
def test_journey_issuer_cap_examples(ocbc_rewards, amount, miles):
    card = replace(ocbc_rewards, card_id="stanChart_journey", eligible_mccs=["5411"],
                   eligible_merchants=[], earn_block_sgd=1)
    row = rank_cards("5411", [card], False, 1, "Grocer", "online", "conditional", amount,
                     transaction_currency="SGD")[0]
    assert row["estimated_miles"] == miles
    assert row["rate_status"] == "conditional"


@pytest.mark.parametrize("mcc", "4829 4900 5047 5199 6012 6050 6051 6540 6211 6513 6529 6530 6534 7299 7349 7511 7523 8062 8211 8220 8241 8244 8249 8299 8398 8651 8661 8999 9211 9222 9223 9311 9399 9402 9405".split())
def test_journey_all_issuer_excluded_categories(ocbc_rewards, mcc):
    card = replace(ocbc_rewards, card_id="stanChart_journey", eligible_mccs=[mcc],
                   eligible_merchants=[])
    row = rank_cards(mcc, [card], False, 1, "Example", "online", "conditional", 10)[0]
    assert row["estimated_miles"] == 0


@pytest.mark.parametrize("merchant,channel,rate", [
    ("Singapore Airlines", "online", 3), ("Scoot", "online", 3),
    ("KrisShop", "online", 3), ("Pelago", "online", 3),
    ("Kris+", "app", 3), ("Kris+", "online", 1.2),
    ("NTUC FairPrice", "online", 1.2)])
def test_krisflyer_uob_current_core_rates(ocbc_rewards, merchant, channel, rate):
    card = replace(ocbc_rewards, card_id="krisflyer_uob", earn_rate_mpd=2.4,
                   base_rate_mpd=1.2, eligible_mccs=["5411"], eligible_merchants=[],
                   min_spend=1000, earn_block_sgd=5)
    row = rank_cards("5411", [card], False, 1, merchant, channel, "guaranteed", 10)[0]
    assert row["earn_rate_mpd"] == rate
    assert row["estimated_miles"] == rate * 10


@pytest.mark.parametrize("mcc,merchant", [("4900", "Utilities"),
    ("5965", "Shop"), ("5993", "Cigar Shop"), ("5411", "AXS"),
    ("5411", "AMAZE*Shop"), ("5411", "IPAYMY123"), ("5541", "SPC")])
def test_krisflyer_uob_published_exclusions(ocbc_rewards, mcc, merchant):
    card = replace(ocbc_rewards, card_id="krisflyer_uob", earn_rate_mpd=2.4,
                   base_rate_mpd=1.2, eligible_mccs=[mcc], eligible_merchants=[],
                   min_spend=1000, earn_block_sgd=5)
    row = rank_cards(mcc, [card], False, 1, merchant, "online", "guaranteed", 10)[0]
    assert row["estimated_miles"] == 0


def test_krisflyer_uob_accelerated_condition_is_specific(ocbc_rewards):
    card = replace(ocbc_rewards, card_id="krisflyer_uob", earn_rate_mpd=2.4,
                   base_rate_mpd=1.2, eligible_mccs=["5812"], eligible_merchants=[],
                   min_spend=1000, cap_sgd=None, earn_block_sgd=5)
    row = rank_cards("5812", [card], False, 1, "Restaurant", "contactless",
                     "conditional", 10)[0]
    assert "Singapore Airlines Group" in row["condition_summary"]
    assert "membership year" in row["condition_summary"]


@pytest.mark.parametrize("mcc,channel,merchant,recurring,expected", [
    ("5941", "mobile_contactless", "Sports Shop", False, 4),
    ("5944", "online", "Jewellery Shop", False, 4),
    ("4121", "online", "Taxi", False, .4),
    ("5944", "online", "Jewellery Shop", True, .4),
    ("5965", "mobile_contactless", "Catalog Shop", False, 0),
    ("5941", "mobile_contactless", "AXS Payment", False, 0),
    ("5941", "contactless", "Sports Shop", False, .4),
])
def test_uob_preferred_visa_channel_and_exclusions(ocbc_rewards, mcc, channel, merchant, recurring, expected):
    card = replace(ocbc_rewards, card_id="uob_ppv", eligible_mccs=["5812", "5814", "5411", "5912", "5311", "5262", "5331", "5944"],
                   eligible_merchants=[], eligible_channels=["mobile_contactless", "online"], earn_rate_mpd=4,
                   base_rate_mpd=.4, cap_sgd=600, earn_block_sgd=5)
    row = rank_cards(mcc, [card], False, 1, merchant, channel, "conditional", 10,
                     is_recurring=recurring)[0]
    assert row["earn_rate_mpd"] == expected


@pytest.mark.parametrize("channel", ["contactless", "mobile_contactless"])
def test_uob_preferred_visa_simplygo_accumulates_monthly(ocbc_rewards, channel):
    card = replace(ocbc_rewards, card_id="uob_ppv", eligible_mccs=["5812"],
                   eligible_merchants=[], eligible_channels=["mobile_contactless", "online"],
                   earn_rate_mpd=4, base_rate_mpd=.4, cap_sgd=600, earn_block_sgd=5)
    row = rank_cards("4111", [card], False, 1, "SimplyGo", channel, "conditional", 2)[0]
    assert row["earn_rate_mpd"] == 4
    assert row["estimated_miles"] is None
    assert "monthly" in row["condition_summary"]


@pytest.mark.parametrize("currency,country,channel,amount,guaranteed,conditional,miles", [
    ("SGD", "US", "fcy", 10, 1.28, 1.28, 12.8),
    ("USD", "US", "online", 9.99, 2.24, 2.24, 11.2),
    ("USD", "SG", "online", 10, 1.28, 1.28, 12.8),
    ("USD", None, "online", 10, 1.28, 2.24, 22.4),
])
def test_ocbc_premier_vi_currency_and_overseas_processing(ocbc_rewards, currency, country, channel,
                                                           amount, guaranteed, conditional, miles):
    card = replace(ocbc_rewards, card_id="ocbc_premier_vi", eligible_mccs=[],
                   eligible_merchants=[], eligible_channels=[], earn_rate_mpd=1.28,
                   base_rate_mpd=1.28, cap_sgd=None, min_spend=0, earn_block_sgd=5)
    results = [rank_cards("5411", [card], False, 1, "NTUC FairPrice", channel, mode, amount,
                          transaction_currency=currency, payment_gateway_country=country)[0]
               for mode in ("guaranteed", "conditional")]
    assert [row["earn_rate_mpd"] for row in results] == [guaranteed, conditional]
    assert results[1]["estimated_miles"] == miles


@pytest.mark.parametrize("mcc,merchant,rate", [
    ("4900", "Utilities", 0),
    ("5411", "AXS", 0),
    ("4111", "Grab Transport", 1.28),
    ("4111", "TransitLink", 0),
    ("8062", "Mount Alvernia Hospital", 1.28),
])
def test_ocbc_premier_vi_representative_exclusions(ocbc_rewards, mcc, merchant, rate):
    card = replace(ocbc_rewards, card_id="ocbc_premier_vi", eligible_mccs=[],
                   eligible_merchants=[], eligible_channels=[], earn_rate_mpd=1.28,
                   base_rate_mpd=1.28, cap_sgd=None, min_spend=0, earn_block_sgd=5)
    row = rank_cards(mcc, [card], False, 1, merchant, "contactless", "conditional", 10)[0]
    assert row["earn_rate_mpd"] == rate


@pytest.mark.parametrize("mcc,name,recurring", [
    ("4900", "Utilities", False), ("6300", "Insurance", False),
    ("5411", "AXS", False), ("4111", "SIMPLYGO", False),
    ("5411", "EZ-LINK", False), ("5411", "Grocer", True)])
@pytest.mark.parametrize("currency", ["SGD", "USD"])
def test_journey_exclusions_override_all_rates(ocbc_rewards, mcc, name, recurring, currency):
    card = replace(ocbc_rewards, card_id="stanChart_journey", eligible_mccs=[mcc],
                   eligible_merchants=[], earn_block_sgd=1)
    row = rank_cards(mcc, [card], False, 1, name, "online", "conditional", 10,
                     transaction_currency=currency, is_recurring=recurring)[0]
    assert row["estimated_miles"] == 0
    assert "transaction_excluded" in row["reason_codes"]


@pytest.mark.parametrize("currency,channel,amount,rate,miles", [
    ("USD", "online", 10, 2, 20), ("SGD", "fcy", 8, 1.3, 10.4),
    ("SGD", "online", 10, 1.3, None)])
def test_prestige_currency_and_daily_rounding(ocbc_rewards, currency, channel, amount, rate, miles):
    card = replace(ocbc_rewards, card_id="citi_prestige", eligible_mccs=[], eligible_merchants=[])
    row = rank_cards("5411", [card], False, 1, "Grocer", channel, "guaranteed", amount,
                     transaction_currency=currency)[0]
    assert row["earn_rate_mpd"] == rate
    assert row["estimated_miles"] == miles
    if miles is None:
        assert "daily_rounding_unconfirmed" in row["reason_codes"]


@pytest.mark.parametrize("mcc", "4829 4900 5199 5960 6010 6011 6012 6050 6051 6211 6300 6513 6529 6530 6532 6533 6534 6536 6537 6538 6540 6555 7299 7399 7349 7511 7523 7801 7995 8062 8211 8220 8241 8244 8249 8299 8398 8651 8661 8999 9211 9222 9223 9311 9399 9402 9405 9754".split())
def test_revolution_all_published_excluded_categories(ocbc_rewards, mcc):
    card = replace(ocbc_rewards, card_id="hsbc_revolution", eligible_mccs=[mcc], eligible_merchants=[])
    row = rank_cards(mcc, [card], False, 1, "Example", "online", "conditional", 10)[0]
    assert row["estimated_miles"] == 0
    assert "transaction_excluded" in row["reason_codes"]


@pytest.mark.parametrize("card_id,foreign_miles,local_miles", [
    ("amex_pps", 20, 14), ("amex_solitaire_pps", 24, 15)])
def test_pps_explicit_currency_overrides_channel(ocbc_rewards, card_id, foreign_miles, local_miles):
    card = replace(ocbc_rewards, card_id=card_id, bank="American Express",
                   eligible_mccs=[], eligible_merchants=[], cap_sgd=None,
                   earn_rate_mpd=1.3, base_rate_mpd=1.3, earn_block_sgd=10)
    for currency, channel, expected in [("USD", "online", foreign_miles), ("SGD", "fcy", local_miles)]:
        row = rank_cards("5411", [card], False, 1, "Example", channel, "guaranteed", 10,
                         pps_prior_spend_sgd={card_id: 3800}, transaction_currency=currency)[0]
        assert row["estimated_miles"] == expected
    with pytest.raises(ValueError):
        rank_cards("4511", [card], False, 1, "Singapore Airlines", "online",
                   pps_sia_group_eligible=True, transaction_currency="USD")
    row = rank_cards("4511", [card], False, 1, "Singapore Airlines", "fcy", "guaranteed", 10,
                     pps_sia_group_eligible=True, transaction_currency="SGD",
                     pps_prior_spend_sgd={card_id: 0})[0]
    assert row["estimated_miles"] == 20
