# KiasuMiles

> *"Which card do I use again?"*

If you're in the miles game, you've asked this at least once - standing at the cashier,
not quite sure if this is the 4 mpd one or the 1.2 mpd one.

KiasuMiles solves this. It connects to your AI agent, learns your exact cards, and tells 
you which one earns the most miles at any Singapore merchant — based on the actual MCC your 
card posts under, not generic blog listicles.

Tell it which cards you carry. Once. It remembers. From then on, just ask.

**No hosting. No API keys. Works offline.**

---

## Why it's different

Most miles guides tell you *"use Card X for dining, Card Y for online shopping."* Useful — until your wallet has 6 cards and you're standing at the checkout trying to remember which one applies here.

KiasuMiles knows **your wallet specifically**. It filters out every card you don't own, factors in monthly caps, and if you carry Amaze, it automatically nets out the fee and calculates the combo earn rate.

You ask. It answers. One card. No second-guessing.

---

## How it works

1. Ask your agent to install KiasuMiles
2. Tell your agent which cards you carry — once, in plain English
3. At any merchant, just ask: *"which card?"*

Your agent returns your best card, the earn rate, and the monthly cap — from your wallet only.

---

## Setup

**Easiest:** Tell your agent to install it for you:

> *"Install kiasumiles-mcp for me"*

Your agent handles the rest automatically.

**Or install directly:**

```bash
pip3 install kiasumiles-mcp && kiasumiles-setup
```

The setup script auto-configures Claude Desktop and Claude Code if installed.

### Supported agents

- **Claude Desktop**
- **Claude Code (CLI)**
- **OpenClaw** 
- **Hermes** — after install, run `hermes mcp list` and `hermes mcp test kiasumiles` to verify. If KiasuMiles tools still don't appear after `/new`, restart the gateway with `hermes gateway restart`, then start a fresh chat.
- **Any agent with pip access**

---

## Set up your card wallet

> *"Use KiasuMiles to set up my wallet — show me what cards are available, then ask me which ones I have"*

Your agent shows you all supported cards, asks which ones you carry, and saves your wallet. You only do this once. To check what's saved anytime:

> *"Use KiasuMiles to show me my wallet"*

---

## Daily use

At a merchant, in the car, at checkout — just ask:

- *"What card at NTUC FairPrice?"*
- *"Best card for Grab contactless?"*
- *"I'm at Shell. Which card?"*
- *"Booking flights on Singapore Airlines — which card?"*
- *"Which card at Shake Shack — paying online"*

KiasuMiles surfaces your best option with the earn rate and cap. If you have Amaze, the combo math is already done.

---

## Updating your wallet

> *"Update my KiasuMiles wallet — add OCBC 90N Mastercard, remove UOB PPV."*

Plain English. Your agent handles the rest.

---

## Tools

| Tool | What it does |
|------|--------------|
| `kiasumiles_lookup` | Best card for a merchant — MCC, earn rate, cap |
| `kiasumiles_configure` | Save your card wallet |
| `kiasumiles_get_wallet` | See your currently saved cards |
| `kiasumiles_list_cards` | See all 50+ supported cards |

---

## Supported cards

50+ Singapore credit cards in the database — but KiasuMiles only ever shows you results for cards **you actually carry**. Set up your wallet once; everything else is filtered out.

HSBC Revolution · UOB PPV · UOB Visa Signature · UOB PRVI Miles · UOB Lady's · KrisFlyer UOB · DBS Altitude · DBS yuu · DBS Woman's World · DBS Vantage · Citi Rewards · Citi PremierMiles · Citi Prestige · OCBC 90N · OCBC Rewards · OCBC VOYAGE · Maybank Horizon · Maybank World · Standard Chartered Journey · Standard Chartered Visa Infinite · BOC Elite Miles · Amex KrisFlyer · Amex KrisFlyer Ascend · Amex HighFlyer · Amaze combos · and more

> *"Show me all KiasuMiles cards"* — ask your agent for the full list.

---

## Data

Merchant MCC data is community-verified and updated regularly. Card earn rates and caps are sourced from publicly available bank T&Cs.

Confidence levels are included in results — if a merchant has limited data points, you'll know.

---

## Verify installation

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
