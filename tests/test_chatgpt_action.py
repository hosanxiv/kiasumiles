from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from kiasumiles import hosted


def assert_no_public_technical_keys(value):
    if isinstance(value, dict):
        forbidden = {"card_id", "mcc", "mcc_category", "reason_codes"}
        assert forbidden.isdisjoint(value)
        for child in value.values():
            assert_no_public_technical_keys(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_public_technical_keys(child)


def test_chatgpt_openapi_route_describes_action_surface():
    client = TestClient(hosted.app)
    response = client.get("/api/chatgpt/openapi.json")

    assert response.status_code == 200
    spec = response.json()
    assert spec["openapi"].startswith("3.")
    assert "/api/chatgpt/lookup" in spec["paths"]
    assert "/api/chatgpt/compare-payment-methods" in spec["paths"]
    assert "/api/chatgpt/changes" in spec["paths"]
    assert "/api/chatgpt/recommend-stack" in spec["paths"]
    lookup_schema = spec["paths"]["/api/chatgpt/lookup"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    assert lookup_schema["properties"]["amount_sgd"]["exclusiveMinimum"] == 0


def test_chatgpt_cards_route_omits_internal_ids():
    client = TestClient(hosted.app)
    response = client.get("/api/chatgpt/cards?bank=UOB")

    assert response.status_code == 200
    payload = response.json()
    assert payload["cards"]
    assert all("card_name" in card for card in payload["cards"])
    assert_no_public_technical_keys(payload)


def test_chatgpt_lookup_requires_current_request_cards():
    client = TestClient(hosted.app)
    response = client.post(
        "/api/chatgpt/lookup",
        json={"merchant": "NTUC FairPrice", "cards": []},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["wallet_stored"] is False
    assert payload["recommendations"] == []
    assert "No cards were supplied" in payload["message"]
    assert_no_public_technical_keys(payload)


def test_chatgpt_lookup_accepts_card_names_and_sanitizes_response():
    client = TestClient(hosted.app)
    response = client.post(
        "/api/chatgpt/lookup",
        json={
            "merchant": "NTUC FairPrice",
            "cards": ["UOB Preferred Platinum Visa", "Citi Rewards Mastercard"],
            "channel": "mobile_contactless",
            "amount_sgd": 25,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["wallet_stored"] is False
    assert payload["wallet_configured"] is True
    assert payload["recommendations"]
    assert payload["conditional_recommendations"][0]["estimated_miles"] is not None
    assert_no_public_technical_keys(payload)


def test_chatgpt_compare_payment_methods_is_stateless_and_sanitized():
    client = TestClient(hosted.app)
    response = client.post(
        "/api/chatgpt/compare-payment-methods",
        json={
            "merchant": "NTUC FairPrice",
            "cards": ["Citi Rewards Mastercard", "Amaze"],
            "amount_sgd": 20,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["wallet_stored"] is False
    assert payload["methods"][-1]["payment_method"] == "amaze"
    assert_no_public_technical_keys(payload)


def test_chatgpt_lookup_rejects_invalid_amount():
    client = TestClient(hosted.app)
    response = client.post(
        "/api/chatgpt/lookup",
        json={"merchant": "NTUC FairPrice", "cards": ["UOB Preferred Platinum Visa"], "amount_sgd": 0},
    )

    assert response.status_code == 400


def test_chatgpt_changes_route_is_source_neutral():
    client = TestClient(hosted.app)
    response = client.get("/api/chatgpt/changes?since=2026-08-01")

    assert response.status_code == 200
    payload = response.json()
    assert payload["changes"]
    assert all("source" not in key for change in payload["changes"] for key in change)


@pytest.mark.parametrize("path", ["lookup", "compare-payment-methods"])
@pytest.mark.parametrize("eligible,expected", [(True, 80), (False, 40), (None, 40)])
def test_revolution_tier_public_api(path, eligible, expected):
    client = TestClient(hosted.app)
    response = client.post(f"/api/chatgpt/{path}", json={
        "merchant": "Marutama Ramen", "cards": ["HSBC Revolution"],
        "channel": "online", "amount_sgd": 10, "revolution_ega_eligible": eligible,
    })
    assert response.status_code == 200
    payload = response.json()
    rows = (payload["conditional_recommendations"] if path == "lookup" else
            [method["best_if_conditions_met"] for method in payload["methods"]])
    assert all(row["estimated_miles"] == expected for row in rows)
    assert all(row["rate_status"] == "conditional" for row in rows)
    assert_no_public_technical_keys(payload)


@pytest.mark.parametrize("path", ["lookup", "compare-payment-methods"])
def test_revolution_public_schema_and_validation(path):
    client = TestClient(hosted.app)
    spec = client.get("/api/chatgpt/openapi.json").json()
    schema = spec["paths"][f"/api/chatgpt/{path}"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    assert schema["properties"]["revolution_ega_eligible"]["type"] == ["boolean", "null"]
    response = client.post(f"/api/chatgpt/{path}", json={
        "merchant": "Unknown", "cards": [], "revolution_ega_eligible": "true",
    })
    assert response.status_code == 400


@pytest.mark.parametrize("path", ["lookup", "compare-payment-methods"])
def test_revolution_monthly_cap_public_api(path):
    client = TestClient(hosted.app)
    arguments = {"merchant": "Marutama Ramen", "cards": ["HSBC Revolution"],
                 "channel": "online", "amount_sgd": 2, "revolution_ega_eligible": True,
                 "revolution_prior_eligible_spend_sgd": 1199}
    response = client.post(f"/api/chatgpt/{path}", json=arguments)
    assert response.status_code == 200
    payload = response.json()
    rows = (payload["recommendations"] if path == "lookup" else
            [method["best_guaranteed"] for method in payload["methods"]])
    assert all(row["estimated_miles"] == 8.4 for row in rows)
    assert_no_public_technical_keys(payload)
    arguments.update(cards=[], revolution_prior_eligible_spend_sgd=True)
    assert client.post(f"/api/chatgpt/{path}", json=arguments).status_code == 400
