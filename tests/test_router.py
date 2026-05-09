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
