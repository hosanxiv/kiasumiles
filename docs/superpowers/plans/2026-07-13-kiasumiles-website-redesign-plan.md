# KiasuMiles Website Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current oversized, ambiguous landing page with a compact agent-first site that uses genuine proof, accurate request-scoped wallet language, accessible setup controls, and production-ready static assets.

**Architecture:** Keep the hosted MCP and deterministic recommendation engine unchanged. Continue serving one self-contained `index.html` through the thin FastMCP adapter, add a static privacy document, and add exact-name routes for versioned proof assets and a small favicon. Use a fresh production-agent conversation for the hero image and privacy-mask the full phone display in the supplied real-life photograph before it enters the public static directory.

**Tech Stack:** Python 3.10+, FastMCP, Starlette, pytest, semantic HTML, inline CSS and JavaScript, ImageMagick, Tesseract OCR, Chrome/Playwright browser verification, Vercel.

---

## File Structure

### Create

- `kiasumiles/static/kiasumiles/privacy.html`: public, nontechnical privacy policy using the same visual identity as the landing page.
- `kiasumiles/static/kiasumiles/favicon.svg`: lightweight KiasuMiles favicon so the browser console stays clean.
- `kiasumiles/static/kiasumiles/assets/proof/kiasumiles-agent-chat-480.webp`: small responsive hero proof.
- `kiasumiles/static/kiasumiles/assets/proof/kiasumiles-agent-chat-960.webp`: large responsive hero proof.
- `kiasumiles/static/kiasumiles/assets/proof/kiasumiles-agent-chat-960.png`: PNG fallback for the hero proof.
- `kiasumiles/static/kiasumiles/assets/proof/kiasumiles-in-use-wide-730.webp`: small desktop/tablet real-life proof.
- `kiasumiles/static/kiasumiles/assets/proof/kiasumiles-in-use-wide-1460.webp`: large desktop real-life proof.
- `kiasumiles/static/kiasumiles/assets/proof/kiasumiles-in-use-wide-1460.jpg`: JPEG fallback for the desktop real-life proof.
- `kiasumiles/static/kiasumiles/assets/proof/kiasumiles-in-use-portrait-480.webp`: small mobile real-life proof.
- `kiasumiles/static/kiasumiles/assets/proof/kiasumiles-in-use-portrait-960.webp`: large mobile real-life proof.
- `kiasumiles/static/kiasumiles/assets/proof/kiasumiles-in-use-portrait-960.jpg`: JPEG fallback for the mobile real-life proof.
- `tests/test_landing_page.py`: source-level copy, accessibility, privacy, and performance contracts for the landing page.

### Modify

- `kiasumiles/hosted.py`: add HTML cache headers, exact-name proof routes, favicon route, and static privacy rendering.
- `kiasumiles/static/kiasumiles/index.html`: replace the current base64-heavy set piece with the approved page and clipboard behavior.
- `tests/test_hosted.py`: replace obsolete landing expectations and add route, MIME, cache, privacy, and legacy-media coverage.

### Preserve

- `kiasumiles/landing.py`: legacy renderer; do not modify it.
- `kiasumiles/static/kiasumiles/hero.png`: keep its existing backward-compatible route.
- `kiasumiles/static/kiasumiles/product-demo-60s.mp4`: keep its existing backward-compatible route, but do not reference it from the landing page.
- `tests/test_public_onboarding_copy.py`: preserve the exact setup-prompt contract.
- `README.md:39-43`: preserve the setup instruction byte-for-byte.
- `kiasumiles/tools.py`, `kiasumiles/agent_contract.py`, `kiasumiles/engine/`, and `kiasumiles/data/`: no recommendation-path changes.

## Task 1: Add the proof-asset and favicon route contract

**Files:**

- Modify: `tests/test_hosted.py`
- Modify: `kiasumiles/hosted.py`
- Create: `kiasumiles/static/kiasumiles/favicon.svg`
- Create: the nine files under `kiasumiles/static/kiasumiles/assets/proof/` listed above

- [ ] **Step 1: Write the failing route tests**

Add `import pytest` to `tests/test_hosted.py`, then add this exact route contract:

```python
PROOF_ASSETS = (
    ("kiasumiles-agent-chat-480.webp", "image/webp"),
    ("kiasumiles-agent-chat-960.webp", "image/webp"),
    ("kiasumiles-agent-chat-960.png", "image/png"),
    ("kiasumiles-in-use-wide-730.webp", "image/webp"),
    ("kiasumiles-in-use-wide-1460.webp", "image/webp"),
    ("kiasumiles-in-use-wide-1460.jpg", "image/jpeg"),
    ("kiasumiles-in-use-portrait-480.webp", "image/webp"),
    ("kiasumiles-in-use-portrait-960.webp", "image/webp"),
    ("kiasumiles-in-use-portrait-960.jpg", "image/jpeg"),
)


@pytest.mark.parametrize(("filename", "content_type"), PROOF_ASSETS)
def test_proof_assets_have_expected_mime_and_cache_headers(filename, content_type):
    with TestClient(hosted.app) as client:
        response = client.get(f"/kiasumiles/assets/proof/{filename}")

    assert response.status_code == 200
    assert response.headers["content-type"] == content_type
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"
    assert response.headers["etag"]


def test_proof_asset_route_rejects_unknown_and_traversal_paths():
    with TestClient(hosted.app) as client:
        missing = client.get("/kiasumiles/assets/proof/not-a-proof.webp")
        traversal = client.get("/kiasumiles/assets/proof/%2E%2E%2Fprivacy.html")

    assert missing.status_code == 404
    assert traversal.status_code == 404


def test_favicon_is_served_without_a_console_404():
    with TestClient(hosted.app) as client:
        response = client.get("/favicon.svg")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"
```

