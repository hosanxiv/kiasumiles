from pathlib import Path


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
