# KiasuMiles

> *"Which card do I use again?"*

If you're in the miles game, you've asked this at least once - standing at the cashier,
not quite sure if this is the 4 mpd one or the 1.2 mpd one.

KiasuMiles solves this through MCP. Connect your AI agent to the hosted endpoint, pass the
cards in a user's stack with each request, and get the best Singapore miles card for the
merchant in front of you.

The server keeps card rules and merchant data current. It does not store user wallet data.
Clients send card IDs per request.

**Hosted MCP endpoint:** `https://kiasumiles.space/mcp`

---

## Why it's different

Most miles guides tell you *"use Card X for dining, Card Y for online shopping."* Useful
until your wallet has 6 cards and you're standing at the checkout trying to remember which
one applies here.

KiasuMiles ranks against **the user's current card stack**. A client passes the cards the
user carries, KiasuMiles filters out everything else, factors in monthly caps, and returns
the best usable option with caveats.

You ask. It answers. One card. No second-guessing.

---

## How it works

1. Connect an MCP-capable agent to `https://kiasumiles.space/mcp`
2. Ask the agent to list supported cards and keep the user's card IDs client-side
3. For each lookup, send the merchant plus the user's card IDs
4. KiasuMiles returns the best card, earn rate, cap summary, and caveats

The hosted service is stateless for wallet data. It stores card rules and merchant data
only.

---

## Private data backend

The hosted app can read card rules and merchant mappings from a private Supabase project
instead of bundled CSV files.

Set these environment variables in Vercel:

- `KIASUMILES_SUPABASE_URL`
- `KIASUMILES_SUPABASE_SERVICE_ROLE_KEY`
- `KIASUMILES_SUPABASE_CARDS_TABLE` (optional, default: `card_rules`)
- `KIASUMILES_SUPABASE_MERCHANTS_TABLE` (optional, default: `merchant_mcc`)
- `KIASUMILES_DATA_BACKEND` (optional: `auto`, `supabase`, or `csv`)

Behavior:

- `auto`: use Supabase when credentials are present, otherwise fall back to bundled CSV data
- `supabase`: require Supabase and fail loudly if it is unavailable
- `csv`: force bundled CSV data even if Supabase credentials exist

The starter table schema lives at [supabase/schema.sql](/Users/hs/Documents/Projects/KiasuMiles/supabase/schema.sql).

`kiasumiles_data_version` and `/health` include `data_backend` so you can confirm whether
production is reading from `supabase` or `bundled_csv`.

---

## Hosted MCP

Use the hosted MCP endpoint for agents that support Streamable HTTP MCP:

```text
https://kiasumiles.space/mcp
```

Hosted MCP tools:

| Tool | What it does |
|------|--------------|
| `kiasumiles_lookup` | Best card for a merchant from card IDs supplied with the request |
| `kiasumiles_list_cards` | See supported cards and stable card IDs |
| `kiasumiles_recommend_stack` | Find gaps in a user's current card stack |
| `kiasumiles_data_version` | Check current card and merchant data version |
| `kiasumiles_agent_guide` | See integration and display guidance for agents |

Hosted MCP deliberately does not expose `kiasumiles_configure` or `kiasumiles_get_wallet`.
Wallet storage belongs in the client or user's own system.

### Example hosted lookup shape

```json
{
  "merchant": "NTUC FairPrice",
  "cards": ["uob_ppv", "citi_rewards_mc"],
  "channel": "mobile_contactless"
}
```

Lookup responses include a short `reason_summary`, `reason_codes`, and `gotchas` so agents
can explain why a card wins and warn about traps like wrong payment channel,
partner-only bonuses, or minimum-spend requirements.

---

## Local MCP

The package can still run as a local stdio MCP server for offline use:

```bash
pip3 install kiasumiles-mcp && kiasumiles-setup
```

The local MCP server can save a wallet on the user's machine and run lookup without web
calls. This is separate from the hosted MCP endpoint.

Run a local MCP server directly:

```bash
kiasumiles-mcp
```

The setup script auto-configures Claude Desktop and Claude Code if installed.

### Supported agents

- **Claude Desktop**
- **Claude Code (CLI)**
- **Codex** - local MCP config can point at `kiasumiles-mcp`; this repo includes `AGENTS.md` guidance for Codex workers.
- **OpenClaw** 
- **Hermes** — after install, run `hermes mcp list` and `hermes mcp test kiasumiles` to verify. If KiasuMiles tools still don't appear after `/new`, restart the gateway with `hermes gateway restart`, then start a fresh chat.
- **Any MCP-capable agent with pip access or Streamable HTTP support**

### ChatGPT app path

