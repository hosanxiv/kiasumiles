# KiasuMiles Website Redesign Design

Date: 2026-07-13

Status: Approved direction, pending implementation plan

## Goal

Redesign `kiasumiles.space` into a shorter, more credible landing page for everyday Singapore credit-card users. The page must explain how KiasuMiles actually works, show a real agent conversation, make setup easy, and state the wallet boundary accurately.

The website remains a marketing and setup surface. It does not become a separate recommendation product.

## Audience and Primary Job

The primary visitor is a nontechnical Singapore cardholder who wants a quick answer before paying. The visitor may not know what MCP means.

The page has one primary job: move the visitor from understanding the checkout benefit to copying the setup instruction into an MCP-capable agent.

Secondary visitors, including developers and technically curious users, can reach the GitHub setup guide and hosted MCP details without making the main page read like documentation.

## Product Truth

The public story must match the real system:

1. The user sets up the card products they carry in an agent or local KiasuMiles client.
2. The user asks that agent which card to use at a merchant, ideally including the payment method.
3. The agent or local client sends the merchant and selected card stack to hosted KiasuMiles for that request.
4. KiasuMiles deterministically checks merchant and card rules.
5. The agent presents the card name, earn rate, `cap_summary`, reason, payment-method requirement, and user-visible caveats.

Hosted KiasuMiles does not store the card stack. The page must not claim that every agent stores data locally. The accurate wording is that the agent or local client holds the selected card products under its own data controls and supplies them for each lookup.

The page must not offer an on-page recommendation form. That would invent a second product surface and imply that the website knows which cards the visitor carries.

## Approved Narrative

The approved direction is "show the whole agent loop," using real proof instead of a staged product demo.

The page order is:

1. Hero with setup action and a fresh real agent-chat screenshot
2. Three-part product boundary summary
3. Real-life usage photograph
4. Compact explanation of the agent loop
5. Copyable setup instruction
6. Trust, privacy, feedback, GitHub, and policy footer

The existing 60-second video is removed from the landing-page journey. Its route remains available for backward compatibility, but the redesigned page does not link to or load it.

## Page Design

### Global Navigation

Use a compact sticky navigation bar with:

- KiasuMiles brand mark and name
- "How it works" anchor
- "Privacy" anchor
- Primary "Set up KiasuMiles" action

On small screens, keep the brand and primary action. Secondary navigation collapses. All interactive targets are at least 44 by 44 pixels.

Add a keyboard-visible skip link and `scroll-margin-top` to anchored sections.

### Hero

Use a two-column desktop composition and a single-column mobile composition.

Recommended headline:

> Ask your agent before you pay.

Supporting copy:

> Set up the card products you carry once. When you ask at checkout, your agent sends those cards to KiasuMiles for a rules-based recommendation.

Primary action: "Copy setup prompt"

Secondary text link: "View the full setup guide"

Trust line:

> KiasuMiles does not store your card stack.

The right side shows a fresh, genuine agent conversation. It must show:

- A natural merchant question that includes the payment method
- The current card name "UOB Preferred Visa"
- A concise answer with earn rate and `cap_summary`
- A clear payment instruction, such as Apple Pay or Google Pay when mobile contactless is required
- No raw MCC, card ID, debug field, or technical setup output

The current `07-kiasumiles-card-recommendation-chat.png` establishes the visual direction but is not shipped unchanged because it contains a raw MCC and the older UOB product name. Implementation will capture a fresh conversation using the current production data and public display rules.

### Product Boundary Summary

Immediately below the hero, show three concise statements:

1. **Agent-side card stack**: The agent or local client holds the selected card products.
2. **Request-scoped lookup**: KiasuMiles ranks only cards supplied for that request.
3. **Actionable answer**: The agent shows the card, payment method, cap, reason, and caveats.

This replaces the current ambiguous "Wallet stays client-side" wording.

### Real-Life Proof

Use `08-wife-using-kiasumiles-in-real-life.jpg` as a large secondary proof section. The photograph demonstrates the product at the moment of use rather than as a staged interface.

Crop the image to prioritize the phone and hand. Keep existing redactions outside the visible crop where possible. Export a web-optimized derivative and verify that no personal identity, contact name, raw MCC, or private data is legible at any responsive crop.

Recommended heading:

> Used where the decision happens.

Supporting copy explains that KiasuMiles is meant for the table, cashier, booking page, or ride checkout where the card decision is immediate.

### How the Agent Loop Works

Present one compact sequence, not a grid of feature cards:

1. **Set up once**: Paste the setup instruction into the agent and choose card products by bank and name.
2. **Ask normally**: Name the merchant and how the payment will be made.
3. **Get one usable answer**: Receive the best supplied card with the payment method, cap, reason, and caveats.

The sequence can use one connected line or directional layout. It must not imply that the hosted service stores the user's wallet.

### Setup Section

Keep the existing public setup instruction byte-for-byte aligned with the README because `tests/test_public_onboarding_copy.py` enforces that contract.

The setup action is a real button with the accessible name "Copy KiasuMiles setup prompt." After copying, announce success through an `aria-live` region.

If clipboard access fails, keep the prompt selectable and show a plain recovery message: "Copy failed. Select the prompt and copy it manually."

The section includes a direct link to the GitHub setup guide for visitors whose agents require manual MCP configuration.

### Footer

Include:

- GitHub setup guide
- Privacy policy at `/privacy`
- Feedback contact or Telegram feedback link already documented by the project
- Current data version or freshness link where it can be sourced without a fragile hard-coded number

Do not expose internal card IDs, MCCs, table names, or private data-source names.

## Visual System

Preserve the existing KiasuMiles identity while removing template-like treatments.