- [ ] **Step 2: Run the tests and confirm the red state**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider tests/test_hosted.py -q
```

Expected: the new proof and favicon tests fail with `404`; existing hosted tests still pass.

- [ ] **Step 3: Capture a fresh genuine hero conversation**

Use a clean demo profile in an MCP-capable agent connected to the production KiasuMiles MCP. Configure only these public product names:

```text
UOB Preferred Visa
Citi Rewards Mastercard
```

Ask exactly:

```text
I'm at NTUC FairPrice and paying with Apple Pay. Which card should I use?
```

Allow the agent to call KiasuMiles and compose its own answer. The visible answer must include the real recommendation, `4 mpd`, the `cap_summary`, and the mobile-contactless payment instruction. It must not show an MCC, internal card identifier, debug output, full private wallet, setup transcript, unrelated chat, contact name, notification, or the stale product name `UOB Preferred Platinum Visa`.

Do not retouch the conversation text. If the real agent emits forbidden content, fix the public display contract and rerun the conversation before capturing it.

Hide unrelated app chrome and capture only the user question plus final answer:

```bash
screencapture -i -o /private/tmp/kiasumiles-agent-chat-source.png
```

- [ ] **Step 4: Export metadata-free responsive hero assets**

Run:

```bash
mkdir -p kiasumiles/static/kiasumiles/assets/proof
```

```bash
magick /private/tmp/kiasumiles-agent-chat-source.png -strip -colorspace sRGB -resize '960x1200^' -gravity center -extent 960x1200 -quality 88 kiasumiles/static/kiasumiles/assets/proof/kiasumiles-agent-chat-960.webp
```

```bash
magick /private/tmp/kiasumiles-agent-chat-source.png -strip -colorspace sRGB -resize '480x600^' -gravity center -extent 480x600 -quality 88 kiasumiles/static/kiasumiles/assets/proof/kiasumiles-agent-chat-480.webp
```

```bash
magick /private/tmp/kiasumiles-agent-chat-source.png -strip -colorspace sRGB -resize '960x1200^' -gravity center -extent 960x1200 -define png:compression-level=9 kiasumiles/static/kiasumiles/assets/proof/kiasumiles-agent-chat-960.png
```

- [ ] **Step 5: Permanently mask the supplied real-life photo before export**

Never copy the original photograph into the public static directory. Apply a strong, polygon-masked blur over the complete phone display on the source-resolution image before cropping. This tested polygon deliberately extends beyond the display edges so no readable sliver survives while the hand and restaurant context remain visible:

```bash
magick interview-codex-thread-screenshots/08-wife-using-kiasumiles-in-real-life.jpg -auto-orient -colorspace sRGB -write mpr:original -blur 0x44 \( -size 1460x2594 xc:black -fill white -draw 'polygon 500,520 1440,710 1040,2080 0,1710' \) -alpha off -compose CopyOpacity -composite mpr:original +swap -compose Over -composite -strip /private/tmp/kiasumiles-in-use-masked.png
```

Create the desktop master and derivatives:

```bash
magick /private/tmp/kiasumiles-in-use-masked.png -crop 1460x912+0+620 +repage -strip -quality 84 kiasumiles/static/kiasumiles/assets/proof/kiasumiles-in-use-wide-1460.jpg
```

```bash
magick kiasumiles/static/kiasumiles/assets/proof/kiasumiles-in-use-wide-1460.jpg -strip -quality 82 kiasumiles/static/kiasumiles/assets/proof/kiasumiles-in-use-wide-1460.webp
```

```bash
magick kiasumiles/static/kiasumiles/assets/proof/kiasumiles-in-use-wide-1460.jpg -resize 730x456 -strip -quality 82 kiasumiles/static/kiasumiles/assets/proof/kiasumiles-in-use-wide-730.webp
```

Create the mobile master and derivatives:

```bash
magick /private/tmp/kiasumiles-in-use-masked.png -crop 1168x1460+146+560 +repage -resize 960x1200 -strip -quality 84 kiasumiles/static/kiasumiles/assets/proof/kiasumiles-in-use-portrait-960.jpg
```

```bash
magick kiasumiles/static/kiasumiles/assets/proof/kiasumiles-in-use-portrait-960.jpg -strip -quality 82 kiasumiles/static/kiasumiles/assets/proof/kiasumiles-in-use-portrait-960.webp
```

```bash
magick kiasumiles/static/kiasumiles/assets/proof/kiasumiles-in-use-portrait-960.jpg -resize 480x600 -strip -quality 82 kiasumiles/static/kiasumiles/assets/proof/kiasumiles-in-use-portrait-480.webp
```

- [ ] **Step 6: Create the favicon**

Create `kiasumiles/static/kiasumiles/favicon.svg` with this complete source:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="KiasuMiles">
  <rect width="64" height="64" rx="14" fill="#073d35"/>
  <path d="M18 16v32h8V36l14 12h11L33 32l17-16H39L26 29V16z" fill="#d9ff68"/>
</svg>
```

- [ ] **Step 7: Add exact-name immutable routes**

In `kiasumiles/hosted.py`, add these constants after `STATIC_DIR`:

