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

KiasuMiles connects to an AI agent that supports remote MCP and tells you which of your
selected cards earns the most miles at the merchant in front of you. Card rules and
merchant data stay current through the hosted KiasuMiles service.

---

## Why this exists

Miles guides tell you "Card X for dining, Card Y for online shopping". That works until
your wallet has six cards and the merchant in front of you doesn't fit the chart.

KiasuMiles ranks against the cards you actually hold. Your AI agent supplies the selected
card stack, checks it against the latest KiasuMiles rules, and returns one usable answer
with the caveats attached. Whether the stack is remembered depends on your agent or
client. No second guessing at the counter.

---

## Get started

### Requirements

You need an AI agent or client that supports remote MCP connections. The agent must also
have permission to add or use the connection. Some environments can connect from a
message; others require you or a workspace administrator to add the endpoint in settings.

The KiasuMiles remote MCP endpoint is:

```text
https://kiasumiles.space/mcp
```

### One message to start setup

Copy and paste this exact message into your AI agent:

```text
Connect me to KiasuMiles at https://kiasumiles.space/mcp if your environment supports remote MCP connections and its tools are not already available.

Ask before changing any settings. Do not say KiasuMiles is connected until you can actually list and use its tools.

If you cannot add the connection yourself, say so plainly and stop. Do not invent setup instructions.

Once connected, help me set up my card stack. Ask which banks I use, show me the matching supported cards, and ask me to confirm my selections.

Before saving anything, explain only what the available tools document about storage and whether my selections will persist. Do not guess.

After confirming my cards, ask for a Singapore merchant and recommend my best card.
```

### What happens the first time

1. The agent checks whether the KiasuMiles tools are already available.
2. If its environment allows it, the agent asks before adding the remote MCP connection.
3. The agent verifies the connection by listing and using the available KiasuMiles tools.
4. It asks which banks and supported cards you use.
5. Before saving anything, it explains what its available tools say about storage and
   persistence.
6. It asks for a Singapore merchant and ranks only the cards you confirmed.

If the agent cannot add a remote MCP connection itself, the prompt tells it to stop
instead of guessing at product-specific menus. Add the endpoint through the agent's own
documented settings, then run the message again.

### Storage and persistence

KiasuMiles never needs your card number, expiry date or CVV. It works only with the card
names you choose to provide. How those names are remembered depends on your AI agent.

The hosted KiasuMiles server exposes recommendation and card-reference tools, but no
wallet save or wallet read tool. Each hosted recommendation is calculated from the cards
the client supplies with that request. Do not assume your card stack will survive a new
conversation unless your agent or client explicitly documents and confirms that behavior.

### Compatibility and mobile

Compatibility depends on a capability, not a brand name: the environment must support
remote MCP connections and allow the KiasuMiles endpoint to be added. A desktop, web and
mobile version of the same product may expose different integrations. Do not assume the
mobile version works just because another version does; check the current settings and
official documentation for the exact app and account you are using.

**OpenClaw and Hermes via Telegram:** Paste the setup prompt directly into your Telegram
chat. The agent will connect KiasuMiles and guide you through choosing your cards. Approve
the connection if it asks.

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

### Troubleshooting

**The agent says it cannot connect**

- Confirm that the environment supports remote MCP connections.
- Check that the endpoint is exactly `https://kiasumiles.space/mcp`.
- Use the environment's documented integration settings if connections cannot be added
  from a conversation.
- If a workspace administrator controls integrations, ask them to approve the endpoint.

**The agent says it connected, but cannot list KiasuMiles tools**

The connection is not verified yet. Ask it to reload existing connections only if that
action is supported by the environment, then list the KiasuMiles tools. Do not treat an
unchanged settings screen as proof that the tools work.

**Your card stack is missing in a new conversation**

That means the agent or client did not persist it in the way you expected. Run the setup
message again and ask the agent to explain its documented storage behavior before saving.
The hosted KiasuMiles server is not a wallet store.

**The recommendation is too broad**

Include the exact merchant and how you are paying, for example:

```text
Which of my cards should I use at NTUC FairPrice with Apple Pay?
```

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

For developers integrating through an OpenAPI action, the hosted server also exposes a
public REST adapter:

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

The endpoint is rate limited per IP (30 requests per minute by default). Normal agent
use never gets near it.

### Try it

```bash
curl -i -X POST https://kiasumiles.space/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl-smoke","version":"1.0"}}}'
```

---

### Client compatibility

Use the hosted MCP endpoint from any AI agent or client that documents support for remote
MCP connections. Setup and persistence are controlled by that environment, not by
KiasuMiles.

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
