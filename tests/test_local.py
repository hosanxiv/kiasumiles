from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from kiasumiles import client_wallet, hosted, local
from kiasumiles.hosted_client import HostedClient, HostedServiceError


class FakeHostedClient:
    def __init__(self):
        self.lookup_calls = []
        self.stack_calls = []
        self.inspect_result = {
            "cards": ["UOB Preferred Platinum Visa"],
            "unmatched_cards": [],
        }
        self.fail_lookup = False

    def list_cards(self, bank=None):
        return {
            "cards": [{"card_name": "UOB Preferred Platinum Visa", "bank": "UOB"}],
            "filtered_by_bank": bank,
        }

    def inspect_wallet(self, cards):
        return self.inspect_result

    def lookup(self, merchant, cards, outlet=None, channel=None, category=None):
        self.lookup_calls.append(
            {
                "merchant": merchant,
                "cards": cards,
                "outlet": outlet,
                "channel": channel,
                "category": category,
            }
        )
        if self.fail_lookup:
            raise HostedServiceError("The KiasuMiles hosted service is unavailable.")
        return {
            "merchant": merchant,
            "recommendations": [{"card_name": "UOB Preferred Platinum Visa"}],
            "wallet_stored": False,
        }

    def recommend_stack(self, cards, top_n=3):
        self.stack_calls.append({"cards": cards, "top_n": top_n})
        return {"coverage": []}

    def data_version(self):
        return {"data_version": "2026-07", "status": "ok"}


@pytest.fixture
def local_runtime(tmp_path, monkeypatch):
    client = FakeHostedClient()
    monkeypatch.setattr(client_wallet, "WALLET_PATH", tmp_path / "wallet.yaml")
    monkeypatch.setattr(local, "_client", client)
    return client


def test_configure_validates_and_saves_canonical_names(local_runtime):
    result = local.kiasumiles_configure(["uob_ppv", "Amaze (Instarem)"])

    assert result == {
        "saved_cards": ["UOB Preferred Platinum Visa", "Amaze (Instarem)"],
        "wallet_configured": True,
        "wallet_stored_locally": True,
    }
    assert client_wallet.load_wallet() == [
        "UOB Preferred Platinum Visa",
        "Amaze (Instarem)",
    ]


def test_invalid_configuration_leaves_existing_wallet_unchanged(local_runtime):
    client_wallet.save_wallet(["UOB Preferred Platinum Visa"])
    local_runtime.inspect_result = {
        "cards": ["UOB Preferred Platinum Visa"],
        "unmatched_cards": ["Imaginary Card"],
    }

    result = local.kiasumiles_configure(["uob_ppv", "Imaginary Card"])

    assert result["wallet_configured"] is True
    assert result["wallet_changed"] is False
    assert "could not be matched" in result["message"]
    assert client_wallet.load_wallet() == ["UOB Preferred Platinum Visa"]


def test_configuration_returns_clear_message_when_local_save_fails(local_runtime, monkeypatch):
    def fail(cards):
        raise client_wallet.WalletFileError("write failed")

    monkeypatch.setattr(client_wallet, "save_wallet", fail)

    result = local.kiasumiles_configure(["uob_ppv"])

    assert result["wallet_configured"] is False
    assert result["wallet_changed"] is False
    assert "could not be saved" in result["message"]


def test_get_wallet_resolves_existing_id_wallet_to_plain_names(local_runtime):
    client_wallet.save_wallet(["uob_ppv", "amaze"])

    result = local.kiasumiles_get_wallet()

    assert result["cards"] == ["UOB Preferred Platinum Visa", "Amaze (Instarem)"]
    assert result["wallet_stored_locally"] is True


def test_lookup_automatically_injects_saved_wallet(local_runtime):
    client_wallet.save_wallet(["uob_ppv", "amaze"])

    result = local.kiasumiles_lookup("Sushiro", channel="contactless")

    assert result["wallet_configured"] is True
    assert result["wallet_stored_locally"] is True
    assert local_runtime.lookup_calls == [
        {
            "merchant": "Sushiro",
            "cards": ["uob_ppv", "amaze"],
            "outlet": None,
            "channel": "contactless",
            "category": None,
        }
    ]


def test_lookup_without_wallet_requires_setup_without_calling_host(local_runtime):
    result = local.kiasumiles_lookup("Sushiro")

    assert result["wallet_configured"] is False
    assert result["recommendations"] == []
    assert local_runtime.lookup_calls == []


def test_recommend_stack_uses_saved_wallet(local_runtime):
    client_wallet.save_wallet(["uob_ppv"])

    result = local.kiasumiles_recommend_stack(top_n=2)

    assert result["wallet_stored_locally"] is True
    assert local_runtime.stack_calls == [{"cards": ["uob_ppv"], "top_n": 2}]


def test_hosted_failure_returns_clear_message(local_runtime):
    client_wallet.save_wallet(["uob_ppv"])
    local_runtime.fail_lookup = True

    result = local.kiasumiles_lookup("Sushiro")

    assert result["recommendations"] == []
    assert "temporarily unavailable" in result["message"]
    assert result["wallet_configured"] is True


def test_agent_guide_describes_local_persistence(local_runtime):
    guide = local.kiasumiles_agent_guide()

    assert guide["runtime"]["wallet_stored_locally"] is True
    assert "kiasumiles_configure" in {tool["name"] for tool in guide["tools"]}


def test_corrupt_wallet_requests_reconfiguration(local_runtime):
    client_wallet.WALLET_PATH.write_text("cards: [broken\n", encoding="utf-8")

    result = local.kiasumiles_lookup("Sushiro")

    assert result["wallet_configured"] is False
    assert result["recommendations"] == []
    assert "configure it again" in result["message"]


def test_local_wallet_round_trip_uses_real_hosted_action(tmp_path, monkeypatch):
    monkeypatch.setattr(client_wallet, "WALLET_PATH", tmp_path / "wallet.yaml")
    web = TestClient(hosted.app)

    def transport(method, path, payload):
        response = web.request(method, path, json=payload)
        response.raise_for_status()
        return response.json()

    monkeypatch.setattr(local, "_client", HostedClient(transport=transport))

    configured = local.kiasumiles_configure(
        ["UOB Preferred Platinum Visa", "Amaze (Instarem)"]
    )
    result = local.kiasumiles_lookup(
        "NTUC FairPrice",
        channel="mobile_contactless",
    )

    assert configured["saved_cards"] == [
        "UOB Preferred Platinum Visa",
        "Amaze (Instarem)",
    ]
    assert result["recommendations"]
    assert result["wallet_stored"] is False
    assert result["wallet_stored_locally"] is True
