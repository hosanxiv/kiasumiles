import json
import pytest
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


def test_data_loader_prefers_supabase_when_configured(monkeypatch):
    sample_cards = [
        {
            "card_id": "remote_card",
            "card_name": "Remote Card",
            "bank": "Remote Bank",
            "network": "Visa",
            "eligible_mccs": "5411,5812",
            "earn_rate_mpd": 4.0,
            "base_rate_mpd": 0.4,
            "cap_sgd": "1000",
            "cap_period": "calendar_month",
            "min_spend": "0",
            "requires_amaze": "false",
            "amaze_fee_pct": "0",
            "eligible_merchants": "",
            "eligible_channels": "online",
            "caveat": "Remote rule",
            "last_verified": "2026-06-11",
            "source_url": "",
            "earn_block_sgd": "1",
        }
    ]
    sample_merchants = [
        {
            "merchant_name": "Remote Merchant",
            "outlet": "",
            "channel": "online",
            "mcc": "5411",
            "mcc_category": "Grocery",
            "confidence": "high",
            "data_points": 7,
            "last_verified": "2026-06-11",
        }
    ]

    monkeypatch.setenv("KIASUMILES_SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("KIASUMILES_SUPABASE_SERVICE_ROLE_KEY", "service-role")

    def fake_fetch(self, table_name):
        if table_name == "card_rules":
            return sample_cards
        if table_name == "merchant_mcc":
            return sample_merchants
        raise AssertionError(table_name)

    monkeypatch.setattr(DataLoader, "_fetch_supabase_rows", fake_fetch)

    loader = DataLoader()

    assert loader.backend_name() == "supabase"
    assert loader.cards()[0].card_id == "remote_card"
    assert loader.merchants()[0].merchant_name == "Remote Merchant"


def test_data_loader_falls_back_to_csv_when_supabase_fetch_fails(monkeypatch):
    monkeypatch.setenv("KIASUMILES_SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("KIASUMILES_SUPABASE_SERVICE_ROLE_KEY", "service-role")
    monkeypatch.setattr(
        DataLoader,
        "_fetch_supabase_rows",
        lambda self, table_name: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    loader = DataLoader()

    assert loader.cards()
    assert loader.merchants()


def test_fetch_supabase_rows_paginates(monkeypatch):
    monkeypatch.setenv("KIASUMILES_SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("KIASUMILES_SUPABASE_SERVICE_ROLE_KEY", "service-role")

    requested_ranges = []

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return self._payload.encode("utf-8")

    def fake_urlopen(request, timeout):
        requested_ranges.append(request.full_url)
        if "offset=0" in request.full_url and "limit=1000" in request.full_url:
            return FakeResponse(json.dumps([{"merchant_name": f"merchant-{idx}"} for idx in range(1000)]))
        if "offset=1000" in request.full_url and "limit=1000" in request.full_url:
            return FakeResponse(json.dumps([{"merchant_name": "merchant-1000"}]))
        raise AssertionError(request.full_url)

    monkeypatch.setattr("kiasumiles.data.loader.urlopen", fake_urlopen)

    rows = DataLoader(backend="supabase")._fetch_supabase_rows("merchant_mcc")

    assert len(rows) == 1001
    assert "offset=0" in requested_ranges[0]
    assert "offset=1000" in requested_ranges[1]
