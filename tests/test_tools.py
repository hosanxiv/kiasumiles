import pytest
from pathlib import Path
from kiasumiles.data.loader import DataLoader
from kiasumiles.engine.wallet import save_wallet, load_wallet


def test_list_cards_returns_all_cards():
    loader = DataLoader()
    cards = loader.cards()
    ids = [c.card_id for c in cards]
    assert "hsbc_revolution" in ids
    assert "uob_ppv" in ids
    assert len(cards) >= 10


def test_configure_saves_valid_cards(tmp_path, monkeypatch):
    monkeypatch.setattr("kiasumiles.engine.wallet.WALLET_PATH", tmp_path / "wallet.yaml")
    loader = DataLoader()
    valid_ids = [c.card_id for c in loader.cards()]
    requested = ["hsbc_revolution", "uob_ppv", "not_a_real_card"]
    saved = [cid for cid in requested if cid in valid_ids]
    not_found = [cid for cid in requested if cid not in valid_ids]
    save_wallet(saved)
    assert load_wallet() == saved
    assert "not_a_real_card" in not_found


def test_configure_result_shape(tmp_path, monkeypatch):
    monkeypatch.setattr("kiasumiles.engine.wallet.WALLET_PATH", tmp_path / "wallet.yaml")
    loader = DataLoader()
    valid_ids = {c.card_id for c in loader.cards()}
    requested = ["hsbc_revolution", "fake_card"]
    saved = [c for c in requested if c in valid_ids]
    not_found = [c for c in requested if c not in valid_ids]
    result = {
        "saved": saved,
        "not_found": not_found,
        "wallet_path": str(tmp_path / "wallet.yaml"),
    }
    assert result["saved"] == ["hsbc_revolution"]
    assert result["not_found"] == ["fake_card"]


# ---------------------------------------------------------------------------
# Lookup tool tests
# ---------------------------------------------------------------------------
from kiasumiles.engine.merchant import find_merchant
from kiasumiles.engine.router import rank_cards
from kiasumiles.data.loader import DataLoader as _DL


def _run_lookup(merchant: str, outlet=None, channel=None, wallet_ids=None):
    loader = _DL()
    wallet = wallet_ids or []
    wallet_has_amaze = "amaze" in wallet
    wallet_cards = [c for c in loader.cards() if c.card_id in wallet] if wallet else loader.cards()
    top_n = 3 if wallet else 5
    record, is_exact = find_merchant(merchant, outlet, channel, loader.merchants())
    if record is None:
        return {"merchant_matched": False, "merchant": merchant}
    recs = rank_cards(record.mcc, wallet_cards, wallet_has_amaze, top_n)
    return {
        "merchant": record.merchant_name,
        "mcc": record.mcc,
        "mcc_category": record.mcc_category,
        "confidence": record.confidence,
        "recommendations": recs,
        "wallet_configured": bool(wallet),
        "merchant_matched": is_exact,
    }


def test_lookup_dining_merchant_returns_recommendations():
    result = _run_lookup("NTUC FairPrice", wallet_ids=["hsbc_revolution", "uob_ppv"])
    assert result["mcc"] == "5411"
    assert len(result["recommendations"]) > 0
    assert result["recommendations"][0]["earn_rate_mpd"] >= 4.0


def test_lookup_no_wallet_returns_top5():
    result = _run_lookup("NTUC FairPrice")
    assert len(result["recommendations"]) <= 5


def test_lookup_unknown_merchant_returns_not_matched():
    result = _run_lookup("xyzzy_nonexistent_9999")
    assert result["merchant_matched"] is False


def test_lookup_skips_unknown_wallet_cards():
    result = _run_lookup("NTUC FairPrice", wallet_ids=["hsbc_revolution", "not_a_card"])
    recs_ids = [r["card_id"] for r in result["recommendations"]]
    assert "not_a_card" not in recs_ids


def test_lookup_result_has_required_fields():
    result = _run_lookup("NTUC FairPrice", wallet_ids=["hsbc_revolution"])
    assert "mcc" in result
    assert "mcc_category" in result
    assert "confidence" in result
    assert "recommendations" in result
    assert "wallet_configured" in result
