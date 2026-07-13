# KiasuMiles Press-Continuity Website Polish

Date: 2026-07-13

Status: Approved correction to the earlier redesign direction

## Goal

Polish `kiasumiles.space` without visually rebranding it. The live page must remain clearly recognisable as the website already photographed during the press interview, while its copy, accessibility, performance, mobile behaviour, and product truth improve.

This specification supersedes the visual-replacement portions of `2026-07-13-kiasumiles-website-redesign-design.md`. Its product-truth and accessibility requirements remain applicable.

## Continuity Contract

Preserve these recognisable parts of the current build:

- The existing white, pale-blue, mint, green, and navy palette.
- The committed color tokens `#061427`, `#1168ff`, `#2bd6ad`, `#5fb43a`, `#b7e76a`, and `#003f37`.
- Archivo headings, Geist body copy, and Geist Mono technical copy.
- The headline `The right card, before you tap.`
- The floating merchant-logo hero and merchant-radar idea.
- The green recommendation-ticket section.
- The dark phone conversation section.
- The server-rules and request-scoped card-stack privacy illustration.
- The two-step setup section and exact public setup prompt.

The result should look like a refined release of the photographed site, not a new campaign or a dark-green replacement.

## Product Truth

- The website is marketing and setup, not a separate recommendation surface.
- Any recommendation shown on the page is explicitly an example using a demo card stack.
- Example questions include the payment method.
- Use the current public product name `UOB Preferred Visa`.
- Show the payment instruction and `cap_summary`; do not claim the user's remaining cap is known.
- Hosted KiasuMiles ranks only cards supplied for the current request and does not store the card stack.
- Do not expose raw MCC codes, internal card identifiers, debug fields, or private source names in page copy.
- Do not add web calls to the deterministic recommendation path.

## Imagery

Keep the current merchant imagery for NTUC FairPrice, Grab, Watsons, Shell, Shopee, and Singapore Airlines. Serve the existing files as external assets rather than embedded base64.

Add the supplied real-life photograph as contextual proof. Per the user's direct instruction, the phone display is not blurred. Export web-optimised derivatives from `interview-codex-thread-screenshots/08-wife-using-kiasumiles-in-real-life.jpg`, strip metadata, convert to sRGB, and use an intentional crop that keeps the hand and phone recognisable.

Do not label the photograph as a current recommendation transcript. The separate example-result UI carries current explanatory copy.

The current stale UOB card-art image is not reused. Preserve the green ticket composition using typography rather than obsolete card artwork.

## Page Evolution

Keep the current section rhythm and IDs where practical:

1. Sticky navigation and merchant-logo hero
2. Merchant radar
3. Green recommendation ticket
4. Agent conversation example
5. Real-life usage photograph
6. Request-scoped privacy explanation
7. Two-step setup
8. Compact footer with policy, GitHub, feedback, and status links

The video remains available at its legacy route but is not loaded or linked from the landing page.

## Copy Corrections

Remove or replace:

- `UOB Preferred Platinum Visa`
- `Cap within limit`
- `Wallet client-side`
- blanket claims that every agent stores cards locally
- merchant questions that omit payment method
- any implication that the website knows the visitor's cards

Keep the existing headline and most section titles when they remain truthful. Prefer small copy corrections over wholesale rewriting.

## Interaction and Accessibility

- Preserve the setup prompt byte-for-byte with the README contract.
- Give the copy control the accessible name `Copy KiasuMiles setup prompt`.
- Announce success and failure in an `aria-live` status region.
- If clipboard access fails, select the prompt and show `Copy failed. Select the prompt and copy it manually.`
- Add a skip link, semantic landmarks, visible keyboard focus, logical heading order, and 44-pixel touch targets.
- Meet WCAG AA contrast and keep mobile text at 14 pixels or larger.
- Respect `prefers-reduced-motion`.

## Performance and Routing

- Remove all `data:image` payloads from the landing HTML.
- Keep the landing HTML below 100 KB uncompressed.
- Add exact-name proof-asset routes with immutable caching.
- Keep existing logo, hero, and video routes working.
- Add a favicon route and HTML revalidation headers.
- Use explicit image dimensions and lazy-load the below-fold real-life photograph.

## Verification

- `.venv/bin/python -m pytest` passes.
- The page has no horizontal overflow at 320, 390, 430, 768, 1024, 1440, and 1920 pixels.
- Clipboard success and forced-failure paths work.
- Keyboard focus and reduced motion work.
- No video request occurs.
- No console errors occur.
- The page remains visually recognisable against the current production build and press screenshots.

