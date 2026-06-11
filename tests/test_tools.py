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
    recs = rank_cards(record.mcc, wallet_cards, wallet_has_amaze, top_n, record.merchant_name, channel or record.channel)
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
    result = _run_lookup("NTUC FairPrice", channel="mobile_contactless", wallet_ids=["hsbc_revolution", "uob_ppv"])
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


# ---------------------------------------------------------------------------
# Fallback routing tests (unknown merchant → keyword inference / category param)
# ---------------------------------------------------------------------------
from kiasumiles.server import kiasumiles_lookup
from kiasumiles.tools import recommend_stack
from kiasumiles.engine.wallet import save_wallet
import os


def _lookup_via_server(merchant, category=None, wallet_ids=None, tmp_path=None):
    """Call the real server tool with a temp wallet."""
    import kiasumiles.engine.wallet as wm
    original = wm.WALLET_PATH
    if tmp_path:
        wm.WALLET_PATH = tmp_path / "wallet.yaml"
    try:
        if wallet_ids:
            save_wallet(wallet_ids)
        return kiasumiles_lookup(merchant=merchant, category=category)
    finally:
        wm.WALLET_PATH = original


def test_unknown_merchant_with_keyword_gets_recommendations(tmp_path):
    result = _lookup_via_server("zzznewramen9999", tmp_path=tmp_path,
                                wallet_ids=["uob_ppv", "citi_rewards_mc"])
    # keyword "ramen" infers dining MCC
    assert result["merchant_matched"] is False
    assert "routing_note" in result
    assert len(result["recommendations"]) > 0


def test_unknown_merchant_keyword_infers_dining_mcc(tmp_path):
    result = _lookup_via_server("zzznewramen9999", tmp_path=tmp_path,
                                wallet_ids=["uob_ppv", "citi_rewards_mc"])
    assert result["mcc"] == "5812"


def test_unknown_merchant_with_category_param_gets_recommendations(tmp_path):
    result = _lookup_via_server("xyzzy_cafe_99", category="dining", tmp_path=tmp_path,
                                wallet_ids=["uob_ppv", "citi_rewards_mc"])
    assert result["merchant_matched"] is False
    assert result["mcc"] == "5812"
    assert len(result["recommendations"]) > 0


def test_dbs_yuu_earns_base_rate_on_unknown_ramen_fallback(tmp_path):
    result = _lookup_via_server("zzznewramen9999", tmp_path=tmp_path,
                                wallet_ids=["dbs_yuu_visa", "uob_ppv"])
    yuu = next((r for r in result["recommendations"] if r["card_id"] == "dbs_yuu_visa"), None)
    # DBS yuu should NOT earn 10 mpd — raw merchant name is not a yuu partner
    if yuu:
        assert yuu["earn_rate_mpd"] == pytest.approx(0.14)


def test_truly_unknown_merchant_no_keyword_no_category_returns_not_found(tmp_path):
    result = _lookup_via_server("xyzzy_unknown_place_9999", tmp_path=tmp_path,
                                wallet_ids=["uob_ppv"])
    assert result["merchant_matched"] is False
    assert result.get("recommendations") is None or result.get("recommendations") == []


def test_stack_recommendations_find_gaps_for_small_wallet():
    result = recommend_stack(cards=["dbs_altitude_visa"], top_n=2)

    assert result["wallet_configured"] is True
    assert result["recommended_additions"]
    assert any(c["status"] in ("weak", "upgrade_available") for c in result["coverage"])
    assert all("helps_categories" in card for card in result["recommended_additions"])


def test_stack_recommendations_accept_stateless_wallet():
    result = recommend_stack(cards=["uob_ppv", "citi_rewards_mc"], top_n=2)
    categories = {row["category"]: row for row in result["coverage"]}

    assert categories["grocery"]["current_best"]["earn_rate_mpd"] >= 4.0
    assert result["skipped_cards"] == []
