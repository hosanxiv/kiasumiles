# KiasuMiles

<p align="center">
  <a href="https://kiasumiles.space">
    <img src="https://raw.githubusercontent.com/hosanxiv/kiasumiles/main/assets/kiasumiles-hero.png" alt="KiasuMiles landing page hero" width="100%">
  </a>
</p>

<p align="center">
  <a href="https://kiasumiles.space"><strong>Visit kiasumiles.space</strong></a>
</p>

> “Which card do I use again?”

KiasuMiles helps you choose from the Singapore miles cards you already hold. Tell a compatible AI agent which cards are in your stack, ask about a merchant, and KiasuMiles ranks those cards using its centrally maintained card and merchant database.

The hosted KiasuMiles service does not store your card stack. It never needs your card number, expiry date, CVV, banking login or payment details.

## Quick start

Send this message to your AI agent:

```text
Connect me to KiasuMiles at https://kiasumiles.space/mcp if its tools are not already available.

Ask before changing settings or running installation commands. Do not say KiasuMiles is connected until you can list its tools and successfully call its data-version tool.

If you cannot add the connection yourself, say so plainly and give me only the documented setup steps for the AI agent I am using. Do not guess. Then wait for me to complete them.

Once KiasuMiles is available, check whether this installation provides tools to read or configure a saved card stack. If it does, show me any saved cards and ask whether I want to keep or change them. If it does not, explain how this AI agent can supply my selected cards for KiasuMiles lookups and whether my selections will persist between conversations.

Ask which banks I have cards with, show me the matching supported cards, and ask me to confirm my selections.

Use only the storage method documented by the available tools. Never claim the hosted KiasuMiles server stores my card stack.

After confirming my cards, ask for a Singapore merchant and recommend my best card.
```

This message is both a setup request and a capability check. Some AI agents can add the connection after asking for approval. Others require you or a workspace administrator to add it in settings.

## Choose your AI agent

### OpenClaw or Hermes through Telegram

Paste the quick-start message into your Telegram chat.

If your agent is allowed to update its MCP configuration, it can ask for approval, add KiasuMiles and verify the tools. This depends on the permissions configured by the person who runs your agent, so do not treat a success message as proof unless the agent can actually use the KiasuMiles tools.

### Codex on desktop

In the desktop app:

1. Open **Settings → MCP servers**.
2. Select **Add server**.
3. Name it `KiasuMiles`.
4. Choose **Streamable HTTP**.
5. Enter:

   ```text
   https://kiasumiles.space/mcp
   ```

6. Save the server and restart the app.
7. Use `/mcp` to confirm that the KiasuMiles tools are available.
8. Send the quick-start message above.

Codex CLI users can add the same hosted server with:

```bash
codex mcp add kiasumiles --url https://kiasumiles.space/mcp
```

Then run `codex mcp list` or use `/mcp` to verify it.

### Claude

Add KiasuMiles as a custom connector using Claude on the web or Claude Desktop:

1. Open **Customize → Connectors**.
2. Select **+ → Add custom connector**.
3. Enter `KiasuMiles` and:

   ```text
   https://kiasumiles.space/mcp
   ```

4. Add the connector.
5. Enable it for the conversation, then send the quick-start message.

Claude currently makes custom connectors available on Free, Pro, Max, Team and Enterprise plans; Free accounts are limited to one custom connector. On Team and Enterprise plans, an Owner or Primary Owner must add the connector for the organisation before members can connect it.

Claude supports connectors on iOS and Android. Installing connectors on mobile is currently in beta, so web or desktop remains the more reliable setup path.

See [Claude’s custom connector guide](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp).

### ChatGPT web and ChatGPT Work

Do not expect the quick-start message to install KiasuMiles by itself.

If your account or workspace provides custom MCP apps in developer mode, add KiasuMiles as a custom app on ChatGPT web using:

```text
https://kiasumiles.space/mcp
```

Managed workspaces may require an administrator or owner to enable developer mode, create and review the app, and publish it to the workspace before members can use it.

After the app is available in a chat, send the quick-start message.

Custom MCP apps are currently web-only in ChatGPT. Do not claim that this setup works in the ChatGPT mobile app.

