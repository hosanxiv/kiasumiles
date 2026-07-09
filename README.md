# KiasuMiles

<p align="center">
  <a href="https://haohao.zo.space/kiasumiles">
    <img src="https://raw.githubusercontent.com/hosanxiv/kiasumiles/main/assets/kiasumiles-hero.png" alt="KiasuMiles landing page hero" width="100%">
  </a>
</p>

<p align="center">
  <a href="https://haohao.zo.space/kiasumiles"><strong>View the live landing page and 60s demo</strong></a>
</p>

> "Which card do I use again?"

If you're in the miles game, you've asked this at least once - standing at the cashier,
not quite sure if this is the 4 mpd card or the 1.2 mpd one.

KiasuMiles answers it over MCP. Install it in your agent, configure your wallet once,
then ask which card to use. Your wallet stays on your device while recommendations use
the current KiasuMiles card and merchant data.

---

## Why this exists

Miles guides tell you "Card X for dining, Card Y for online shopping". That works until
your wallet has six cards and the merchant in front of you doesn't fit the chart.

KiasuMiles ranks against the cards you actually hold. The local MCP loads your saved wallet,
sends it with the merchant request, and returns one usable answer with the caveats attached.
No second guessing at the counter and no repeating your card list in every conversation.

The hosted service keeps card rules and merchant data current. It never stores your wallet:
the local MCP sends the wallet with each request, where it is used once and dropped.

---

## How to use it

Install the local MCP command in any agent that supports stdio MCP:

```text
uvx kiasumiles-mcp
```

The Codex plugin already includes this command. Other clients can use the same command in
their MCP configuration.

### First-time setup prompt

Copy and paste this:

```text
Use KiasuMiles. First help me set up my wallet.
Ask me which banks I have cards with, show me the matching supported cards,
then save my selected cards locally for future KiasuMiles lookups.
```

You only do this once. The wallet remains available in new conversations on the same device.

### Everyday prompts

After setup, ask checkout questions like:

```text
What card should I use at NTUC FairPrice?
```

```text
I'm paying for Grab in the app. Which card?
```

```text
Booking Singapore Airlines online. Which card gets the most miles?
```

KiasuMiles returns the best card from your saved wallet, the miles per dollar, the cap,
and any caveats you should know before paying.

### Check or update the wallet

Use plain English:

```text
Show me my KiasuMiles wallet.
```
```text
Add OCBC 90N to my KiasuMiles wallet.
```
```text
Remove UOB PPV from my KiasuMiles wallet.
```

```text
Review my KiasuMiles wallet and tell me which categories are weak.
```

You do not need to know card IDs or wallet paths. The agent handles them.

---

## Direct Hosted MCP

Developers can still connect directly to `https://kiasumiles.space/mcp`. Direct remote
connections are deliberately stateless: the client must supply the wallet with every request.
Use the local `kiasumiles-mcp` command for the normal persistent-wallet experience.

---

## Hosted MCP Details

For agents and developers, KiasuMiles exposes these hosted MCP tools:

| Tool | What it does |
|------|--------------|
| `kiasumiles_lookup` | Best card for a merchant, ranked from the cards supplied by the client |
| `kiasumiles_list_cards` | Supported cards and their stable internal IDs |
| `kiasumiles_recommend_stack` | Weak categories in the cards supplied by the client |
| `kiasumiles_data_version` | Current card and merchant data version |
| `kiasumiles_agent_guide` | Integration and display guidance for agents |

The hosted server deliberately has no wallet setup or wallet read tools. Wallet storage
belongs in the agent, app, or user-controlled client. Hosted recommendations are scoped to
the card IDs supplied in the current request; if no cards are supplied, the tools ask for a
card stack instead of ranking the whole database.

For ChatGPT Actions, the hosted server also exposes a public REST adapter:

| Route | Purpose |
|------|---------|
| `GET /api/chatgpt/openapi.json` | OpenAPI schema for a private or public GPT Action |
| `GET /api/chatgpt/cards?bank=UOB` | Card names by bank, without internal IDs |
| `POST /api/chatgpt/lookup` | Stateless merchant lookup using cards supplied in the request |
| `POST /api/chatgpt/recommend-stack` | Weak-category review using cards supplied in the request |

The Action adapter accepts card names, resolves them internally, and strips raw card IDs
and MCC fields from public JSON responses.

Example lookup shape:

```json
{
  "merchant": "NTUC FairPrice",
  "cards": ["uob_ppv", "citi_rewards_mc"],
  "channel": "mobile_contactless"
}
```

Lookup responses include `reason_summary`, `reason_codes`, and `gotchas`, so the agent can
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

### Supported agents

- Codex plugin
- Claude Desktop
- Claude Code
- OpenClaw
- Hermes
- Any agent that can launch a local stdio MCP command

ChatGPT and other remote-only hosts can use the direct hosted MCP or Action surface, but
wallet persistence depends on storage supplied by that host.

### Codex plugin

The repo carries a local Codex plugin at `plugins/kiasumiles` and a repo marketplace at
`.agents/plugins/marketplace.json`. The plugin bundles the MCP config, a skill for
checkout recommendations, and display guidance so Codex doesn't surface card IDs, MCC
codes, or raw technical fields at the user.

In Codex, add the repo marketplace, install KiasuMiles, configure your wallet once, then ask:

> "What card should I use at NTUC FairPrice?"

---

## For Maintainers

The hosted app reads card rules and merchant mappings from the configured production
backend. The public package ships small demo CSVs for development and tests.

Environment variables (set in Vercel for hosted deployments):

- `KIASUMILES_SUPABASE_URL`
- `KIASUMILES_SUPABASE_SERVICE_ROLE_KEY`
- `KIASUMILES_SUPABASE_CARDS_TABLE` (optional, default `card_rules`)
- `KIASUMILES_SUPABASE_MERCHANTS_TABLE` (optional, default `merchant_mcc`)
- `KIASUMILES_DATA_BACKEND` (optional: `auto` or `supabase`)
- `KIASUMILES_RATE_LIMIT_REQUESTS` (optional, default 30; 0 disables)
- `KIASUMILES_RATE_LIMIT_WINDOW_SECONDS` (optional, default 60)

Backend selection:

- `auto`: Supabase when credentials are present, else bundled demo CSVs
- `supabase`: require Supabase, fail loudly if unreachable

The table schema lives at [supabase/schema.sql](supabase/schema.sql). Both
`kiasumiles_data_version` and `/health` report `data_backend`, so you can confirm
whether production is reading from `supabase` or `demo_csv`.

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
cards you supply in the request.

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
