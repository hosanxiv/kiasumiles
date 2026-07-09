from __future__ import annotations

import yaml
import pytest

from kiasumiles.client_wallet import WalletFileError, load_wallet, save_wallet


def test_missing_wallet_returns_empty_list(tmp_path):
    assert load_wallet(tmp_path / "missing.yaml") == []


def test_wallet_round_trips_existing_format(tmp_path):
    path = tmp_path / "wallet.yaml"

    saved_path = save_wallet(["uob_ppv", "amaze"], path)

    assert saved_path == path
    assert load_wallet(path) == ["uob_ppv", "amaze"]
    assert yaml.safe_load(path.read_text(encoding="utf-8")) == {
        "cards": ["uob_ppv", "amaze"]
    }


def test_save_wallet_creates_parent_directories(tmp_path):
    path = tmp_path / "nested" / "wallet.yaml"

    save_wallet(["Citi Rewards Mastercard"], path)

    assert path.exists()


def test_save_wallet_wraps_filesystem_errors(tmp_path):
    blocked_parent = tmp_path / "not-a-directory"
    blocked_parent.write_text("occupied", encoding="utf-8")

    with pytest.raises(WalletFileError, match="could not be saved"):
        save_wallet(["uob_ppv"], blocked_parent / "wallet.yaml")


@pytest.mark.parametrize(
    "contents",
    [
        "cards: not-a-list\n",
        "cards:\n  - 123\n",
        "- uob_ppv\n",
        "cards: [unterminated\n",
    ],
)
def test_malformed_wallet_raises_clear_error(tmp_path, contents):
    path = tmp_path / "wallet.yaml"
    path.write_text(contents, encoding="utf-8")

    with pytest.raises(WalletFileError, match="wallet"):
        load_wallet(path)
