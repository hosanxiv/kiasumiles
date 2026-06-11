import pytest
from kiasumiles.data.loader import DataLoader, MerchantRecord
from kiasumiles.engine.merchant import find_merchant, infer_mcc_from_name


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


def test_infer_mcc_dining_keywords():
    assert infer_mcc_from_name("fire ramen") == "5812"
    assert infer_mcc_from_name("Sushi Tei") == "5812"
    assert infer_mcc_from_name("the coffee club") == "5812"


def test_infer_mcc_grocery_keywords():
    assert infer_mcc_from_name("sheng siong supermarket") == "5411"
    assert infer_mcc_from_name("Cold Storage Buona Vista") == "5411"


def test_infer_mcc_transport_keywords():
    assert infer_mcc_from_name("Grab ride") == "4121"
    assert infer_mcc_from_name("Gojek taxi") == "4121"


def test_infer_mcc_petrol_keywords():
    assert infer_mcc_from_name("Shell petrol Woodlands") == "5541"
    assert infer_mcc_from_name("Caltex AMK") == "5541"


def test_infer_mcc_pharmacy_keywords():
    assert infer_mcc_from_name("Watsons Tampines") == "5912"
    assert infer_mcc_from_name("Guardian pharmacy") == "5912"


def test_infer_mcc_no_match_returns_none():
    assert infer_mcc_from_name("xyzzy unknown place 99") is None


def test_infer_mcc_case_insensitive():
    assert infer_mcc_from_name("RAMEN KEISUKE") == "5812"
