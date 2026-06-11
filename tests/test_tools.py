import pytest

from kiasumiles.data.loader import DataLoader
from kiasumiles.tools import list_cards, lookup_hosted, recommend_stack


def test_list_cards_returns_all_cards():
    result = list_cards()

    ids = [card["card_id"] for card in result["cards"]]
    assert "hsbc_revolution" in ids
    assert "uob_ppv" in ids
    assert result["total"] >= 10


def test_list_cards_can_filter_by_bank():
    result = list_cards("UOB")

    assert result["filtered_by_bank"] == "UOB"
    assert result["cards"]
    assert all("uob" in card["bank"].lower() for card in result["cards"])


def test_lookup_dining_merchant_returns_recommendations():
    result = lookup_hosted(
        "NTUC FairPrice",
        cards=["hsbc_revolution", "uob_ppv"],
        channel="mobile_contactless",
    )

    assert result["mcc"] == "5411"
    assert len(result["recommendations"]) > 0
    assert result["recommendations"][0]["earn_rate_mpd"] >= 4.0


def test_lookup_unknown_merchant_returns_not_matched():
    result = lookup_hosted("xyzzy_nonexistent_9999", cards=["hsbc_revolution"])

    assert result["merchant_matched"] is False


def test_lookup_skips_unknown_cards():
    result = lookup_hosted("NTUC FairPrice", cards=["hsbc_revolution", "not_a_card"])

    recs_ids = [r["card_id"] for r in result["recommendations"]]
    assert "not_a_card" not in recs_ids
    assert result["skipped_cards"] == ["not_a_card"]


def test_lookup_result_has_required_fields():
    result = lookup_hosted("NTUC FairPrice", cards=["hsbc_revolution"])

    assert "mcc" in result
    assert "mcc_category" in result
    assert "confidence" in result
    assert "recommendations" in result
    assert result["wallet_configured"] is True
    assert result["wallet_stored"] is False


def test_unknown_merchant_with_keyword_gets_recommendations():
    result = lookup_hosted("zzznewramen9999", cards=["uob_ppv", "citi_rewards_mc"])

    assert result["merchant_matched"] is False
    assert "routing_note" in result
    assert len(result["recommendations"]) > 0


def test_unknown_merchant_keyword_infers_dining_mcc():
    result = lookup_hosted("zzznewramen9999", cards=["uob_ppv", "citi_rewards_mc"])

    assert result["mcc"] == "5812"


def test_unknown_merchant_with_category_param_gets_recommendations():
    result = lookup_hosted("xyzzy_cafe_99", cards=["uob_ppv", "citi_rewards_mc"], category="dining")

    assert result["merchant_matched"] is False
    assert result["mcc"] == "5812"
    assert len(result["recommendations"]) > 0


def test_dbs_yuu_earns_base_rate_on_unknown_ramen_fallback():
    result = lookup_hosted("zzznewramen9999", cards=["dbs_yuu_visa", "uob_ppv"])

    yuu = next((r for r in result["recommendations"] if r["card_id"] == "dbs_yuu_visa"), None)
    if yuu:
        assert yuu["earn_rate_mpd"] == pytest.approx(0.14)


def test_truly_unknown_merchant_no_keyword_no_category_returns_not_found():
    result = lookup_hosted("xyzzy_unknown_place_9999", cards=["uob_ppv"])

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


def test_recommend_stack_requires_cards():
    with pytest.raises(TypeError):
        recommend_stack()  # type: ignore[call-arg]


def test_demo_loader_still_has_sample_data():
    loader = DataLoader()

    assert loader.cards()
    assert loader.merchants()
