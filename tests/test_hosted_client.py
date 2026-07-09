from __future__ import annotations

from urllib.error import URLError

import pytest

from kiasumiles.hosted_client import HostedClient, HostedServiceError, request_json


def test_list_cards_passes_bank_filter_to_hosted_service():
    calls = []

    def transport(method, path, payload):
        calls.append((method, path, payload))
        return {"cards": [{"card_name": "UOB Preferred Platinum Visa"}]}

    result = HostedClient(transport=transport).list_cards("UOB")

    assert result["cards"][0]["card_name"] == "UOB Preferred Platinum Visa"
    assert calls == [("GET", "/api/chatgpt/cards?bank=UOB", None)]


def test_inspect_wallet_returns_names_and_unmatched_cards():
    def transport(method, path, payload):
        assert method == "POST"
        assert path == "/api/chatgpt/recommend-stack"
        assert payload == {"cards": ["uob_ppv", "not-real"], "top_n": 1}
        return {
            "wallet_cards": ["UOB Preferred Platinum Visa"],
            "unmatched_cards": ["not-real"],
        }

    result = HostedClient(transport=transport).inspect_wallet(["uob_ppv", "not-real"])

    assert result == {
        "cards": ["UOB Preferred Platinum Visa"],
        "unmatched_cards": ["not-real"],
    }


def test_lookup_sends_saved_wallet_with_merchant():
    calls = []

    def transport(method, path, payload):
        calls.append((method, path, payload))
        return {"recommendations": [{"card_name": "Citi Rewards Mastercard"}]}

    result = HostedClient(transport=transport).lookup(
        merchant="Sushiro",
        cards=["citi_rewards_mc"],
        channel="contactless",
    )

    assert result["recommendations"][0]["card_name"] == "Citi Rewards Mastercard"
    assert calls == [
        (
            "POST",
            "/api/chatgpt/lookup",
            {
                "merchant": "Sushiro",
                "cards": ["citi_rewards_mc"],
                "channel": "contactless",
            },
        )
    ]


def test_recommend_stack_and_data_version_use_existing_routes():
    calls = []

    def transport(method, path, payload):
        calls.append((method, path, payload))
        if path == "/health":
            return {"status": "ok", "data_version": "2026-07"}
        return {"coverage": []}

    client = HostedClient(transport=transport)

    assert client.recommend_stack(["uob_ppv"], top_n=2) == {"coverage": []}
    assert client.data_version()["data_version"] == "2026-07"
    assert calls == [
        ("POST", "/api/chatgpt/recommend-stack", {"cards": ["uob_ppv"], "top_n": 2}),
        ("GET", "/health", None),
    ]


def test_request_json_turns_network_failure_into_hosted_service_error(monkeypatch):
    def fail(*args, **kwargs):
        raise URLError("offline")

    monkeypatch.setattr("kiasumiles.hosted_client.urlopen", fail)

    with pytest.raises(HostedServiceError, match="hosted service"):
        request_json("https://kiasumiles.space", "GET", "/health", None)


def test_request_json_rejects_invalid_json(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return b"not-json"

    monkeypatch.setattr("kiasumiles.hosted_client.urlopen", lambda *args, **kwargs: Response())

    with pytest.raises(HostedServiceError, match="invalid response"):
        request_json("https://kiasumiles.space", "GET", "/health", None)
