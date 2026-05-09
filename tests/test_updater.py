# tests/test_updater.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from kiasumiles.data.updater import check_version, download_csv, VERSION_URL, refresh, local_version


def test_version_url_is_github():
    assert "raw.githubusercontent.com" in VERSION_URL
    assert "kiasumiles" in VERSION_URL.lower()


def test_check_version_returns_none_on_network_error():
    with patch("httpx.get", side_effect=Exception("network down")):
        result = check_version()
    assert result is None


def test_download_csv_writes_file(tmp_path):
    fake_content = b"merchant_name,mcc\nTest,5812\n"
    mock_response = MagicMock()
    mock_response.content = fake_content
    mock_response.raise_for_status = MagicMock()
    with patch("httpx.get", return_value=mock_response):
        out_path = tmp_path / "merchant_mcc.csv"
        download_csv("https://example.com/test.csv", out_path)
    assert out_path.read_bytes() == fake_content


def test_download_csv_creates_parent_dirs(tmp_path):
    fake_content = b"col\nval\n"
    mock_response = MagicMock()
    mock_response.content = fake_content
    mock_response.raise_for_status = MagicMock()
    with patch("httpx.get", return_value=mock_response):
        out_path = tmp_path / "sub" / "dir" / "file.csv"
        download_csv("https://example.com/file.csv", out_path)
    assert out_path.exists()


def test_refresh_offline_when_github_unreachable(tmp_path, monkeypatch):
    monkeypatch.setattr("kiasumiles.data.updater._CACHE_DIR", tmp_path)
    with patch("kiasumiles.data.updater.check_version", return_value=None):
        result = refresh(force=False)
    assert result["source"] == "offline"
    assert "message" in result


def test_refresh_cache_hit_when_up_to_date(tmp_path, monkeypatch):
    monkeypatch.setattr("kiasumiles.data.updater._CACHE_DIR", tmp_path)
    (tmp_path / "version.txt").write_text("2026-05-09")
    with patch("kiasumiles.data.updater.check_version", return_value={"version": "2026-05-09"}):
        with patch("kiasumiles.data.updater.download_csv") as dl:
            result = refresh(force=False)
            dl.assert_not_called()
    assert result["source"] == "cache"
    assert result["current_version"] == "2026-05-09"


def test_refresh_downloads_on_new_version(tmp_path, monkeypatch):
    monkeypatch.setattr("kiasumiles.data.updater._CACHE_DIR", tmp_path)
    (tmp_path / "version.txt").write_text("2026-04-01")
    fake_csv = b"merchant_name,mcc\nTest,5812\n"
    mock_resp = MagicMock()
    mock_resp.content = fake_csv
    mock_resp.raise_for_status = MagicMock()
    with patch("kiasumiles.data.updater.check_version", return_value={"version": "2026-05-09", "merchants_updated": 10, "cards_updated": 2}):
        with patch("httpx.get", return_value=mock_resp):
            result = refresh(force=False)
    assert result["source"] == "github"
    assert result["current_version"] == "2026-05-09"
    assert result["merchants_updated"] == 10
    assert (tmp_path / "version.txt").read_text() == "2026-05-09"
    assert (tmp_path / "merchant_mcc.csv").exists()
    assert (tmp_path / "card_rules.csv").exists()
