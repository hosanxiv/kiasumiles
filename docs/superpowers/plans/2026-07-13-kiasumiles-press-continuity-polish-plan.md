# KiasuMiles Press-Continuity Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish the existing KiasuMiles landing page while preserving the palette, imagery, hero, and signature sections already photographed by the press.

**Architecture:** Keep the single static landing document served by the thin FastMCP adapter. Externalise existing merchant images, add exact-name routes for an unblurred real-life proof photograph and favicon, and update the existing visual set pieces in place with truthful request-scoped copy and accessible clipboard behaviour. Recommendation code remains untouched.

**Tech Stack:** Python 3.10+, FastMCP, Starlette, pytest, semantic HTML, inline CSS and JavaScript, ImageMagick, Chrome/Playwright, Vercel.

---

## File Structure

### Create

- `kiasumiles/static/kiasumiles/privacy.html`: nontechnical privacy policy in the existing light/green visual identity.
- `kiasumiles/static/kiasumiles/favicon.svg`: compact KM favicon.
- `kiasumiles/static/kiasumiles/assets/proof/kiasumiles-real-life-720.webp`: unblurred, metadata-stripped responsive photograph.
- `kiasumiles/static/kiasumiles/assets/proof/kiasumiles-real-life-1460.webp`: unblurred, metadata-stripped responsive photograph.
- `kiasumiles/static/kiasumiles/assets/proof/kiasumiles-real-life-1460.jpg`: JPEG fallback.
- `tests/test_landing_page.py`: source-level continuity, truth, accessibility, and performance contracts.

### Modify

- `kiasumiles/hosted.py`: cache headers, exact proof routes, favicon route, and static privacy rendering.
- `kiasumiles/static/kiasumiles/index.html`: continuity-preserving polish.
- `tests/test_hosted.py`: route, MIME, cache, privacy, and legacy-media coverage.
- `README.md`: replace only the stale claim that the landing page contains a 60-second demo; preserve the setup prompt.

### Preserve

- `kiasumiles/landing.py`
- `kiasumiles/static/kiasumiles/hero.png`
- `kiasumiles/static/kiasumiles/product-demo-60s.mp4`
- `tests/test_public_onboarding_copy.py`
- `kiasumiles/tools.py`, `kiasumiles/agent_contract.py`, `kiasumiles/engine/`, and `kiasumiles/data/`
- Existing merchant-logo files under `kiasumiles/static/kiasumiles/assets/logos/`

## Task 1: Add proof, favicon, privacy, and cache routes

**Files:**

- Modify: `tests/test_hosted.py`
- Modify: `kiasumiles/hosted.py`
- Create: `kiasumiles/static/kiasumiles/privacy.html`
- Create: `kiasumiles/static/kiasumiles/favicon.svg`
- Create: the three files under `kiasumiles/static/kiasumiles/assets/proof/`

- [ ] **Step 1: Write failing route tests**

Add tests that assert:

```python
PROOF_ASSETS = (
    ("kiasumiles-real-life-720.webp", "image/webp"),
    ("kiasumiles-real-life-1460.webp", "image/webp"),
    ("kiasumiles-real-life-1460.jpg", "image/jpeg"),
)
```

For each proof asset, request `/kiasumiles/assets/proof/{filename}` and require status `200`, the exact MIME type, an ETag, and `Cache-Control: public, max-age=31536000, immutable`. Add tests that unknown and encoded traversal filenames return `404`.

Add a favicon test for `/favicon.svg` with `image/svg+xml` and immutable caching.

Add landing and privacy cache tests requiring `Cache-Control: public, max-age=0, must-revalidate`. The privacy response must contain a return link, the feedback contact, request-scoped card wording, and no raw `card IDs` phrase.

- [ ] **Step 2: Run the tests and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider tests/test_hosted.py -q
```

Expected: the new proof, favicon, privacy-static, and cache assertions fail for missing behaviour.

- [ ] **Step 3: Export the unblurred photograph**

Use this source unchanged with respect to screen visibility:

```text
interview-codex-thread-screenshots/08-wife-using-kiasumiles-in-real-life.jpg
```

Create the proof directory, then use ImageMagick to auto-orient, strip metadata, convert to sRGB, and make a centered `4:5` crop that retains the hand and phone. Do not blur, pixelate, mask, retouch, or replace the phone display.

Export:

```text
kiasumiles-real-life-720.webp   720x900, WebP quality 82
kiasumiles-real-life-1460.webp  1168x1460, WebP quality 84
kiasumiles-real-life-1460.jpg   1168x1460, JPEG quality 86
```

Verify with `identify` that dimensions are correct and EXIF/XMP/GPS metadata is absent.

- [ ] **Step 4: Implement the narrow routes**

In `kiasumiles/hosted.py`, define an exact filename-to-MIME mapping for the three proof files. Add `/kiasumiles/assets/proof/{filename}` and return `404` for anything outside the mapping. Add `/favicon.svg`. Add immutable cache headers to versioned proof and favicon responses. Add revalidation headers to `/` and `/privacy`.

Move the inline privacy policy into `privacy.html`. Describe that the agent or local client supplies selected card products for each lookup and hosted KiasuMiles does not store the stack. Keep the contact address and return link.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider tests/test_hosted.py -q
```

