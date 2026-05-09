import pytest
from kiasumiles.data.loader import DataLoader, MerchantRecord
from kiasumiles.engine.merchant import find_merchant


@pytest.fixture
def records() -> list[MerchantRecord]:
    return DataLoader().merchants()


def test_exact_match(records):
    match, is_exact = find_merchant("NTUC FairPrice", None, None, records)
    assert match is not None
    assert is_exact is True
    assert match.mcc == "5411"


def test_case_insensitive_match(records):
    match, is_exact = find_merchant("ntuc fairprice", None, None, records)
    assert match is not None
    assert is_exact is True


def test_fuzzy_match_typo(records):
    match, is_exact = find_merchant("NTUC Fair Price", None, None, records)
    assert match is not None
    assert is_exact is False


def test_no_match_returns_none(records):
    match, is_exact = find_merchant("xyzzy_nonexistent_99", None, None, records)
    assert match is None


def test_channel_filter_prefers_matching_channel(records):
    """When channel is specified, prefer records that match that channel."""
    match, _ = find_merchant("Grab", None, "app", records)
    if match:
        assert match.channel in ("app", "any")
