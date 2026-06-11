# KiasuMiles

> "Which card do I use again?"

If you're in the miles game, you've asked this at least once - standing at the cashier,
not quite sure if this is the 4 mpd card or the 1.2 mpd one.

KiasuMiles answers it over MCP. Point your agent at the hosted endpoint, send the cards
you actually carry with each request, and get back the card that earns the most at the
merchant in front of you.

Hosted MCP endpoint: `https://kiasumiles.space/mcp`

---

## Why this exists

Miles guides tell you "Card X for dining, Card Y for online shopping". That works until
your wallet has six cards and the merchant in front of you doesn't fit the chart.

KiasuMiles ranks against the cards you actually hold. The client passes your card IDs,
KiasuMiles filters out everything else, factors in monthly caps, and returns one usable
answer with the caveats attached. No second guessing at the counter.

The server keeps card rules and merchant data current. It never stores your wallet:
card IDs are sent with each request, used once, and dropped.

---

## How it works

1. Connect an MCP-capable agent to `https://kiasumiles.space/mcp`
2. Ask the agent to list supported cards, then keep your card IDs client-side
3. For each lookup, send the merchant name plus your card IDs
4. KiasuMiles returns the best card, earn rate, cap summary, and caveats

---

## Hosted MCP

For any agent that speaks Streamable HTTP MCP:

```text
https://kiasumiles.space/mcp
```

| Tool | What it does |
|------|--------------|
| `kiasumiles_lookup` | Best card for a merchant, ranked from the card IDs you supply |
| `kiasumiles_list_cards` | Supported cards and their stable card IDs |
| `kiasumiles_recommend_stack` | Gaps in your current stack and what would fill them |
| `kiasumiles_data_version` | Current card and merchant data version |
| `kiasumiles_agent_guide` | Integration and display guidance for agents |

The hosted server deliberately has no `kiasumiles_configure` or `kiasumiles_get_wallet`.
Wallet storage belongs in the client or in your own system, not on someone else's server.

Example lookup payload:

```json
{
  "merchant": "NTUC FairPrice",
  "cards": ["uob_ppv", "citi_rewards_mc"],
  "channel": "mobile_contactless"
}
```

Responses include `reason_summary`, `reason_codes`, and `gotchas`, so the agent can
explain why a card wins and warn about traps: wrong payment channel, partner-only
bonuses, minimum spend you haven't hit.

The endpoint is rate limited per IP (30 requests a minute by default). Normal agent
use never gets near it.

### Try it

```bash
curl -i -X POST https://kiasumiles.space/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl-smoke","version":"1.0"}}}'
```

---

## Local MCP

The package also runs as a local stdio MCP server, fully offline:

```bash
pip3 install kiasumiles-mcp && kiasumiles-setup
```

The local server can save a wallet on your machine and answer lookups without any web
calls. The setup script auto-configures Claude Desktop and Claude Code if it finds them.

Run the server directly:

```bash
kiasumiles-mcp
```

The package ships demo data only. If you keep a fuller card and merchant database in
private CSVs, point `KIASUMILES_DATA_DIR` at the folder that holds `card_rules.csv` and
`merchant_mcc.csv`.

Local-only tools on top of the hosted set:

| Tool | What it does |
|------|--------------|
| `kiasumiles_configure` | Save a local card wallet |
| `kiasumiles_get_wallet` | Show locally saved cards |

### Supported agents

- Claude Desktop
- Claude Code (CLI)
- Codex - local MCP config can point at `kiasumiles-mcp`; the repo includes `AGENTS.md` for Codex workers
- OpenClaw
- Hermes - after install, run `hermes mcp list` and `hermes mcp test kiasumiles` to verify. If tools still don't appear after `/new`, restart with `hermes gateway restart` and start a fresh chat
- Anything else with MCP support, via pip or the hosted endpoint

### Codex plugin

The repo carries a local Codex plugin at `plugins/kiasumiles` and a repo marketplace at
`.agents/plugins/marketplace.json`. The plugin bundles the MCP config, a skill for
checkout recommendations, and display guidance so Codex doesn't surface card IDs, MCC
codes, or wallet paths at the user.