See [OpenAI’s developer-mode and MCP app guide](https://help.openai.com/en/articles/12584461-developer-mode-apps-and-full-mcp-connectors-in-chatgpt-beta).

### Another AI agent

Check whether it supports remote MCP servers over Streamable HTTP and lets you add a custom server URL. If it does, add:

```text
https://kiasumiles.space/mcp
```

Then verify that it can list and call the KiasuMiles tools before relying on it.

## First use

After KiasuMiles is connected:

1. Your agent asks which banks you use.
2. KiasuMiles shows the supported cards from those banks.
3. You confirm the cards you hold.
4. Your agent explains whether it can remember that selection.
5. You provide a merchant and, where useful, how you are paying.
6. KiasuMiles ranks only the cards supplied for that lookup.

Try:

```text
What card should I use at NTUC FairPrice?
```

Other useful questions:

```text
I’m paying for Grab in the app. Which card should I use?
```

```text
Which card should I use for a Singapore Airlines booking online?
```

```text
Which of my cards should I use at this restaurant with Apple Pay?
```

The result can include the card name, miles per dollar, spending-cap summary, reason for the ranking and relevant caveats.

## Your card stack and privacy

The hosted KiasuMiles MCP server has no wallet-save or wallet-read tools. For each hosted recommendation, the AI agent or client supplies the selected cards in that request.

Whether your card stack survives a new conversation depends on the AI agent or client you are using. KiasuMiles cannot guarantee that persistence, so ask the agent to explain its documented storage behaviour.

KiasuMiles needs only the names of your cards. Do not provide:

- Card numbers
- Expiry dates
- CVVs
- Banking usernames or passwords
- One-time passwords
- Transaction or account credentials

If your agent supports remembering your selection, you can ask:

```text
Show me the card stack you use for KiasuMiles lookups.
```

```text
Add OCBC 90°N to the card stack you use for KiasuMiles.
```

```text
Remove UOB Preferred Visa from the card stack you use for KiasuMiles.
```

The agent should tell you whether that change will persist. These are requests to your agent; the hosted KiasuMiles server itself does not save the stack.

## Troubleshooting

### The agent says it cannot connect

- Confirm that the agent supports remote MCP servers over Streamable HTTP.
- Check that the endpoint is exactly `https://kiasumiles.space/mcp`.
- Check whether your account or workspace allows custom connections.
- Use the product-specific steps above instead of asking the agent to guess.

### The agent says KiasuMiles is connected, but cannot list its tools

The connection has not been verified. Restart or reload the agent using its documented method, then require it to list the KiasuMiles tools and call `kiasumiles_data_version`.

### My card stack disappeared in a new conversation

The agent or client did not persist it. Run the quick-start message again and ask the agent to explain its storage behaviour. The hosted KiasuMiles server is not a wallet store.

### The recommendation is too broad

Include the exact merchant and payment method:

```text
Which of my cards should I use at NTUC FairPrice with Apple Pay?
```

### The service returns a rate-limit error

The hosted MCP endpoint defaults to 30 requests per 60 seconds for each IP address handled by a running service instance. If you receive HTTP 429, wait and retry.

## Supported cards and data

Ask your agent:

```text
Show me all cards currently supported by KiasuMiles.
```

The production service reports its current number of card rules, merchant records, data version and backend at:

```text
https://kiasumiles.space/health
```

Records may include a confidence level and last-verified date, but those fields do not guarantee that every merchant classification or bank rule is current.

Recommendations are informational. Check the relevant bank’s current terms before making a large or unusual purchase.

For supported Amaze pairings, include both Amaze and the paired card in your selected stack so KiasuMiles can apply its configured adjustment.

## Hosted MCP reference

KiasuMiles currently exposes five hosted MCP tools:

| Tool | Purpose |
|---|---|
| `kiasumiles_list_cards` | Lists supported cards, optionally filtered by bank |
| `kiasumiles_lookup` | Ranks supplied cards for a merchant |
| `kiasumiles_recommend_stack` | Reviews category coverage among supplied cards |
| `kiasumiles_data_version` | Returns the data version, record counts and backend |
| `kiasumiles_agent_guide` | Returns integration and display guidance |

Hosted lookups are stateless. The `cards` parameter is required, and the server does not retain it as a wallet.

### Test the MCP connection

```bash
curl -i -X POST https://kiasumiles.space/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl-smoke","version":"1.0"}}}'
```

### Public REST adapter

The hosted service also exposes a stateless REST adapter:

| Route | Purpose |
|---|---|
| `GET /api/chatgpt/openapi.json` | OpenAPI schema |
| `GET /api/chatgpt/cards?bank=UOB` | Lists supported card names by bank |
| `POST /api/chatgpt/lookup` | Looks up a merchant using card names supplied in the request |
| `POST /api/chatgpt/recommend-stack` | Reviews the supplied card stack |

The public adapter accepts card names and removes internal card IDs, merchant-category codes and internal reason codes from its JSON responses.

Example:

```json
{
  "merchant": "NTUC FairPrice",
  "cards": [
    "UOB Preferred Visa",
    "Citi Rewards Mastercard"
  ],
  "channel": "mobile_contactless"
}
```

## For maintainers

Production can load card rules and merchant mappings from Supabase. The repository includes a smaller bundled dataset for development and tests.

Environment variables:

- `KIASUMILES_SUPABASE_URL`
- `KIASUMILES_SUPABASE_SERVICE_ROLE_KEY`
- `KIASUMILES_SUPABASE_CARDS_TABLE` — optional; defaults to `card_rules`
- `KIASUMILES_SUPABASE_MERCHANTS_TABLE` — optional; defaults to `merchant_mcc`
- `KIASUMILES_DATA_BACKEND` — optional; `auto` or `supabase`
- `KIASUMILES_RATE_LIMIT_REQUESTS` — optional; defaults to `30`; `0` disables the MCP rate limit
- `KIASUMILES_RATE_LIMIT_WINDOW_SECONDS` — optional; defaults to `60`

Backend selection:

- `auto`: use Supabase when its credentials are present; otherwise use the bundled dataset
- `supabase`: require Supabase and fail if it is unavailable

The database schema is at [supabase/schema.sql](supabase/schema.sql). Both `/health` and `kiasumiles_data_version` report the selected backend.

### Supabase keep-awake

The `Supabase keep-awake` GitHub Actions workflow performs one direct, read-only
`card_rules` query at 08:17, 16:17, and 00:17 Singapore time each day. It does
not use the hosted `/health` route, because a warm hosted process can serve
cached data without touching Supabase. The query selects one identifier and
never inserts, updates, or deletes data.

Configure the encrypted repository secrets:

1. In the GitHub repository, open **Settings → Secrets and variables → Actions**.
2. Choose **New repository secret** and create
   `KIASUMILES_SUPABASE_URL` with the production project API URL.
3. Choose **New repository secret** again and create
   `KIASUMILES_SUPABASE_SERVICE_ROLE_KEY` with the production service-role key
   used by the hosted backend.

Never put either value in the workflow file, source code, logs, or a pull
request. The script prints only a generic success message or a sanitized error;
a failed query exits non-zero so the workflow is visibly red in GitHub Actions.

The scheduled trigger starts only after the workflow is on the repository's
default branch. After merging, open **Actions → Supabase keep-awake → Run
workflow** once and confirm the run succeeds. Keep GitHub Actions failure
notifications enabled so a failed scheduled run is noticed.

## Feedback

If a recommendation appears wrong or a merchant is missing, message [@kiasumilesbot](https://t.me/kiasumilesbot) on Telegram with the merchant name and the recommendation you received.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## About

KiasuMiles is built by [Hosan](https://theaiburrow.xyz), founder of [The AI Burrow](https://theaiburrow.xyz), Singapore’s applied AI collective for teams and builders who want to move past the hype and actually deploy.

- [theaiburrow.xyz](https://theaiburrow.xyz)
- Telegram: [t.me/theaiburrow](https://t.me/theaiburrow)
- Email: [hello@theaiburrow.xyz](mailto:hello@theaiburrow.xyz)

MIT License