- Keep the dark navy, deep Kiasu green, mint, and acid-lime accent.
- Use saturated green and lime for one or two committed moments instead of gradients on every section.
- Keep Archivo for display and Geist for body copy.
- Keep display letter spacing between `-0.04em` and `-0.02em`.
- Keep hero type at or below 96 pixels and use balanced wrapping.
- Cap panel radii at 16 pixels. Pill buttons and tags may remain fully rounded.
- Do not pair a decorative one-pixel border with a shadow wider than 8 pixels.
- Replace most full-viewport sections with content-driven spacing.
- Keep body text between 45 and 75 characters per line.
- Use a compact reading width on wide screens.

The page should feel direct, local, and useful. It should not resemble a generic fintech dashboard, developer documentation, an editorial magazine, or an AI-generated card grid.

## Motion

Use motion only where it clarifies the page:

- A restrained first-load reveal may bring in the hero copy and proof image.
- Button and link feedback uses short ease-out transitions.
- No repeated fade-on-scroll treatment across every section.
- Content remains visible when scripts fail or browser tabs are backgrounded.
- `prefers-reduced-motion: reduce` removes nonessential movement.

## Technical Design

The shipped source remains `kiasumiles/static/kiasumiles/index.html`, served verbatim by the thin route in `kiasumiles/hosted.py`.

`kiasumiles/landing.py` is a legacy renderer and is not modified as part of this redesign.

Implementation will:

- Replace embedded base64 merchant and card images with external static assets
- Add optimized proof assets under `kiasumiles/static/kiasumiles/assets/proof/`
- Add narrowly scoped static routes for proof assets if the existing route set cannot serve them
- Keep recommendation logic, MCP tools, REST adapters, and deterministic engine code unchanged
- Keep the existing video file and route, but remove its landing-page reference
- Load the hero chat image with explicit dimensions and high priority
- Lazy-load the real-life photograph with explicit dimensions
- Use `textContent` and fixed strings for feedback, never interpolate untrusted HTML

No web request is added to the recommendation path.

## Responsive Behaviour

The page must work from 320-pixel phones through wide desktop windows.

- Hero columns stack with copy first and screenshot second.
- Hero text never exceeds the viewport or clips at 320, 390, 430, or 768 pixels.
- The real-life image uses an intentional responsive crop and never reveals excluded details.
- The product boundary summary and agent loop become a vertical sequence on mobile.
- The setup prompt wraps without horizontal scrolling.
- Navigation and all buttons maintain 44-pixel touch targets.

## Accessibility

- Meet WCAG AA contrast for body text, links, controls, and placeholders.
- Use semantic navigation, main, section, figure, and footer elements.
- Give both proof images specific alt text.
- Preserve logical heading order.
- Provide visible keyboard focus for every interactive element.
- Announce clipboard success and failure.
- Do not rely on color alone for status or meaning.
- Respect reduced motion.

## Copy and Trust Guardrails

The public page must not contain:

- Raw MCC codes
- Internal card IDs or raw technical response fields
- The stale "UOB Preferred Platinum Visa" product name
- "Cap within limit" or any claim that KiasuMiles knows the user's remaining cap
- A blanket claim that every wallet stays on the user's physical device
- A claim that the website itself recommends a card
- A claim that KiasuMiles stores or remembers the user's card stack

Use `cap_summary` when describing caps. Surface routing or low-confidence caveats whenever a real result is shown.

## Performance Targets

- Keep the HTML response below 100 KB uncompressed by removing embedded images.
- Serve proof images in modern, web-optimized formats with appropriate fallbacks.
- Keep the hero proof image small enough to support a mobile LCP target below 2.5 seconds on a typical 4G connection.
- Lazy-load below-fold imagery.
- Prevent layout shift with fixed image dimensions or aspect ratios.
- Avoid loading the unneeded 60-second video.

## Verification

Automated verification:

- Run `.venv/bin/python -m pytest`.
- Preserve `tests/test_public_onboarding_copy.py`.
- Add landing-page assertions for the new hero, privacy link, setup action, and proof asset routes.
- Add negative assertions for raw MCC copy, internal card IDs, stale UOB naming, "Cap within limit," and the old blanket wallet claim.
- Verify all public proof assets return the expected MIME types.

Browser verification:

- Test 320, 390, 430, 768, 1024, 1440, and 1920 pixel widths.
- Confirm no horizontal scrolling or clipped navigation.
- Complete the setup-prompt copy flow by mouse, touch emulation, and keyboard.
- Verify clipboard success and forced-failure recovery.
- Verify focus order, visible focus, skip link, reduced motion, and image alt text.
- Confirm no console errors or warnings.
- Inspect the final hero and real-life crops for private or technical information.
- Compare the local result with the deployed production page after release.

## Success Criteria

The redesign is successful when:

1. A first-time visitor can explain in one sentence that KiasuMiles works through their agent.
2. The first viewport contains a concrete setup action, an accurate privacy statement, and real product proof.
3. No on-page element implies that the website knows the visitor's cards.
4. The page shows genuine usage without exposing raw technical fields or stale card information.
5. The setup prompt works without requiring the visitor to understand MCP internals.
6. The page is materially shorter and lighter than the current six-section, 540 KB HTML response.
7. The current deterministic recommendation engine and hosted wallet contract remain unchanged.

## Out of Scope

- An interactive website recommendation form
- A new web wallet
- Browser storage of card selections
- Changes to ranking, merchant matching, or cap logic
- A new MCP tool or agent protocol
- Deleting the existing video route
- Redesigning the GitHub README beyond any copy synchronization required by the existing setup-prompt test