In Codex, add the repo marketplace, install KiasuMiles, then ask:

> "Use KiasuMiles to set up my wallet."

---

## Wallet model

Hosted:

- The server stores no wallet data
- The client keeps the user's card stack and sends card IDs with each request
- No wallet configure or wallet read tools exist on the hosted side

Local:

- The wallet lives on your machine at `~/.kiasumiles/wallet.yaml`
- `kiasumiles_configure` and `kiasumiles_get_wallet` manage it
- The query path stays offline

---

## Data backends

The hosted app reads card rules and merchant mappings from a private Supabase project.
The public repo ships small demo CSVs for development and tests.

Environment variables (set in Vercel for hosted deployments):

- `KIASUMILES_SUPABASE_URL`
- `KIASUMILES_SUPABASE_SERVICE_ROLE_KEY`
- `KIASUMILES_SUPABASE_CARDS_TABLE` (optional, default `card_rules`)
- `KIASUMILES_SUPABASE_MERCHANTS_TABLE` (optional, default `merchant_mcc`)
- `KIASUMILES_DATA_BACKEND` (optional: `auto`, `supabase`, or `csv`)
- `KIASUMILES_DATA_DIR` (optional, folder with private local CSVs)
- `KIASUMILES_RATE_LIMIT_REQUESTS` (optional, default 30; 0 disables)
- `KIASUMILES_RATE_LIMIT_WINDOW_SECONDS` (optional, default 60)

Backend selection:

- `auto`: Supabase when credentials are present, else `KIASUMILES_DATA_DIR` if set, else bundled demo CSVs
- `supabase`: require Supabase, fail loudly if unreachable
- `csv`: force local CSVs, from `KIASUMILES_DATA_DIR` or the bundled demo data

The table schema lives at [supabase/schema.sql](supabase/schema.sql). Both
`kiasumiles_data_version` and `/health` report `data_backend`, so you can confirm
whether production is reading from `supabase`, `private_csv`, or `demo_csv`.

---

## Daily use

At checkout, in the car, mid-booking, ask your agent:

- "What card at NTUC FairPrice?"
- "Best card for Grab contactless?"
- "I'm at Shell. Which card?"
- "Booking flights on Singapore Airlines, which card?"
- "Which card at Shake Shack, paying online?"

KiasuMiles picks from your supplied stack and shows the earn rate and cap. If Amaze is
in the stack, the combo math is already done.

---

## Supported cards

50+ Singapore credit cards in the database. Recommendations only ever draw from the
cards you supply or save locally.

HSBC Revolution · UOB PPV · UOB Visa Signature · UOB PRVI Miles · UOB Lady's · KrisFlyer UOB · DBS Altitude · DBS yuu · DBS Woman's World · DBS Vantage · Citi Rewards · Citi PremierMiles · Citi Prestige · OCBC 90N · OCBC Rewards · OCBC VOYAGE · Maybank Horizon · Maybank World · Standard Chartered Journey · Standard Chartered Visa Infinite · BOC Elite Miles · Amex KrisFlyer · Amex KrisFlyer Ascend · Amex HighFlyer · Amaze combos · and more

Ask your agent to "show me all KiasuMiles cards" for the full list.

---

## Data

Merchant MCC data comes from community reports and gets re-verified on a rolling basis.
Card earn rates and caps come from published bank T&Cs. Results carry a confidence
level, so if a merchant only has a few data points behind it, you'll know.

---

## Feedback

If a recommendation looks wrong (wrong card, stale earn rate, missing merchant), message
[@kiasumilesbot](https://t.me/kiasumilesbot) on Telegram with the merchant name and the
card that was suggested. Every report gets read.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

---

## About

KiasuMiles is built by [Hosan](https://theaiburrow.xyz), founder of
[The AI Burrow](https://theaiburrow.xyz), Singapore's applied AI collective for teams
and builders who want to move past the hype and actually deploy.

- [theaiburrow.xyz](https://theaiburrow.xyz)
- Telegram: [t.me/theaiburrow](https://t.me/theaiburrow)
- Email: [hello@theaiburrow.xyz](mailto:hello@theaiburrow.xyz)

MIT License
