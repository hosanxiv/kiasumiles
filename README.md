# KiasuMiles

> SG's first AI-powered miles card optimizer — *"which card do I tap?"*

KiasuMiles connects to your AI agent and tells you which credit card earns the most miles at any Singapore merchant — based on the actual MCC your card will post under.

**No hosting. No API keys. Works offline.**

---

## How it works

1. You install KiasuMiles and connect it to your agent (Claude, OpenClaw, Hermes)
2. You tell the agent which cards you carry — once, in plain English
3. Next time you're at a merchant, just ask: *"which card?"*

---

## Step 1 — Install

```bash
pip install kiasumiles-mcp
```

This installs KiasuMiles and creates an entry point at `~/.local/bin/kiasumiles-mcp` (or inside your active virtual environment). If the command runs without errors, you're ready for Step 2.

> **Using a virtual environment?** Activate it first, then `pip install kiasumiles-mcp`. Note the full path to `kiasumiles-mcp` inside your venv — you'll need it in Step 2.

---

## Step 2 — Connect to your agent

Pick your agent and follow the instructions. **You only do this once.**

---

### Claude Desktop

1. Open this file in a text editor:
   `~/Library/Application Support/Claude/claude_desktop_config.json`

   *(If the file doesn't exist yet, create it)*

2. Add this — if there's already content in the file, add the `"kiasumiles"` block inside the existing `"mcpServers"` section:

```json
{
  "mcpServers": {
    "kiasumiles": {
      "command": "uvx",
      "args": ["kiasumiles-mcp"]
    }
  }
}
```

3. Save the file and **fully quit and reopen Claude Desktop**

4. Check it loaded: look for KiasuMiles in the tools menu (the hammer icon), or ask:
   > *"What KiasuMiles tools do you have?"*
   
   Claude should list four tools. If it says it doesn't know what KiasuMiles is, the server didn't load — see [Troubleshooting](#troubleshooting).

---

### Claude CLI (Claude Code)

Run these two commands in your terminal — the second one finds the path automatically:

```bash
pip install kiasumiles-mcp
claude mcp add kiasumiles $(which kiasumiles-mcp)
```

> **Using a virtual environment?** Activate it first, *then* run both commands above. The `$(which kiasumiles-mcp)` part finds wherever the package was just installed.

Restart Claude CLI, then run `/mcp` to verify:

```
kiasumiles: /path/to/kiasumiles-mcp  - ✓ Connected
```

If it shows **Failed to connect**, the path is wrong — see [Troubleshooting](#troubleshooting).

---

### OpenClaw

Edit `~/.openclaw/config.json`:

```json
{
  "mcpServers": {
    "kiasumiles": {
      "command": "uvx",
      "args": ["kiasumiles-mcp"]
    }
  }
}
```

Restart OpenClaw and check that `kiasumiles` appears in your connected tools.

---

### Hermes

Edit `~/.hermes/mcp.json`:

```json
{
  "mcpServers": {
    "kiasumiles": {
      "command": "uvx",
      "args": ["kiasumiles-mcp"]
    }
  }
}
```

Restart Hermes and check that `kiasumiles` appears in your connected tools.

---

## Step 3 — Set up your card wallet

Once KiasuMiles is connected and showing as loaded, tell your agent exactly this — replacing the cards with your own:

> *"Use kiasumiles_list_cards to see what's available, then set up my KiasuMiles wallet with these cards: HSBC Revolution, UOB PPV, DBS yuu, Amaze, Citi Rewards Mastercard, DBS Altitude, UOB PRVI Miles."*

The agent will match your card names to the database and save your wallet. You only do this once.

**Example response you should see:**

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

If a card isn't found, it means the name didn't match — ask *"show me all KiasuMiles cards"* to find the right name.

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

Or edit `~/.kiasumiles/wallet.yaml` directly.

---

## Troubleshooting

**"Failed to connect" / Claude doesn't know what KiasuMiles is**

Claude Code silently swallows MCP startup errors, so "Failed to connect" gives no clue why. Run this in your terminal to see the real error:

```bash
kiasumiles-mcp
```

Common causes:

**1. Command not found** — package isn't installed or isn't on your PATH:
```bash
pip install kiasumiles-mcp
```

**2. Wrong path registered** — the MCP config points somewhere stale. Fix it:
```bash
claude mcp remove kiasumiles
claude mcp add kiasumiles $(which kiasumiles-mcp)
```
Then restart Claude Code and run `/mcp` — you should see `✓ Connected`.

**3. Virtual environment not active** — if you installed into a venv, you must activate it before running the `claude mcp add` command:
```bash
source /path/to/your/venv/bin/activate
claude mcp remove kiasumiles
claude mcp add kiasumiles $(which kiasumiles-mcp)
```

**Quick check** — paste this in your terminal to confirm everything is wired correctly:
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' | kiasumiles-mcp
```
You should see a JSON response containing `"name":"KiasuMiles"`. If you get an error instead, the binary isn't working and the MCP won't connect.

**Card not found during wallet setup**

Ask your agent: *"show me all KiasuMiles cards"* — this lists every supported card by name. Find yours and use that exact name.

**Data feels outdated**

Ask: *"refresh my KiasuMiles data"* — this pulls the latest merchant and card rules from GitHub.

---

## Tools

| Tool | What it does |
|------|--------------|
| `kiasumiles_lookup` | Best card for a merchant — MCC, earn rate, cap |
| `kiasumiles_configure` | Save your wallet |
| `kiasumiles_list_cards` | See all 48 supported cards |
| `kiasumiles_refresh` | Pull latest data from GitHub |

---

## Supported cards (sample)

HSBC Revolution · UOB PPV · UOB Visa Signature · DBS Altitude · DBS yuu · DBS Woman's World · Citi Rewards · Citi PremierMiles · OCBC 90N · OCBC Rewards · Maybank Horizon · Maybank World · UOB PRVI Miles · UOB Lady's · KrisFlyer UOB · Amex KrisFlyer · Standard Chartered Journey · BOC Elite Miles · Amaze combos · and more

Ask *"show me all KiasuMiles cards"* for the full list.

---

## Data

Merchant MCC data is community-verified and updated monthly. Card rules sourced from publicly available bank T&Cs.

---

*Built by [Hosan](https://aiburrow.xyz) · MIT License*
