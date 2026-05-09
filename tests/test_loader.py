import pytest
from pathlib import Path
from kiasumiles.data.loader import MerchantRecord, CardRule, DataLoader


def test_merchant_record_fields():
    r = MerchantRecord(
        merchant_name="NTUC FairPrice",
        outlet=None,
        channel="any",
        mcc="5411",
        mcc_category="Grocery",
        confidence="high",
        data_points=26,
        last_verified="2026-03",
    )
    assert r.mcc == "5411"
    assert r.outlet is None


def test_card_rule_eligible_mccs_parsed():
    rule = CardRule(
        card_id="hsbc_revolution",
        card_name="HSBC Revolution",
        bank="HSBC",
        network="Visa",
        eligible_mccs=["5812", "5814", "5411"],
        earn_rate_mpd=4.0,
        base_rate_mpd=0.4,
        cap_sgd=1000.0,
        cap_period="calendar_month",
        min_spend=0.0,
        requires_amaze=False,
        amaze_fee_pct=0.0,
    )
    assert "5812" in rule.eligible_mccs
    assert rule.earn_rate_mpd == 4.0


def test_data_loader_loads_bundled_csvs():
    loader = DataLoader()
    merchants = loader.merchants()
    cards = loader.cards()
    assert len(merchants) > 0
    assert len(cards) > 0


def test_data_loader_merchant_names_are_strings():
    loader = DataLoader()
    for m in loader.merchants():
        assert isinstance(m.merchant_name, str)
        assert len(m.merchant_name) > 0


def test_data_loader_card_ids_are_unique():
    loader = DataLoader()
    ids = [c.card_id for c in loader.cards()]
    assert len(ids) == len(set(ids))
