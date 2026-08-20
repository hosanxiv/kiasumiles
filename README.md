# KiasuMiles

<p align="center">
  <a href="https://kiasumiles.space">
    <img src="https://raw.githubusercontent.com/hosanxiv/kiasumiles/main/assets/kiasumiles-hero.png" alt="KiasuMiles landing page hero" width="100%">
  </a>
</p>

<p align="center">
  <a href="https://kiasumiles.space"><strong>View the live KiasuMiles landing page</strong></a>
</p>

> "Which card do I use again?"

If you're in the miles game, you've asked this at least once - standing at the cashier,
not quite sure if this is the 4 mpd card or the 1.2 mpd one.

KiasuMiles connects to your AI agent and tells you which of your selected cards earns the
most miles at the merchant in front of you. Card rules and merchant data stay current
through the hosted KiasuMiles service, while any saved card stack stays with your agent or
local connector.

---

## Why this exists

Miles guides tell you "Card X for dining, Card Y for online shopping". That works until
your wallet has six cards and the merchant in front of you doesn't fit the chart.

KiasuMiles ranks against the cards you actually hold. Your agent supplies the selected
card stack, checks it against the latest KiasuMiles rules, and returns one usable answer
with the caveats attached. Whether that stack persists across conversations depends on
your agent or connector. No second guessing at the counter.

---

## Get started

### One message to start setup

Send this message to your AI agent. It will connect KiasuMiles only when the agent and its
permissions allow it; otherwise it must stop without pretending setup succeeded.

```text
Connect me to KiasuMiles at https://kiasumiles.space/mcp if its tools are not already available.

Ask before changing any settings. Do not claim KiasuMiles is connected until you can use and list its tools.

If this AI agent does not support adding remote MCP connections from our conversation, say that it is unsupported and stop. Do not invent menu paths or setup instructions.

Once connected, check for a saved card stack if the available tools support it. Show me any saved cards and ask whether I want to keep or change them. Otherwise, ask which banks I use and show me their supported cards.

Before saving my selections, tell me what the KiasuMiles tools say about where they will be stored and whether they will persist across new conversations. Do not guess.

After confirming my cards, ask for a Singapore merchant and recommend my best card.
```

What to expect:

- **OpenClaw and Hermes through Telegram:** the agent may complete setup when it has host
  access and permission. It may ask you to approve a change or reload its tools.
- **Codex:** Codex may add the MCP connection when its environment permits it. Otherwise,
  it will stop and you can add the endpoint through Codex MCP settings.
- **Claude:** Claude cannot add KiasuMiles from a chat message. Add it as a custom connector
  in Claude's Connectors settings using the endpoint above, then send the message again.
- **ChatGPT:** ChatGPT mobile does not support custom MCP apps. On ChatGPT web, an eligible
  workspace administrator or owner must create and publish the custom app before it can be
  selected in a conversation.

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

KiasuMiles returns the best card from your card stack, the miles per dollar, the cap,
and any caveats you should know before paying.

### Check or update your cards

Use plain English:

```text
Show me my KiasuMiles card stack.
```
```text
Add OCBC 90N to my KiasuMiles card stack.
```
```text
Remove UOB PPV from my KiasuMiles card stack.
```

```text
Review my KiasuMiles card stack and tell me which categories are weak.
```

You do not need to know card IDs or technical setup details. The agent handles them.

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

- ChatGPT
- Codex
- Claude Desktop
- Claude Code
- OpenClaw
- Hermes
- Any MCP-capable agent

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

40+ Singapore credit cards in the database. Recommendations only ever draw from the
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