```python
PROOF_DIR = STATIC_DIR / "assets" / "proof"
FAVICON_PATH = STATIC_DIR / "favicon.svg"
HTML_CACHE_HEADERS = {"Cache-Control": "public, max-age=0, must-revalidate"}
IMMUTABLE_CACHE_HEADERS = {"Cache-Control": "public, max-age=31536000, immutable"}
PROOF_ASSETS = {
    "kiasumiles-agent-chat-480.webp": "image/webp",
    "kiasumiles-agent-chat-960.webp": "image/webp",
    "kiasumiles-agent-chat-960.png": "image/png",
    "kiasumiles-in-use-wide-730.webp": "image/webp",
    "kiasumiles-in-use-wide-1460.webp": "image/webp",
    "kiasumiles-in-use-wide-1460.jpg": "image/jpeg",
    "kiasumiles-in-use-portrait-480.webp": "image/webp",
    "kiasumiles-in-use-portrait-960.webp": "image/webp",
    "kiasumiles-in-use-portrait-960.jpg": "image/jpeg",
}
```

Add these routes after `logo_asset()`:

```python
@mcp.custom_route("/kiasumiles/assets/proof/{filename:path}", methods=["GET"])
async def proof_asset(request: Request):
    filename = request.path_params["filename"]
    media_type = PROOF_ASSETS.get(filename)
    if media_type is None:
        return PlainTextResponse("Not found", status_code=404)

    path = (PROOF_DIR / filename).resolve()
    if not path.is_file() or PROOF_DIR.resolve() not in path.parents:
        return PlainTextResponse("Not found", status_code=404)

    return FileResponse(
        path,
        media_type=media_type,
        headers=IMMUTABLE_CACHE_HEADERS,
    )


@mcp.custom_route("/favicon.svg", methods=["GET"])
async def favicon(_: Request) -> FileResponse:
    return FileResponse(
        FAVICON_PATH,
        media_type="image/svg+xml",
        headers=IMMUTABLE_CACHE_HEADERS,
    )
```

