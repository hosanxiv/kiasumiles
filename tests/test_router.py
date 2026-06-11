import pytest
from kiasumiles.data.loader import DataLoader, CardRule
from kiasumiles.engine.router import effective_mpd, rank_cards


@pytest.fixture
def cards() -> list[CardRule]:
    return DataLoader().cards()


def test_effective_mpd_eligible_mcc(cards):
    rev = next(c for c in cards if c.card_id == "hsbc_revolution")
    result = effective_mpd(rev, "5812", wallet_has_amaze=False)
    assert result == 4.0


def test_effective_mpd_ineligible_mcc_returns_base(cards):
    rev = next(c for c in cards if c.card_id == "hsbc_revolution")
    result = effective_mpd(rev, "9999", wallet_has_amaze=False)
    assert result == rev.base_rate_mpd


def test_effective_mpd_amaze_card_nets_fee(cards):
    amaze = next(c for c in cards if c.card_id == "amaze_citi")
    result = effective_mpd(amaze, "5812", wallet_has_amaze=True)
    assert result == pytest.approx(3.96, rel=0.01)  # 4mpd * (1 - 0.01)


def test_effective_mpd_amaze_card_without_amaze_in_wallet(cards):
    amaze = next(c for c in cards if c.card_id == "amaze_citi")
    result = effective_mpd(amaze, "5812", wallet_has_amaze=False)
    assert result == amaze.base_rate_mpd


def test_rank_cards_returns_top_n(cards):
    wallet_ids = ["hsbc_revolution", "uob_ppv", "dbs_altitude_visa"]
    wallet_cards = [c for c in cards if c.card_id in wallet_ids]
    results = rank_cards("5812", wallet_cards, wallet_has_amaze=False, top_n=3)
    assert len(results) <= 3
    assert results[0]["card_id"] == "hsbc_revolution"
    assert results[0]["earn_rate_mpd"] == 4.0


def test_rank_cards_no_wallet_returns_top5_from_all(cards):
    results = rank_cards("5812", cards, wallet_has_amaze=False, top_n=5)
    assert len(results) <= 5
    assert results[0]["earn_rate_mpd"] >= 4.0


def test_rank_cards_sorted_descending(cards):
    results = rank_cards("5812", cards, wallet_has_amaze=False, top_n=5)
    rates = [r["earn_rate_mpd"] for r in results]
    assert rates == sorted(rates, reverse=True)


def test_effective_mpd_amaze_card_ineligible_mcc_returns_base(cards):
    amaze = next(c for c in cards if c.card_id == "amaze_citi")
    result = effective_mpd(amaze, "9999", wallet_has_amaze=True)
    assert result == amaze.base_rate_mpd


def test_dbs_yuu_base_rate_at_non_yuu_merchant(cards):
    yuu = next(c for c in cards if c.card_id == "dbs_yuu_visa")
    result = effective_mpd(yuu, "5814", wallet_has_amaze=False, merchant_name="Marutama Ramen @ The Central")
    assert result == pytest.approx(0.14)


def test_dbs_yuu_earns_bonus_at_eligible_merchant(cards):
    yuu = next(c for c in cards if c.card_id == "dbs_yuu_visa")
    result = effective_mpd(yuu, "5411", wallet_has_amaze=False, merchant_name="Cold Storage")
    assert result == 10.0


def test_dbs_wwmc_base_rate_at_physical_merchant(cards):
    wwmc = next(c for c in cards if c.card_id == "dbs_wwmc")
    result = effective_mpd(wwmc, "5812", wallet_has_amaze=False, channel="any")
    assert result == pytest.approx(0.4)


def test_dbs_wwmc_earns_bonus_at_online_merchant(cards):
    wwmc = next(c for c in cards if c.card_id == "dbs_wwmc")
    result = effective_mpd(wwmc, "5812", wallet_has_amaze=False, channel="online")
    assert result == 4.0


def test_cap_summary_with_cap_and_blocks(cards):
    uob_ppv = next(c for c in cards if c.card_id == "uob_ppv")
    results = rank_cards("5812", [uob_ppv], wallet_has_amaze=False, top_n=1)
    assert results[0]["cap_summary"] == "S$600 cap / calendar month · earns in S$5 blocks"


def test_cap_summary_with_cap_no_blocks(cards):
    citi = next(c for c in cards if c.card_id == "citi_rewards_mc")
    results = rank_cards("5812", [citi], wallet_has_amaze=False, top_n=1)
    assert results[0]["cap_summary"] == "S$1,000 cap / statement month"


def test_cap_summary_no_cap_with_blocks(cards):
    altitude = next(c for c in cards if c.card_id == "dbs_altitude_visa")
    results = rank_cards("9999", [altitude], wallet_has_amaze=False, top_n=1)
    assert results[0]["cap_summary"] == "No cap · earns in S$5 blocks"


def test_cap_summary_no_cap_no_blocks(cards):
    ocbc = next(c for c in cards if c.card_id == "ocbc_90n_visa")
    results = rank_cards("9999", [ocbc], wallet_has_amaze=False, top_n=1)
    assert results[0]["cap_summary"] == "No cap"


def test_rank_cards_includes_min_spend(cards):
    wallet = [c for c in cards if c.card_id in ("uob_ppv", "uob_signature")]
    results = rank_cards("5812", wallet, wallet_has_amaze=False, top_n=5)
    sig = next(r for r in results if r["card_id"] == "uob_signature")
    assert sig["min_spend_sgd"] == 1000.0
    ppv = next(r for r in results if r["card_id"] == "uob_ppv")
    assert ppv["min_spend_sgd"] is None


def test_rank_cards_includes_reason_summary(cards):
    uob_ppv = next(c for c in cards if c.card_id == "uob_ppv")
    results = rank_cards("5411", [uob_ppv], wallet_has_amaze=False, top_n=1, channel="mobile_contactless")

    assert "reason_summary" in results[0]
    assert "mcc_eligible" in results[0]["reason_codes"]
    assert "channel_eligible" in results[0]["reason_codes"]
    assert "bonus_rate_applied" in results[0]["reason_codes"]


def test_rank_cards_flags_wrong_channel_gotcha(cards):
    uob_ppv = next(c for c in cards if c.card_id == "uob_ppv")
    results = rank_cards("5411", [uob_ppv], wallet_has_amaze=False, top_n=1, channel="contactless")

    assert results[0]["earn_rate_mpd"] == pytest.approx(uob_ppv.base_rate_mpd)
    assert "channel_not_eligible" in results[0]["reason_codes"]
    assert results[0]["gotchas"]


def test_citi_rewards_mobile_contactless_grocery_falls_to_base(cards):
    citi = next(c for c in cards if c.card_id == "citi_rewards_mc")
    results = rank_cards("5411", [citi], wallet_has_amaze=False, top_n=1, channel="mobile_contactless")

    assert results[0]["earn_rate_mpd"] == pytest.approx(citi.base_rate_mpd)
    assert "channel_not_eligible" in results[0]["reason_codes"]
    assert "bonus_rate_applied" not in results[0]["reason_codes"]
    assert "shopping-like categories" in results[0]["gotchas"][0]
