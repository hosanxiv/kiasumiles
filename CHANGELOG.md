# Changelog

## 1.0.2 - 2026-07-10

- Restored the local `kiasumiles-mcp` entry point and persistent wallet tools
- Wallets are saved on the user's device and attached automatically to recommendations
- Local recommendations use the live hosted card and merchant data
- The hosted MCP and REST surfaces remain stateless and store no wallet data
- Updated the Codex plugin to launch the wallet-aware local MCP again

## 1.0.0 - 2026-06-11

First stable release.

- Hosted MCP endpoint at `https://kiasumiles.space/mcp` (Streamable HTTP, no wallet
  storage server-side)
- Landing page, privacy policy, and health routes on the hosted app
- Card and merchant data moved to a managed backend; the package now ships a small
  demo dataset for development and tests
- Per-IP rate limiting on the hosted endpoint
- Codex plugin and repo marketplace under `plugins/kiasumiles`
- Agent contract module with shared tool descriptions and display rules
- Slimmer install: landing page media no longer ships in the package

## 0.1.3 - 2026-05-25

- Smarter routing: channel-aware matching and earn-block rounding
- Cap summaries in recommendation output
- Merchant and card data fixes

## 0.1.2 - 2026-05-14

- Bug fixes and packaging cleanup

## 0.1.1 - 2026-05-11

- Feedback bot included in the distributed package

## 0.1.0 - 2026-05-11

- First release: local stdio MCP server, wallet storage, merchant lookup, card ranking