Expected: all hosted tests pass.

- [ ] **Step 6: Commit**

```bash
git add tests/test_hosted.py kiasumiles/hosted.py kiasumiles/static/kiasumiles/privacy.html kiasumiles/static/kiasumiles/favicon.svg kiasumiles/static/kiasumiles/assets/proof
git commit -m "Add public proof and privacy assets"
```

## Task 2: Polish the existing landing page without rebranding it

**Files:**

- Create: `tests/test_landing_page.py`
- Modify: `kiasumiles/static/kiasumiles/index.html`
- Modify: `README.md`

- [ ] **Step 1: Write failing continuity and product-truth tests**

Read the landing HTML as text and add focused tests for these contracts:

```python
CURRENT_PALETTE = (
    "#061427",
    "#1168ff",
    "#2bd6ad",
    "#5fb43a",
    "#b7e76a",
    "#003f37",
)

MERCHANT_ASSETS = (
    "fairprice-real-crop.png",
    "grab-colour.svg",
    "watsons-crop.png",
    "shell-colour.svg",
    "shopee-real-crop.png",
    "Singapore_Airlines_Logo.svg",
)
```

Assert every palette value and merchant asset remains present. Assert the page retains `The right card, before you tap.`, the IDs `radar`, `answer`, `flow`, `privacy`, and `start`, and the signature headings `It recognises the merchant, not just the category.`, `Your cards. One answer.`, `Ask. Get an answer.`, and `Two steps. Then just ask.`

Assert the page includes `UOB Preferred Visa`, `Apple Pay`, `Example using a demo card stack`, the unblurred real-life proof asset, `/privacy`, `/health`, GitHub, feedback, the copy button accessible name, an `aria-live="polite"` region, and the exact clipboard-failure message.

Assert the HTML is below `100_000` bytes and contains none of:

```python
FORBIDDEN = (
    "data:image",
    "product-demo-60s",
    "MCC",
    "card_id",
    "UOB Preferred Platinum Visa",
    "Cap within limit",
    "Wallet stays client-side",
    "Screen blurred for privacy",
)
```

Keep the existing setup-prompt test unchanged and add an assertion that the README no longer promotes a 60-second landing-page demo.

- [ ] **Step 2: Run the tests and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider tests/test_landing_page.py tests/test_public_onboarding_copy.py tests/test_hosted.py -q
```

Expected: the new tests fail against embedded images, stale copy, missing proof, missing footer, and inaccessible clipboard fallback.

- [ ] **Step 3: Evolve the existing visual system in place**

Replace the base64-heavy document with semantic HTML and inline CSS while preserving the current visual identity and section sequence.

Required continuity details:

- Keep the palette constants in `CURRENT_PALETTE`; do not introduce the discarded dark canvas `#071c1a` or acid lime `#d9ff68` as dominant brand colors.
- Keep Archivo, Geist, and Geist Mono.
- Keep the existing hero headline and floating six-merchant composition using `/kiasumiles/assets/logos/{filename}` URLs.
- Keep the merchant radar, green recommendation ticket, dark phone conversation, privacy illustration, and two-step setup as recognisable set pieces.
- Keep the current light-blue and mint washes. Reduce oversized radii to at most 16 pixels on content panels and keep hero type at or below 96 pixels.
- Replace full-viewport minimum heights with content-driven spacing while retaining the current narrative pacing.
- Add a skip link, semantic `header`, `nav`, `main`, sections, figures, and footer.

Required product-truth details:

- The recommendation ticket is labelled `Example using a demo card stack`.
- Use `UOB Preferred Visa`, `4 mpd`, NTUC FairPrice, Apple Pay or Google Pay, and `S$600 per calendar month; earns in S$5 blocks`.
- The example chat asks `Which card should I use at NTUC FairPrice with Apple Pay?` and is labelled as an example.
- Replace blanket wallet copy with request-scoped wording: the agent or local client holds selected card products under its own controls, supplies them for the lookup, and hosted KiasuMiles does not store the stack.
- Add the unblurred real-life photograph after the agent example. Its alt text describes a person checking a KiasuMiles conversation on a phone at a restaurant and must not say blurred, private, current, or live.
- Keep the photo contextual; do not claim that the visible transcript is the current product response.

Required interaction details:

