# KiasuMiles OpenAI Case Study

## One-Line Summary

KiasuMiles turns a high-friction real-world decision - which Singapore miles card to use at checkout - into a hosted MCP service any agent can call, without storing the user's wallet on the server.

## Problem

Singapore miles optimizers often know the rules in theory but fail at the point of purchase. The same merchant can post under different MCCs, the user's specific card ownership matters, monthly caps matter, and the answer is needed in the few seconds before the tap.

Generic model knowledge is not enough because card rules drift, merchant MCCs are specific, and the cards a person actually carries are personal context the model does not have.

## Product Bet

The agent should not be the source of truth for card rules, and the server should not be the source of truth for the user's wallet. Instead:

- The hosted service owns what changes centrally: merchant MCC data, card earn rules, caps, and caveats.
- The client owns what is personal: the list of cards the user carries.
- Each lookup sends the merchant plus the card IDs in scope, and the service ranks only those cards and returns a short, checkout-ready answer.

This split keeps the rules current for everyone without asking users to reinstall, while the server never has to store or be trusted with a wallet.

## Architecture

KiasuMiles ships in two transports from one codebase:

- **Hosted** (`kiasumiles.hosted`): a Streamable HTTP MCP server at `https://kiasumiles.space/mcp`, deployed on Vercel, reading card and merchant data from a private Supabase project. It is stateless for wallet data - card IDs arrive with each request, are used once, and are dropped. It deliberately exposes no wallet configure or wallet read tools.
- **Local** (`kiasumiles.server`): a stdio MCP server that runs fully offline and can persist a wallet on the user's own machine for personal use.

The business logic is shared and transport-neutral:

- `kiasumiles.engine`: merchant matching, card ranking, caps and caveats,
- `kiasumiles.tools`: transport-neutral tool handlers,
- `kiasumiles.hosted` / `kiasumiles.server`: thin hosted-HTTP and local-stdio adapters,
- `kiasumiles.agent_contract`: shared tool descriptions and display rules for agents,
- `plugins/kiasumiles`: Codex plugin packaging and skill guidance.

Data backend selection is explicit (`auto`, `supabase`, or `csv`), and both `kiasumiles_data_version` and `/health` report which backend is live, so production can confirm it is reading from Supabase rather than demo data.

## Hosted Tool Surface

The hosted endpoint exposes a deliberately small set:

- `kiasumiles_lookup` - best card for a merchant, ranked from the card IDs supplied,
- `kiasumiles_list_cards` - supported cards and their stable card IDs,
- `kiasumiles_recommend_stack` - gaps in the supplied stack and what would fill them,
- `kiasumiles_data_version` - current card and merchant data version,
- `kiasumiles_agent_guide` - integration and display guidance for agents.

There is no `kiasumiles_configure` or `kiasumiles_get_wallet` on the hosted side. Wallet storage belongs in the client or in the caller's own system, not on someone else's server. Those two wallet tools exist only on the local server, where the data stays on the user's machine.

## Why This Is Codex-Friendly

Codex can inspect the repo, run the tests, understand the domain vocabulary in `CONTEXT.md`, and install the repo-scoped plugin through `.agents/plugins/marketplace.json`.

The plugin bundles both MCP config and a skill. That matters because MCP exposes capability, while the skill teaches agent behavior: when to call the tool, how to handle the user's card stack, and what not to show the user (card IDs, MCC codes, raw fields). The plugin points Codex at the local `kiasumiles-mcp` server, so a Codex worker can run the full wallet-aware flow offline.

## Why This Is ChatGPT-App-Ready

The business logic does not live inside any one transport adapter. A hosted ChatGPT Apps SDK adapter can import `kiasumiles.tools`, register the same tool descriptions from `kiasumiles.agent_contract`, and decide separately how ChatGPT-side user state should be handled - mirroring the same client-owns-the-wallet split the hosted MCP endpoint already uses.

That keeps the hosted MCP product, the local MCP product, and a future hosted ChatGPT app aligned without duplicating card-routing logic.

## What Changed In This Iteration

- Shipped the hosted Streamable HTTP MCP endpoint at `https://kiasumiles.space/mcp`, stateless for wallet data.
- Moved card and merchant data to a managed Supabase backend, with explicit `auto` / `supabase` / `csv` backend selection and backend reporting in `/health` and `kiasumiles_data_version`.
- Added per-IP rate limiting and `/health`, `/privacy`, and landing routes on the hosted app.
- Kept the local stdio server as the offline, wallet-storing mode, with `kiasumiles_configure` and `kiasumiles_get_wallet` scoped to local only.
- Added an agent contract module with reusable tool descriptions and display rules, and split reusable tool handlers from the transport adapters.
- Added a repo-scoped Codex plugin scaffold with MCP config and a KiasuMiles skill, plus `CONTEXT.md` and `AGENTS.md` so future agents share the same vocabulary and commands.

## Good Interview Thread

The interesting part is not just "I built an MCP server." It is the data-custody split: the server owns the rules that drift, the client owns the wallet that is personal, and neither has to trust the other with the wrong thing. MCP gives the model a reliable hosted capability, the local transport gives a fully offline fallback, and Codex plugin packaging gives the model durable operating instructions. The combination turns a fragile prompt into a repeatable product surface.

## Next Decisions

- Decide how a hosted ChatGPT app should handle user card state on the ChatGPT side.
- Decide whether the ChatGPT app needs UI, or whether tool-only is enough.
- Expand merchant coverage and re-verification cadence on the Supabase backend.
- Add CI and publish plugin installation instructions after the repo hygiene pass.
