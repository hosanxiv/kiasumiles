# KiasuMiles

> SG's first AI-powered miles card optimizer — *"which card do I tap?"*

KiasuMiles connects to your AI agent and tells you which credit card earns the most miles at any Singapore merchant — based on the actual MCC your card will post under.

**No hosting. No API keys. Works offline.**

---

## How it works

1. Add KiasuMiles to your agent's MCP config (one config block, copy-paste)
2. Tell your agent which cards you carry — once, in plain English
3. Next time you're at a merchant, just ask: *"which card?"*

---

## Setup

Pick your agent below. **You only do this once.**

---

### Claude Desktop

Open this file in a text editor:

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

*(Create it if it doesn't exist yet)*

Add the `"kiasumiles"` block inside `"mcpServers"`:

```json
{
  "mcpServers": {
    "kiasumiles": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/hosanxiv/kiasumiles", "kiasumiles-mcp"]
    }
  }
}
```

Save and fully restart Claude Desktop.

> **First time using uvx?** Install `uv` first — it's a fast Python tool manager:
> ```bash
> curl -LsSf https://astral.sh/uv/install.sh | sh
> ```
> Then restart your terminal and try again.

**Check it loaded:** look for KiasuMiles in the tools menu (hammer icon), or ask:
> *"What KiasuMiles tools do you have?"*

---

### Claude Code (CLI)

Install the package locally, then register it:

```bash
pip3 install kiasumiles-mcp
kiasumiles-setup
```

`kiasumiles-setup` auto-connects to Claude Desktop and Claude Code in one step.

Restart Claude Code, then run `/mcp` to confirm:

```
kiasumiles: /path/to/kiasumiles-mcp  - ✓ Connected
```

> **Prefer uv?** `uv tool install kiasumiles-mcp` then `kiasumiles-setup`
> **Using pipx?** `pipx install kiasumiles-mcp` then `kiasumiles-setup`

---

### OpenClaw

Add to your OpenClaw MCP config:

```json
{
  "mcpServers": {
    "kiasumiles": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/hosanxiv/kiasumiles", "kiasumiles-mcp"]
    }
  }
}
```

> **Running OpenClaw on a VPS (Ubuntu)?** Install `uv` first:
> ```bash
> curl -LsSf https://astral.sh/uv/install.sh | sh
> source $HOME/.local/bin/env
> ```
> Then add the config block above and restart OpenClaw.

---

### Hermes

Add to your Hermes MCP config:

```json
{
  "mcpServers": {
    "kiasumiles": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/hosanxiv/kiasumiles", "kiasumiles-mcp"]
    }
  }
}
```

> **Running Hermes on a VPS (Ubuntu)?** Install `uv` first:
> ```bash
> curl -LsSf https://astral.sh/uv/install.sh | sh
> source $HOME/.local/bin/env
> ```
> Then add the config block above and restart Hermes.

---

## Set up your card wallet

Once KiasuMiles is connected, tell your agent — replacing the cards with your own:

> *"Use kiasumiles_list_cards to see what's available, then set up my KiasuMiles wallet with these cards: HSBC Revolution, UOB PPV, DBS yuu, Amaze, Citi Rewards Mastercard, DBS Altitude, UOB PRVI Miles."*

The agent matches your card names to the database and saves your wallet. You only do this once.

**Example response:**

```
Wallet saved with 7 cards:
· HSBC Revolution
· UOB Preferred Platinum Visa
· DBS yuu Visa
· Amaze
· Citi Rewards Mastercard
· DBS Altitude Visa
· UOB PRVI Miles Visa

Wallet saved to ~/.kiasumiles/wallet.yaml
```

If a card isn't found, ask *"show me all KiasuMiles cards"* to find the right name.

---

## Daily use

Just ask, any time:

- *"What card at NTUC FairPrice?"*
- *"Best card for Grab contactless?"*
- *"I'm at Shell. Which card?"*
- *"Booking flights on Singapore Airlines — which card?"*
- *"Which card at Shake Shack — I'm paying online"*

KiasuMiles returns your best card, the earn rate, and the monthly cap. If you have Amaze, it automatically factors in the combo and nets out the fee.

---

## Updating your wallet

Changed cards? Tell your agent:

> *"Update my KiasuMiles wallet — add OCBC 90N Mastercard, remove UOB PPV."*

You can also ask: *"What cards do I have saved?"* to see your current wallet.

---

## Troubleshooting

**Agent doesn't know what KiasuMiles is after setup**

Run this in your terminal to check the server starts correctly:

```bash
uvx --from git+https://github.com/hosanxiv/kiasumiles kiasumiles-mcp
```

You should see a JSON response. If you get an error, the most common cause is `uv` not being installed — see the setup steps for your agent above.

---

**Claude Code: "Failed to connect"**

Run to see the real error:

```bash
kiasumiles-mcp
```

Then re-register:

```bash
claude mcp remove kiasumiles
claude mcp add kiasumiles $(which kiasumiles-mcp)
```

---

**Card not found during wallet setup**

Ask your agent: *"show me all KiasuMiles cards"* — lists every supported card by name.

---

## Tools

| Tool | What it does |
|------|--------------|
| `kiasumiles_lookup` | Best card for a merchant — MCC, earn rate, cap |
| `kiasumiles_configure` | Save your wallet |
| `kiasumiles_get_wallet` | See your currently saved cards |
| `kiasumiles_list_cards` | See all supported cards |

---

## Supported cards (brief list)

HSBC Revolution · UOB PPV · UOB Visa Signature · DBS Altitude · DBS yuu · DBS Woman's World · Citi Rewards · Citi PremierMiles · OCBC 90N · OCBC Rewards · Maybank Horizon · Maybank World · UOB PRVI Miles · UOB Lady's · KrisFlyer UOB · Amex KrisFlyer · Standard Chartered Journey · BOC Elite Miles · Amaze combos · and more

Ask *"show me all KiasuMiles cards"* for the full list.

---

## Data

Merchant MCC data is community-verified and updated regularly. Card rules sourced from publicly available bank T&Cs.

---

*Built by [Hosan](https://theaiburrow.xyz) · MIT License*
