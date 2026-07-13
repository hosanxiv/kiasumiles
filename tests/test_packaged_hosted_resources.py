import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PROOF_PATH = "/kiasumiles/assets/proof/kiasumiles-real-life-720.webp"
LOGO_ASSETS = (
    ("fairprice-real-crop.png", "image/png"),
    ("grab-colour.svg", "image/svg+xml"),
    ("watsons-crop.png", "image/png"),
    ("shell-colour.svg", "image/svg+xml"),
    ("shopee-real-crop.png", "image/png"),
    ("Singapore_Airlines_Logo.svg", "image/svg+xml"),
)
LOGO_PATHS = [
    f"/kiasumiles/assets/logos/{filename}"
    for filename, _ in LOGO_ASSETS
]
MAX_SDIST_BYTES = 5 * 1024 * 1024
FORBIDDEN_SDIST_TOP_LEVEL = {
    ".playwright-cli",
    ".superpowers",
    "live-codex-captures",
    "output",
}


def test_built_distributions_serve_lightweight_resources_without_legacy_media(tmp_path):
    dist_dir = tmp_path / "dist"
    for target in ("wheel", "sdist"):
        subprocess.run(
            [
                sys.executable,
                "-m",
                "hatchling",
                "build",
                "-t",
                target,
                "-d",
                str(dist_dir),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    wheel = next(dist_dir.glob("*.whl"))
    sdist = next(dist_dir.glob("*.tar.gz"))
    install_dir = tmp_path / "installed"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-index",
            "--no-deps",
            "--no-compile",
            "--target",
            str(install_dir),
            str(wheel),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    smoke_script = f"""
import json
from starlette.testclient import TestClient
from kiasumiles import hosted

client = TestClient(hosted.app, raise_server_exceptions=False)
paths = ["/", "/privacy", "/favicon.svg", {PROOF_PATH!r}] + {LOGO_PATHS!r}
print(json.dumps({{
    path: {{
        "status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "cache_control": response.headers.get("cache-control"),
    }}
    for path in paths
    for response in [client.get(path)]
}}))
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(install_dir)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    smoke = subprocess.run(
        [sys.executable, "-c", smoke_script],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    routes = json.loads(smoke.stdout)

    with zipfile.ZipFile(wheel) as archive:
        wheel_files = set(archive.namelist())
    extract_dir = tmp_path / "extracted"
    with tarfile.open(sdist) as archive:
        sdist_files = {
            "/".join(Path(member.name).parts[1:])
            for member in archive.getmembers()
        }
        archive.extractall(extract_dir, filter="data")
    extracted_root = next(extract_dir.iterdir())

    expected_routes = {
        "/": {
            "status": 200,
            "content_type": "text/html; charset=utf-8",
            "cache_control": "public, max-age=0, must-revalidate",
        },
        "/privacy": {
            "status": 200,
            "content_type": "text/html; charset=utf-8",
            "cache_control": "public, max-age=0, must-revalidate",
        },
        "/favicon.svg": {
            "status": 200,
            "content_type": "image/svg+xml",
            "cache_control": "public, max-age=31536000, immutable",
        },
        PROOF_PATH: {
            "status": 200,
            "content_type": "image/webp",
            "cache_control": "public, max-age=31536000, immutable",
        },
    }
    expected_routes.update(
        {
            path: {
                "status": 200,
                "content_type": media_type,
                "cache_control": None,
            }
            for path, (_, media_type) in zip(LOGO_PATHS, LOGO_ASSETS)
        }
    )
    assert routes == expected_routes
    required_resources = {
        "kiasumiles/static/kiasumiles/index.html",
        "kiasumiles/static/kiasumiles/privacy.html",
        "kiasumiles/static/kiasumiles/favicon.svg",
        "kiasumiles/static/kiasumiles/assets/proof/kiasumiles-real-life-720.webp",
        "kiasumiles/static/kiasumiles/assets/proof/kiasumiles-real-life-1460.webp",
        "kiasumiles/static/kiasumiles/assets/proof/kiasumiles-real-life-1460.jpg",
    } | {
        f"kiasumiles/static/kiasumiles/assets/logos/{filename}"
        for filename, _ in LOGO_ASSETS
    }
    assert required_resources <= wheel_files
    required_sdist_files = required_resources | {
        "LICENSE",
        "PKG-INFO",
        "README.md",
        "pyproject.toml",
        "kiasumiles/__init__.py",
    }
    assert required_sdist_files <= sdist_files
    assert not any(path == "tests" or path.startswith("tests/") for path in sdist_files)

    extracted_env = os.environ.copy()
    extracted_env["PYTHONPATH"] = str(extracted_root)
    extracted_env["PYTHONDONTWRITEBYTECODE"] = "1"
    imported = subprocess.run(
        [sys.executable, "-c", "import kiasumiles; print(kiasumiles.__file__)"],
        cwd=extracted_root,
        env=extracted_env,
        check=True,
        capture_output=True,
        text=True,
    )
    assert Path(imported.stdout.strip()).resolve().is_relative_to(extracted_root.resolve())
    package_metadata = (extracted_root / "PKG-INFO").read_text(encoding="utf-8")
    assert "\nName: kiasumiles-mcp\n" in package_metadata
    assert "\nVersion: 1.0.2\n" in package_metadata

    forbidden_sdist_files = sorted(
        path
        for path in sdist_files
        if path.split("/", 1)[0] in FORBIDDEN_SDIST_TOP_LEVEL
        or path.startswith(("interview-", "straits-times-"))
    )
    assert forbidden_sdist_files == []
    assert sdist.stat().st_size < MAX_SDIST_BYTES

    for packaged_files in (wheel_files, sdist_files):
        assert "kiasumiles/static/kiasumiles/hero.png" not in packaged_files
        assert "kiasumiles/static/kiasumiles/product-demo-60s.mp4" not in packaged_files
        assert (
            "kiasumiles/static/kiasumiles/assets/logos/"
            "uob-preferred-platinum-visa-card.png"
        ) not in packaged_files
