# kiasumiles/data/updater.py
from __future__ import annotations
import json
from pathlib import Path
import httpx

_BASE = "https://raw.githubusercontent.com/hosanxiv/kiasumiles-data/main"
VERSION_URL = f"{_BASE}/version.json"
_MERCHANT_URL = f"{_BASE}/merchant_mcc.csv"
_CARDS_URL = f"{_BASE}/card_rules.csv"
_CACHE_DIR = Path.home() / ".kiasumiles" / "data"
_TIMEOUT = 10.0


def check_version() -> dict | None:
    """Fetch remote version.json. Returns dict or None on failure."""
    try:
        r = httpx.get(VERSION_URL, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def download_csv(url: str, dest: Path) -> None:
    """Download a CSV file to dest, creating parent dirs as needed."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = httpx.get(url, timeout=30.0)
    r.raise_for_status()
    dest.write_bytes(r.content)


def local_version() -> str | None:
    """Read cached version string, or None if no cache exists."""
    version_file = _CACHE_DIR / "version.txt"
    if not version_file.exists():
        return None
    return version_file.read_text().strip()


def refresh(force: bool = False) -> dict:
    """
    Pull latest CSVs from GitHub if remote version is newer than local.
    Returns a result dict for the kiasumiles_refresh MCP tool.
    """
    prev = local_version()
    remote = check_version()

    if remote is None:
        return {
            "previous_version": prev,
            "current_version": prev,
            "merchants_updated": 0,
            "cards_updated": 0,
            "source": "offline",
            "message": "Could not reach GitHub. Using cached data.",
        }

    remote_version = remote.get("version", "")
    # versions are YYYY-MM-DD ISO dates; lexicographic compare is correct
    if not force and prev and prev >= remote_version:
        return {
            "previous_version": prev,
            "current_version": prev,
            "merchants_updated": 0,
            "cards_updated": 0,
            "source": "cache",
            "message": "Already up to date.",
        }

    try:
        download_csv(_MERCHANT_URL, _CACHE_DIR / "merchant_mcc.csv")
        download_csv(_CARDS_URL, _CACHE_DIR / "card_rules.csv")
        (_CACHE_DIR / "version.txt").write_text(remote_version)
    except Exception:
        return {
            "previous_version": prev,
            "current_version": prev,
            "merchants_updated": 0,
            "cards_updated": 0,
            "source": "error",
            "message": "Download failed. Retaining existing data.",
        }

    return {
        "previous_version": prev,
        "current_version": remote_version,
        "merchants_updated": remote.get("merchants_updated", 0),
        "cards_updated": remote.get("cards_updated", 0),
        "source": "github",
    }
