import pytest
from pathlib import Path
import yaml
from kiasumiles.engine.wallet import load_wallet, save_wallet, WALLET_PATH


def test_save_wallet_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr("kiasumiles.engine.wallet.WALLET_PATH", tmp_path / "wallet.yaml")
    result = save_wallet(["hsbc_revolution", "uob_ppv"])
    assert result.exists()
    data = yaml.safe_load(result.read_text())
    assert data["cards"] == ["hsbc_revolution", "uob_ppv"]


def test_load_wallet_returns_cards(tmp_path, monkeypatch):
    wpath = tmp_path / "wallet.yaml"
    wpath.write_text("cards:\n  - hsbc_revolution\n  - uob_ppv\n")
    monkeypatch.setattr("kiasumiles.engine.wallet.WALLET_PATH", wpath)
    cards = load_wallet()
    assert cards == ["hsbc_revolution", "uob_ppv"]


def test_load_wallet_missing_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("kiasumiles.engine.wallet.WALLET_PATH", tmp_path / "missing.yaml")
    cards = load_wallet()
    assert cards == []


def test_save_wallet_creates_parent_dirs(tmp_path, monkeypatch):
    nested = tmp_path / "deep" / "nested" / "wallet.yaml"
    monkeypatch.setattr("kiasumiles.engine.wallet.WALLET_PATH", nested)
    save_wallet(["citi_rewards_mc"])
    assert nested.exists()


def test_load_wallet_empty_cards_returns_empty_list(tmp_path, monkeypatch):
    wpath = tmp_path / "wallet.yaml"
    wpath.write_text("cards:\n")  # empty cards key
    monkeypatch.setattr("kiasumiles.engine.wallet.WALLET_PATH", wpath)
    result = load_wallet()
    assert result == []
