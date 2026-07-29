import json
from pathlib import Path

from starlette.testclient import TestClient

from api.index import app as vercel_app


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_vercelignore_only_excludes_the_root_assets_directory() -> None:
    patterns = {
        line.strip()
        for line in (PROJECT_ROOT / ".vercelignore").read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert "/assets/" in patterns
    assert "assets/" not in patterns


def test_vercelignore_excludes_private_and_local_artifacts() -> None:
    patterns = {
        line.strip()
        for line in (PROJECT_ROOT / ".vercelignore").read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    required = {
        ".impeccable/",
        ".playwright-cli/",
        ".superpowers/",
        "interview-*",
        "straits-times-*",
        "live-codex-captures/",
        "screenshots/",
        "tmp/",
        "output/",
        "**/supabase_logs.csv",
        "**/*supabase*logs*.csv",
        "*.log",
    }
    assert required <= patterns


def test_vercel_rewrite_forwards_the_original_public_path() -> None:
    config = json.loads((PROJECT_ROOT / "vercel.json").read_text())

    assert config["rewrites"] == [
        {
            "source": "/:path*",
            "destination": "/api/index.py?__kiasumiles_path=:path*",
        }
    ]


def test_vercel_entrypoint_restores_landing_and_health_paths() -> None:
    client = TestClient(vercel_app)
    landing = client.get("/api/index.py?__kiasumiles_path=")
    health = client.get("/api/index.py?__kiasumiles_path=health")

    assert landing.status_code == 200
    assert "The right card, before you tap." in landing.text
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