KiasuMiles now has a hosted MCP boundary intended for ChatGPT Apps SDK work:

- hosted MCP endpoint: `https://kiasumiles.space/mcp`
- public landing page: `https://kiasumiles.space/`
- privacy route: `https://kiasumiles.space/privacy`
- health route: `https://kiasumiles.space/health`

The reusable tool handlers live in `kiasumiles.tools`, separate from the FastMCP adapters,
so hosted ChatGPT Apps SDK adapters and local MCP clients can share merchant matching and
card-ranking behavior without duplicating business logic.

### Codex plugin

This repo includes a local Codex plugin at `plugins/kiasumiles` and a repo marketplace at `.agents/plugins/marketplace.json`.

The plugin bundles:

- MCP config for `kiasumiles-mcp`
- a KiasuMiles skill for checkout-ready card recommendations
- display guidance so Codex avoids showing card IDs, MCC codes, and raw wallet paths

In Codex, add the repo marketplace and install **KiasuMiles**, then ask:

> *"Use KiasuMiles to set up my wallet."*

---

## Wallet model

Hosted MCP:

- The server does not store wallet data.
- The client stores or collects the user's card stack.
- Each recommendation request includes card IDs for that request.
- Hosted tools do not include wallet configure or wallet read operations.

Local MCP:

- The user's machine can store a local wallet.
- Local tools include `kiasumiles_configure` and `kiasumiles_get_wallet`.
- The query path stays offline.

---

## Daily use

At a merchant, in the car, at checkout, ask an MCP-connected agent:

- *"What card at NTUC FairPrice?"*
- *"Best card for Grab contactless?"*
- *"I'm at Shell. Which card?"*
- *"Booking flights on Singapore Airlines — which card?"*
- *"Which card at Shake Shack — paying online"*

KiasuMiles surfaces the best option from the supplied card stack with the earn rate and cap.
If Amaze is in the supplied stack, the combo math is already done.

---

## Tools

Hosted MCP:

| Tool | What it does |
|------|--------------|
| `kiasumiles_lookup` | Best card for a merchant from supplied card IDs |
| `kiasumiles_list_cards` | See supported cards |
| `kiasumiles_recommend_stack` | Find gaps in a user's current card stack and suggest useful additions |
| `kiasumiles_data_version` | Check bundled data version and counts |
| `kiasumiles_agent_guide` | See integration and display guidance for agents |

Local MCP also includes:

| Tool | What it does |
|------|--------------|
| `kiasumiles_configure` | Save a local card wallet |
| `kiasumiles_get_wallet` | See locally saved cards |

---

## Supported cards

50+ Singapore credit cards in the database, but recommendations are filtered to cards
supplied by the client or saved in the local wallet.

HSBC Revolution · UOB PPV · UOB Visa Signature · UOB PRVI Miles · UOB Lady's · KrisFlyer UOB · DBS Altitude · DBS yuu · DBS Woman's World · DBS Vantage · Citi Rewards · Citi PremierMiles · Citi Prestige · OCBC 90N · OCBC Rewards · OCBC VOYAGE · Maybank Horizon · Maybank World · Standard Chartered Journey · Standard Chartered Visa Infinite · BOC Elite Miles · Amex KrisFlyer · Amex KrisFlyer Ascend · Amex HighFlyer · Amaze combos · and more

> *"Show me all KiasuMiles cards"* — ask your agent for the full list.

---

## Data

Merchant MCC data is community-verified and updated regularly. Card earn rates and caps are sourced from publicly available bank T&Cs.

Confidence levels are included in results — if a merchant has limited data points, you'll know.

---

## Verify installation

Hosted MCP:

```bash
curl -i -X POST https://kiasumiles.space/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl-smoke","version":"0.1"}}}'
```

Local MCP:

> *"Check if you have access to KiasuMiles tools"*

Your agent will confirm it can see `kiasumiles_lookup` and the other tools.

---

## Feedback

If a card recommendation looks wrong (wrong card, stale earn rate, missing merchant), send the details to **[@kiasumilesbot](https://t.me/kiasumilesbot)** on Telegram. Include the merchant name and which card was suggested. Every report is reviewed.

---

## About

KiasuMiles is built by **[Hosan](https://theaiburrow.xyz)** — founder behind **[The AI Burrow](https://theaiburrow.xyz)**, Singapore's applied AI collective for teams and builders who want to move past the hype and actually deploy.

- 🌐 [theaiburrow.xyz](https://theaiburrow.xyz)
- 💬 Telegram community: [t.me/theaiburrow](https://t.me/theaiburrow)
- 📩 [hello@theaiburrow.xyz](mailto:hello@theaiburrow.xyz)

*MIT License*