- [ ] **Step 8: Verify the green state and inspect every asset directly**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider tests/test_hosted.py -q
```

Expected: all hosted tests pass.

Run OCR over the hero fallback and both real-life fallbacks:

```bash
tesseract kiasumiles/static/kiasumiles/assets/proof/kiasumiles-agent-chat-960.png stdout 2>/dev/null | rg -n -i 'MCC|5812|card_id|uob_ppv|Preferred Platinum|Cap within limit'
```

```bash
tesseract kiasumiles/static/kiasumiles/assets/proof/kiasumiles-in-use-wide-1460.jpg stdout 2>/dev/null | rg -n -i 'MCC|5812|card_id|uob_ppv|Preferred Platinum|Cap within limit'
```

```bash
tesseract kiasumiles/static/kiasumiles/assets/proof/kiasumiles-in-use-portrait-960.jpg stdout 2>/dev/null | rg -n -i 'MCC|5812|card_id|uob_ppv|Preferred Platinum|Cap within limit'
```

Expected: all three commands return no matches. Open each public derivative at 100% and 200% zoom and confirm the phone screen mask fully covers every message and contact field.

Check metadata:

```bash
identify -verbose kiasumiles/static/kiasumiles/assets/proof/* | rg -n -i 'Profile-|exif:|xmp:|GPS|DELL|Display P3'
```

Expected: no sensitive metadata or device profile names.

- [ ] **Step 9: Commit the proof infrastructure**

```bash
git add kiasumiles/hosted.py tests/test_hosted.py kiasumiles/static/kiasumiles/favicon.svg kiasumiles/static/kiasumiles/assets/proof
git commit -m "Add privacy-safe landing proof assets"
```

## Task 2: Move the privacy policy into a polished static document

**Files:**

- Modify: `tests/test_hosted.py`
- Modify: `kiasumiles/hosted.py`
- Create: `kiasumiles/static/kiasumiles/privacy.html`

- [ ] **Step 1: Write the failing privacy contract**

Add this test to `tests/test_hosted.py`:

```python
def test_privacy_policy_is_public_request_scoped_and_nontechnical():
    with TestClient(hosted.app) as client:
        response = client.get("/privacy")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.headers["cache-control"] == "public, max-age=0, must-revalidate"
    assert "KiasuMiles does not store your selected card stack" in response.text
    assert "for that request" in response.text
    assert 'href="/"' in response.text
    assert 'href="mailto:hello@theaiburrow.xyz"' in response.text
    assert "card IDs" not in response.text
    assert "MCC" not in response.text
```

- [ ] **Step 2: Run the test and confirm it fails**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider tests/test_hosted.py::test_privacy_policy_is_public_request_scoped_and_nontechnical -q
```

Expected: fail because the current inline policy contains technical identifier language and no HTML cache header.

- [ ] **Step 3: Create the static privacy document**

Create `kiasumiles/static/kiasumiles/privacy.html` with these exact content requirements:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="How KiasuMiles handles card selections and recommendation requests.">
  <title>Privacy | KiasuMiles</title>
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <style>
    :root { color-scheme: light; --ink:#0a211e; --muted:#526661; --paper:#f4f8f2; --green:#073d35; --acid:#d9ff68; }
    * { box-sizing: border-box; }
    body { margin:0; color:var(--ink); background:var(--paper); font:17px/1.65 ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    main { width:min(760px,calc(100% - 40px)); margin:0 auto; padding:64px 0 88px; }
    a { color:var(--green); text-underline-offset:3px; }
    .back { display:inline-flex; min-height:44px; align-items:center; font-weight:750; }
    h1 { max-width:12ch; margin:56px 0 12px; font-size:clamp(44px,8vw,72px); line-height:.94; letter-spacing:-.045em; }
    h2 { margin:42px 0 8px; font-size:24px; letter-spacing:-.025em; }
    p, li { max-width:68ch; }
    .date { color:var(--muted); }
    .note { margin-top:48px; padding:20px; border:1px solid #bed0ca; border-radius:16px; background:#fff; }
    :focus-visible { outline:3px solid var(--acid); outline-offset:3px; }
  </style>
</head>
<body>
  <main>
    <a class="back" href="/">Back to KiasuMiles</a>
    <h1>Privacy, in plain English.</h1>
    <p class="date">Last updated: 13 July 2026</p>
    <p>KiasuMiles provides Singapore credit-card miles recommendations through a hosted service used by your agent or local client.</p>
    <h2>Your selected cards</h2>
    <p>KiasuMiles does not store your selected card stack. Your agent or local client holds the card products you choose under its own data controls and supplies them to KiasuMiles for that request.</p>
    <h2>What a recommendation request contains</h2>
    <p>A request may include the merchant name, how you plan to pay, and the card products your agent should compare. KiasuMiles uses that information to calculate and return the recommendation.</p>
    <h2>Operational logs</h2>
    <p>Limited operational logs may be used to keep the service reliable and investigate errors. Do not send card numbers, account details, passwords, or other sensitive personal information to KiasuMiles.</p>
    <h2>Rules and data updates</h2>
    <p>Card rules and merchant data are maintained centrally so they can be refreshed without asking users to reinstall the service.</p>
    <div class="note">
      <strong>Questions or corrections?</strong>
      <p>Email <a href="mailto:hello@theaiburrow.xyz">hello@theaiburrow.xyz</a>.</p>
    </div>
  </main>
</body>
</html>
```

- [ ] **Step 4: Make the FastMCP adapter read the static policy**

Replace the inline `privacy()` response in `kiasumiles/hosted.py` with:

```python
@mcp.custom_route("/privacy", methods=["GET"])
async def privacy(_: Request) -> HTMLResponse:
    return HTMLResponse(
        (STATIC_DIR / "privacy.html").read_text(encoding="utf-8"),
        headers=HTML_CACHE_HEADERS,
    )
```

Also update `landing()` so the HTML uses the same revalidation policy:

```python
@mcp.custom_route("/", methods=["GET"])
async def landing(_: Request) -> HTMLResponse:
    return HTMLResponse(
        (STATIC_DIR / "index.html").read_text(encoding="utf-8"),
        headers=HTML_CACHE_HEADERS,
    )
```

- [ ] **Step 5: Run the focused and hosted tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider tests/test_hosted.py -q
```

Expected: all hosted tests pass.

- [ ] **Step 6: Commit the policy change**

```bash
git add kiasumiles/hosted.py kiasumiles/static/kiasumiles/privacy.html tests/test_hosted.py
git commit -m "Polish the public privacy policy"
```

## Task 3: Replace the landing page with the approved agent-first story

**Files:**

- Create: `tests/test_landing_page.py`
- Modify: `tests/test_hosted.py`
- Modify: `kiasumiles/static/kiasumiles/index.html`

- [ ] **Step 1: Write source-level landing-page regression tests**

Create `tests/test_landing_page.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LANDING = ROOT / "kiasumiles" / "static" / "kiasumiles" / "index.html"


def landing_html() -> str:
    return LANDING.read_text(encoding="utf-8")


def test_landing_page_uses_the_approved_agent_story():
    html = landing_html()

    assert "Ask your agent before you pay." in html
    assert "Set up the card products you carry once." in html
    assert "KiasuMiles does not store your card stack." in html
    assert "Agent-side card stack" in html
    assert "Request-scoped lookup" in html
    assert "Actionable answer" in html
    assert "Used where the decision happens." in html
    assert "Set up once" in html
    assert "Ask normally" in html
    assert "Get one usable answer" in html


def test_landing_page_has_setup_trust_and_feedback_links():
    html = landing_html()

    assert 'href="#how-it-works"' in html
    assert 'href="#setup"' in html
    assert 'href="#privacy"' in html
    assert 'href="/privacy"' in html
    assert 'href="/health"' in html
    assert 'href="https://github.com/hosanxiv/kiasumiles#readme"' in html
    assert 'href="https://t.me/kiasumilesbot"' in html


def test_setup_control_has_accessible_success_and_failure_feedback():
    html = landing_html()

    assert 'aria-label="Copy KiasuMiles setup prompt"' in html
    assert 'role="status"' in html
    assert 'aria-live="polite"' in html
    assert "KiasuMiles setup prompt copied." in html
    assert "Copy failed. Select the prompt and copy it manually." in html
    assert "navigator.clipboard.writeText" in html
    assert "textContent" in html


def test_landing_page_uses_responsive_external_proof_assets():
    html = landing_html()

    for filename in (
        "kiasumiles-agent-chat-480.webp",
        "kiasumiles-agent-chat-960.webp",
        "kiasumiles-agent-chat-960.png",
        "kiasumiles-in-use-wide-730.webp",
        "kiasumiles-in-use-wide-1460.webp",
        "kiasumiles-in-use-wide-1460.jpg",
        "kiasumiles-in-use-portrait-480.webp",
        "kiasumiles-in-use-portrait-960.webp",
        "kiasumiles-in-use-portrait-960.jpg",
    ):
        assert f"/kiasumiles/assets/proof/{filename}" in html

    assert 'fetchpriority="high"' in html
    assert 'loading="lazy"' in html
    assert 'width="960" height="1200"' in html
    assert 'width="1460" height="912"' in html


def test_proof_assets_stay_within_mobile_friendly_byte_budgets():
    proof_dir = LANDING.parent / "assets" / "proof"
    budgets = {
        "kiasumiles-agent-chat-480.webp": 75_000,
        "kiasumiles-agent-chat-960.webp": 160_000,
        "kiasumiles-agent-chat-960.png": 300_000,
        "kiasumiles-in-use-wide-730.webp": 70_000,
        "kiasumiles-in-use-wide-1460.webp": 160_000,
        "kiasumiles-in-use-wide-1460.jpg": 240_000,
        "kiasumiles-in-use-portrait-480.webp": 55_000,
        "kiasumiles-in-use-portrait-960.webp": 120_000,
        "kiasumiles-in-use-portrait-960.jpg": 180_000,
    }

    for filename, limit in budgets.items():
        assert (proof_dir / filename).stat().st_size <= limit


def test_landing_page_is_light_and_contains_no_stale_or_technical_claims():
    html = landing_html()

    assert LANDING.stat().st_size < 100_000
    for forbidden in (
        "data:image",
        ".mp4",
        "MCC",
        "card_id",
        "UOB Preferred Platinum Visa",
        "Cap within limit",
        "Wallet stays client-side",
    ):
        assert forbidden not in html
```

- [ ] **Step 2: Replace obsolete hosted-page assertions with legacy-media coverage**

Replace `test_landing_page_and_media_routes_are_served()` in `tests/test_hosted.py` with:

```python
def test_landing_page_and_legacy_media_routes_remain_available():
    with TestClient(hosted.app) as client:
        landing = client.get("/")
        hero = client.get("/kiasumiles/hero.png")
        video = client.get("/kiasumiles/product-demo-60s.mp4")
        logo = client.get("/assets/logos/grab-colour.svg")
        namespaced_logo = client.get("/kiasumiles/assets/logos/grab-colour.svg")
        blocked = client.get("/assets/logos/../secret.txt")

    assert landing.status_code == 200
    assert landing.headers["cache-control"] == "public, max-age=0, must-revalidate"
    assert "Ask your agent before you pay." in landing.text
    assert "Install KiasuMiles MCP for me" in landing.text
    assert "https://kiasumiles.space/mcp" in landing.text
    assert hero.status_code == 200
    assert hero.headers["content-type"] == "image/png"
    assert video.status_code == 200
    assert video.headers["content-type"] == "video/mp4"
    assert logo.status_code == 200
    assert logo.headers["content-type"] == "image/svg+xml"
    assert namespaced_logo.status_code == 200
    assert namespaced_logo.headers["content-type"] == "image/svg+xml"
    assert blocked.status_code == 404
```

- [ ] **Step 3: Run the new tests and confirm the red state**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider tests/test_landing_page.py tests/test_public_onboarding_copy.py tests/test_hosted.py -q
```

Expected: the landing tests fail against the old headline, missing proof assets, missing links, inaccessible clipboard feedback, stale product copy, and 539 KB HTML.

- [ ] **Step 4: Replace the complete page with the approved semantic structure**

Keep the existing Google Fonts request for Archivo, Geist, and Geist Mono with `display=swap`. Use this exact metadata before the stylesheet:

```html
<meta name="description" content="Ask your agent which Singapore miles card to use before you pay. KiasuMiles checks current rules against the cards you carry.">
<meta name="theme-color" content="#071c1a">
<link rel="canonical" href="https://kiasumiles.space/">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:title" content="KiasuMiles | Ask your agent before you pay">
<meta property="og:description" content="Rules-based Singapore miles recommendations through the agent you already use.">
<meta property="og:url" content="https://kiasumiles.space/">
<meta property="og:image" content="https://kiasumiles.space/kiasumiles/assets/proof/kiasumiles-agent-chat-960.png">
<meta name="twitter:card" content="summary_large_image">
<title>KiasuMiles | Ask your agent before you pay</title>
```

Add the exact setup prompt and this exact body structure:

```html
<a class="skip-link" href="#main-content">Skip to content</a>
<header class="site-header">
  <nav class="nav shell" aria-label="Primary navigation">
    <a class="brand" href="#top" aria-label="KiasuMiles home"><span class="brand-mark" aria-hidden="true">KM</span><span>KiasuMiles</span></a>
    <div class="nav-links">
      <a href="#how-it-works">How it works</a>
      <a href="#privacy">Privacy</a>
    </div>
    <a class="button button-small" href="#setup">Set up KiasuMiles</a>
  </nav>
</header>
<main id="main-content">
  <section class="hero" id="top" aria-labelledby="hero-title">
    <div class="shell hero-grid">
      <div class="hero-copy">
        <p class="eyebrow">KiasuMiles for your agent</p>
        <h1 id="hero-title">Ask your agent before you pay.</h1>
        <p class="lede">Set up the card products you carry once. When you ask at checkout, your agent sends those cards to KiasuMiles for a rules-based recommendation.</p>
        <div class="hero-actions">
          <a class="button" href="#setup">Copy setup prompt</a>
          <a class="text-link" href="https://github.com/hosanxiv/kiasumiles#readme">View the full setup guide</a>
        </div>
        <p class="trust-line"><span aria-hidden="true">●</span>KiasuMiles does not store your card stack.</p>
      </div>
      <figure class="hero-proof">
        <picture>
          <source type="image/webp" srcset="/kiasumiles/assets/proof/kiasumiles-agent-chat-480.webp 480w, /kiasumiles/assets/proof/kiasumiles-agent-chat-960.webp 960w" sizes="(max-width: 760px) calc(100vw - 40px), 480px">
          <img src="/kiasumiles/assets/proof/kiasumiles-agent-chat-960.png" width="960" height="1200" fetchpriority="high" decoding="async" alt="Agent conversation recommending UOB Preferred Visa for an Apple Pay purchase at NTUC FairPrice.">
        </picture>
        <figcaption>Real KiasuMiles recommendation using a demo card stack.</figcaption>
      </figure>
    </div>
  </section>
  <section class="boundary" aria-labelledby="boundary-title">
    <div class="shell">
      <p class="eyebrow">What lives where</p>
      <h2 id="boundary-title">Your agent knows your cards. KiasuMiles checks the rules.</h2>
      <div class="boundary-grid">
        <article><span>01</span><h3>Agent-side card stack</h3><p>Your agent or local client holds the card products you selected under its own data controls.</p></article>
        <article><span>02</span><h3>Request-scoped lookup</h3><p>KiasuMiles ranks only the cards supplied for the question you are asking now.</p></article>
        <article><span>03</span><h3>Actionable answer</h3><p>Your agent gives you the card, payment method, cap summary, reason, and any caveats.</p></article>
      </div>
    </div>
  </section>
  <section class="real-proof" id="proof" aria-labelledby="proof-title">
    <div class="shell proof-grid">
      <div class="proof-copy">
        <p class="eyebrow">Real-life proof</p>
        <h2 id="proof-title">Used where the decision happens.</h2>
        <p>At the table, cashier, booking page, or ride checkout, the useful answer is the one you can act on immediately.</p>
        <p class="privacy-caption">The phone display is blurred in this photograph to protect private conversation details.</p>
      </div>
      <figure class="life-photo">
        <picture>
          <source media="(max-width: 640px)" type="image/webp" srcset="/kiasumiles/assets/proof/kiasumiles-in-use-portrait-480.webp 480w, /kiasumiles/assets/proof/kiasumiles-in-use-portrait-960.webp 960w" sizes="calc(100vw - 40px)">
          <source media="(max-width: 640px)" srcset="/kiasumiles/assets/proof/kiasumiles-in-use-portrait-960.jpg">
          <source type="image/webp" srcset="/kiasumiles/assets/proof/kiasumiles-in-use-wide-730.webp 730w, /kiasumiles/assets/proof/kiasumiles-in-use-wide-1460.webp 1460w" sizes="(max-width: 1100px) calc(100vw - 40px), 760px">
          <img src="/kiasumiles/assets/proof/kiasumiles-in-use-wide-1460.jpg" width="1460" height="912" loading="lazy" decoding="async" alt="A person checking KiasuMiles on a phone while seated at a restaurant; the display is blurred for privacy.">
        </picture>
      </figure>
    </div>
  </section>
  <section class="agent-loop" id="how-it-works" aria-labelledby="loop-title">
    <div class="shell">
      <p class="eyebrow">How it works</p>
      <h2 id="loop-title">One setup. One normal question. One usable answer.</h2>
      <ol class="loop-steps">
        <li><span>1</span><div><h3>Set up once</h3><p>Paste the setup instruction into your agent and choose card products by bank and name.</p></div></li>
        <li><span>2</span><div><h3>Ask normally</h3><p>Name the merchant and how you plan to pay, such as Apple Pay, physical contactless, or online.</p></div></li>
        <li><span>3</span><div><h3>Get one usable answer</h3><p>Receive the best supplied card with the payment method, cap summary, reason, and caveats.</p></div></li>
      </ol>
    </div>
  </section>
  <section class="setup" id="setup" aria-labelledby="setup-title">
    <div class="shell setup-grid">
      <div>
        <p class="eyebrow">Get started</p>
        <h2 id="setup-title">Give your agent one instruction.</h2>
        <p>Paste this once. Your agent will connect KiasuMiles and help you choose the card products you carry.</p>
        <a class="text-link" href="https://github.com/hosanxiv/kiasumiles#readme">Need manual MCP setup?</a>
      </div>
      <div class="prompt-card">
        <pre id="setup-prompt" tabindex="-1"><code>Install KiasuMiles MCP for me: https://kiasumiles.space/mcp

Use KiasuMiles. First help me set up my card stack. Ask me which banks I have cards with, show me the matching supported cards, then remember my selected cards for future KiasuMiles lookups.</code></pre>
        <div class="prompt-actions">
          <button class="button copy-button" type="button" aria-label="Copy KiasuMiles setup prompt" data-copy="Install KiasuMiles MCP for me: https://kiasumiles.space/mcp&#10;&#10;Use KiasuMiles. First help me set up my card stack. Ask me which banks I have cards with, show me the matching supported cards, then remember my selected cards for future KiasuMiles lookups.">Copy setup prompt</button>
          <p id="copy-status" class="copy-status" role="status" aria-live="polite"></p>
        </div>
      </div>
    </div>
  </section>
</main>
<footer class="footer" id="privacy">
  <div class="shell footer-grid">
    <div><a class="brand footer-brand" href="#top"><span class="brand-mark" aria-hidden="true">KM</span><span>KiasuMiles</span></a><p>Rules-based Singapore miles recommendations, through the agent you already use.</p></div>
    <nav aria-label="Footer navigation">
      <a href="/privacy">Privacy policy</a>
      <a href="https://github.com/hosanxiv/kiasumiles#readme">GitHub setup guide</a>
      <a href="https://t.me/kiasumilesbot">Report a wrong result</a>
      <a href="/health">Service status and data freshness</a>
    </nav>
  </div>
</footer>
```

- [ ] **Step 5: Apply the visual-system contract in the inline stylesheet**

Use these exact design constraints in the new stylesheet:

- Colors: `#071c1a` dark canvas, `#073d35` deep green, `#7ee2c8` mint, `#d9ff68` acid accent, `#f4f8f2` paper, `#0a211e` ink, and `#526661` muted text.
- Type: Archivo for headings, Geist for body copy, Geist Mono for the setup prompt. `h1` uses `clamp(3.25rem, 7vw, 6rem)`, line-height `.92`, and letter-spacing `-.045em`.
- Layout: `.shell` is `width:min(1180px, calc(100% - 40px))`; sections use content-driven padding `clamp(4.5rem, 8vw, 8rem) 0`; no section uses viewport-height sizing.
- Hero: `.hero-grid` uses `grid-template-columns:minmax(0,1.05fr) minmax(320px,.75fr)` and aligns items center. The proof is no wider than `480px` and sits against the dark hero without a decorative device frame.
- Navigation: sticky, rectangular, and no more than `64px` tall. On screens below `720px`, hide `.nav-links` while retaining the brand and setup action. Every target remains at least `44px` high.
- Radii: content panels and images use at most `16px`; only buttons and small tags may use `999px`.
- Borders and shadows: use a one-pixel border or a shadow no wider than `0 6px 0`; never combine a border with a wide blurred shadow.
- Boundary and steps: use top rules and numeric markers rather than floating feature cards. At `760px` and below, both become a one-column vertical sequence.
- Images: use `display:block`, `width:100%`, and `height:auto`; do not use CSS crop as a privacy control.
- Readability: paragraph measure stays between `45ch` and `70ch`; setup text uses `white-space:pre-wrap` and `overflow-wrap:anywhere`.
- Focus: every link and control gets `outline:3px solid #d9ff68` with `outline-offset:3px` on `:focus-visible`.
- Anchors: all anchored sections use `scroll-margin-top:96px`.
- Motion: only `.hero-copy` and `.hero-proof` may run one `rise-in` animation on initial load. Under `prefers-reduced-motion: reduce`, disable animation, transition, and smooth scrolling.
- Overflow: do not set `overflow-x:hidden` on the page or body; the QA check must expose real overflow.

- [ ] **Step 6: Add complete clipboard success and failure behavior**

Add this script immediately before `</body>`:

```html
<script>
  (function () {
    var button = document.querySelector('.copy-button');
    var prompt = document.getElementById('setup-prompt');
    var status = document.getElementById('copy-status');
    var resetTimer = 0;

    function selectPrompt() {
      prompt.focus();
      var selection = window.getSelection();
      var range = document.createRange();
      range.selectNodeContents(prompt);
      selection.removeAllRanges();
      selection.addRange(range);
    }

    button.addEventListener('click', async function () {
      window.clearTimeout(resetTimer);
      try {
        if (!navigator.clipboard || !navigator.clipboard.writeText) {
          throw new Error('Clipboard API unavailable');
        }
        await navigator.clipboard.writeText(button.getAttribute('data-copy'));
        button.textContent = 'Copied';
        status.textContent = 'KiasuMiles setup prompt copied.';
      } catch (error) {
        selectPrompt();
        button.textContent = 'Copy manually';
        status.textContent = 'Copy failed. Select the prompt and copy it manually.';
      }

      resetTimer = window.setTimeout(function () {
        button.textContent = 'Copy setup prompt';
      }, 2200);
    });
  }());
</script>
```

- [ ] **Step 7: Run targeted tests and confirm the green state**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider tests/test_landing_page.py tests/test_public_onboarding_copy.py tests/test_hosted.py -q
```

Expected: all tests pass.

Run:

```bash
wc -c kiasumiles/static/kiasumiles/index.html
```

Expected: fewer than `100000` bytes.

Run:

```bash
rg -n 'data:image|product-demo-60s|MCC|card_id|UOB Preferred Platinum Visa|Cap within limit|Wallet stays client-side' kiasumiles/static/kiasumiles/index.html
```

Expected: no output.

- [ ] **Step 8: Commit the landing-page replacement**

```bash
git add kiasumiles/static/kiasumiles/index.html tests/test_landing_page.py tests/test_hosted.py
git commit -m "Redesign the KiasuMiles landing page"
```

## Task 4: Verify interaction, responsiveness, accessibility, and privacy in a real browser

**Files:**

- Modify only if verification reveals a defect: `kiasumiles/static/kiasumiles/index.html`, `kiasumiles/static/kiasumiles/privacy.html`, `kiasumiles/hosted.py`, proof derivatives, and their tests

- [ ] **Step 1: Start the real hosted app**

Run:

```bash
KIASUMILES_PORT=8000 .venv/bin/kiasumiles-hosted
```

Expected: the FastMCP service listens at `http://127.0.0.1:8000` and serves `/`, `/privacy`, `/health`, `/mcp`, the proof assets, and the legacy media routes.

- [ ] **Step 2: Verify every required viewport**

Use browser automation to load `http://127.0.0.1:8000/` at `320`, `390`, `430`, `768`, `1024`, `1440`, and `1920` pixels wide. At every width verify:

- `document.documentElement.scrollWidth === window.innerWidth`
- no text, navigation, proof image, or setup prompt clips
- the hero action and real proof appear in the intended reading order
- all interactive targets are at least `44px` in both dimensions
- images retain their aspect ratio and do not cause layout shift
- no request for the MP4 occurs
- no console error or warning appears, including `/favicon.ico`

- [ ] **Step 3: Verify the clipboard flow with success and forced failure**

In a secure browser context, click `Copy setup prompt`, read the clipboard, and assert the value exactly matches `PUBLIC_SETUP_PROMPT` from `tests/test_public_onboarding_copy.py`.

Then override clipboard writing to reject, click again, and verify:

- the prompt text is selected
- focus moves to `#setup-prompt`
- the live region announces `Copy failed. Select the prompt and copy it manually.`
- the button label becomes `Copy manually` and then resets

- [ ] **Step 4: Verify keyboard and reduced-motion behavior**

Navigate the page using only `Tab`, `Shift+Tab`, `Enter`, and `Space`. Confirm the skip link becomes visible, focus order follows the DOM, every focus ring is visible, the setup button works, and the footer links are reachable.

Emulate `prefers-reduced-motion: reduce` and confirm the hero content is visible immediately with no animation or smooth scroll.

- [ ] **Step 5: Inspect public proof files outside the page crop**

Open each `/kiasumiles/assets/proof/` URL directly at 100% and 200% zoom. Confirm:

- no full private wallet is present
- no contact name or notification is present
- no raw MCC or internal identifier is present
- no stale UOB product name is present
- no hidden off-crop detail survives in the downloadable file
- the real-life phone display is fully blurred in both wide and portrait derivatives

- [ ] **Step 6: Fix any observed defect with a regression test first**

For copy, route, privacy, or performance defects, add the failing assertion to `tests/test_landing_page.py` or `tests/test_hosted.py`, run it to see the failure, make the smallest fix, and rerun the focused test.

For visual-only defects, save a before screenshot, make the smallest CSS or asset adjustment, and save an after screenshot at the same viewport for comparison.

- [ ] **Step 7: Commit verified polish fixes if any files changed**

```bash
git add kiasumiles/static/kiasumiles/index.html kiasumiles/static/kiasumiles/privacy.html kiasumiles/static/kiasumiles/assets/proof kiasumiles/hosted.py tests/test_landing_page.py tests/test_hosted.py
git commit -m "Polish responsive landing behavior"
```

If no file changed during browser verification, do not create an empty commit.

## Task 5: Run the complete regression and production smoke suite

**Files:**

- No planned source changes; any discovered defect follows Task 4, Step 6

- [ ] **Step 1: Run the complete test suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider
```

Expected: all tests pass; the baseline before redesign was `103 passed`.

- [ ] **Step 2: Verify source size and forbidden-copy checks again**

Run:

```bash
wc -c kiasumiles/static/kiasumiles/index.html
```

Expected: fewer than `100000` bytes.

Run:

```bash
rg -n 'data:image|product-demo-60s|MCC|card_id|UOB Preferred Platinum Visa|Cap within limit|Wallet stays client-side' kiasumiles/static/kiasumiles/index.html
```

Expected: no output.

- [ ] **Step 3: Verify route status, MIME, and cache behavior**

With the local server still running, run:

```bash
curl -sS -D - -o /dev/null http://127.0.0.1:8000/
```

Expected: `200`, `text/html`, and `Cache-Control: public, max-age=0, must-revalidate`.

```bash
curl -sS -D - -o /dev/null http://127.0.0.1:8000/kiasumiles/assets/proof/kiasumiles-agent-chat-960.webp
```

Expected: `200`, `image/webp`, an ETag, and immutable one-year caching.

```bash
curl -sS -D - -o /dev/null http://127.0.0.1:8000/kiasumiles/assets/proof/kiasumiles-in-use-wide-1460.jpg
```

Expected: `200`, `image/jpeg`, an ETag, and immutable one-year caching.

```bash
curl -sS -D - -o /dev/null http://127.0.0.1:8000/kiasumiles/product-demo-60s.mp4
```

Expected: `200` and `video/mp4`, confirming backward compatibility.

- [ ] **Step 4: Review the final diff and commit state**

Run:

```bash
git status --short
git diff --check
git log -5 --oneline
```

Expected: no staged or unstaged project changes remain. User-owned untracked interview and capture files remain untouched.

## Task 6: Publish and verify the redesigned production site

**Files:**

- Deployment only after Tasks 1 through 5 are green

- [ ] **Step 1: Push the implementation branch**

Run:

```bash
git push origin codex-hosted-mcp-launch
```

Expected: the remote branch advances to the fully verified redesign commit.

- [ ] **Step 2: Create and inspect a Vercel preview deployment**

The repository is already linked to the Vercel project in `.vercel/project.json`. Run:

```bash
npx vercel --yes
```

Expected: a successful preview deployment URL. Open that URL and rerun the desktop, mobile, clipboard, console, direct-asset, privacy, and no-MP4 checks from Task 4.

- [ ] **Step 3: Deploy the same verified source to production**

Run:

```bash
npx vercel --prod --yes
```

Expected: a successful production deployment associated with `kiasumiles.space`.

- [ ] **Step 4: Verify the live domain rather than trusting the deploy command**

Run:

```bash
curl -sS https://kiasumiles.space/ | rg -n 'Ask your agent before you pay.|KiasuMiles does not store your card stack.'
```

Expected: both approved strings appear.

Run:

```bash
curl -sS -D - -o /dev/null https://kiasumiles.space/kiasumiles/assets/proof/kiasumiles-agent-chat-960.webp
```

Expected: `200`, `image/webp`, and immutable caching.

Open the live site at `390px` and `1440px`, repeat the console and clipboard checks, and compare the result with the final local screenshots. Do not report completion until the deployed site matches the verified local build.
