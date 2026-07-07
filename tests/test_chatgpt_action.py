from __future__ import annotations

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
    assert "/api/chatgpt/recommend-stack" in spec["paths"]


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
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["wallet_stored"] is False
    assert payload["wallet_configured"] is True
    assert payload["recommendations"]
    assert_no_public_technical_keys(payload)