- Preserve the exact `data-copy` setup prompt and readable visible prompt.
- Use one button with `aria-label="Copy KiasuMiles setup prompt"`.
- On success, show `KiasuMiles setup prompt copied.` in a polite live region.
- On failure, focus and select the prompt, set the button to `Copy manually`, and show `Copy failed. Select the prompt and copy it manually.`.
- Clear competing reset timers and return the button to `Copy setup prompt`.
- Every touch target is at least 44 pixels; every link and control has visible `:focus-visible` styling.
- Respect reduced motion and never hide content pending JavaScript.

Required footer links:

```text
/privacy
https://github.com/hosanxiv/kiasumiles#readme
https://t.me/kiasumilesbot
/health
```

- [ ] **Step 4: Correct the README line only**

Replace the claim that the live page contains a 60-second demo with a truthful short description of the live landing page. Do not alter the canonical setup prompt.

- [ ] **Step 5: Run targeted tests and static checks**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider tests/test_landing_page.py tests/test_public_onboarding_copy.py tests/test_hosted.py -q
wc -c kiasumiles/static/kiasumiles/index.html
rg -n 'data:image|product-demo-60s|MCC|card_id|UOB Preferred Platinum Visa|Cap within limit|Wallet stays client-side|Screen blurred for privacy' kiasumiles/static/kiasumiles/index.html
```

Expected: tests pass, HTML is below 100 KB, and the forbidden scan prints no matches.

- [ ] **Step 6: Commit**

```bash
git add tests/test_landing_page.py kiasumiles/static/kiasumiles/index.html README.md
git commit -m "Polish the press-recognisable landing page"
```

## Task 3: Verify the real page across browsers and interaction states

**Files:**

- Modify only when a verified defect requires a regression fix: landing HTML, hosted routes, static assets, privacy HTML, and their tests

- [ ] **Step 1: Start the hosted app**

```bash
KIASUMILES_PORT=8000 .venv/bin/kiasumiles-hosted
```

- [ ] **Step 2: Verify all target widths**

Use a real browser at `320`, `390`, `430`, `768`, `1024`, `1440`, and `1920` pixels. At each width assert `document.documentElement.scrollWidth === window.innerWidth`, no navigation or text clips, images retain aspect ratio, and touch targets are at least 44 pixels. Confirm no MP4 request and no console errors.

- [ ] **Step 3: Verify interaction and accessibility states**

Verify clipboard success and forced failure, prompt selection, live-region feedback, button reset, skip-link visibility, keyboard focus order, reduced-motion behaviour, alt text, and direct opening of each proof asset.

- [ ] **Step 4: Compare visual continuity**

Capture 390-pixel and 1440-pixel screenshots. Compare them with the current site and confirm the palette, merchant-logo hero, radar, green ticket, dark chat, privacy diagram, and setup section remain recognisable. The page may be cleaner and shorter, but it must not resemble the discarded dark-green mockup.

- [ ] **Step 5: Fix defects test-first and commit only if needed**

For behavioural defects, add a failing regression test before the smallest fix. For a visual-only defect, save before and after screenshots at the same viewport. Run the targeted suite after every fix.

```bash
git add kiasumiles/static/kiasumiles/index.html kiasumiles/static/kiasumiles/privacy.html kiasumiles/static/kiasumiles/assets/proof kiasumiles/hosted.py tests/test_landing_page.py tests/test_hosted.py
git commit -m "Polish responsive landing behaviour"
```

Do not create an empty commit.

## Task 4: Run the full regression and production smoke suite

**Files:**

- No planned source changes; defects follow Task 3's test-first rule

- [ ] **Step 1: Run all tests**

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider
```

Expected: all tests pass; baseline before the polish was `103 passed`.

- [ ] **Step 2: Repeat static and route checks**

Verify the landing HTML remains below 100 KB, forbidden copy is absent, `/`, `/privacy`, `/favicon.svg`, all three proof assets, the existing merchant assets, `/health`, and the legacy video route return the expected status and MIME types.

- [ ] **Step 3: Review repository state**

```bash
git diff --check
git status --short
git log -8 --oneline
```

Expected: no tracked project changes remain and user-owned interview/capture files remain untouched.

- [ ] **Step 4: Create a Vercel preview and verify it**

Run `npx vercel --yes`, then repeat the 390-pixel and 1440-pixel screenshots, clipboard checks, direct asset checks, and console inspection against the preview URL.

- [ ] **Step 5: Publish the verified source and verify the live domain**

After the preview matches the verified local build, run `npx vercel --prod --yes`. Verify `https://kiasumiles.space/` contains `The right card, before you tap.`, `Example using a demo card stack`, and the unblurred real-life proof asset. Confirm the live page matches the local screenshots before reporting completion.

