---
name: kiasumiles
description: Use KiasuMiles to configure a persistent local card wallet and recommend the best Singapore credit card for a merchant.
---

# KiasuMiles

Use this skill when the user asks to set up their KiasuMiles wallet, which Singapore credit card to use, which card earns the most miles at a merchant, or whether KiasuMiles is available.

## Workflow

1. Call `kiasumiles_agent_guide` when you need presentation rules or integration context.
2. For first-time setup, ask which banks the user has cards with. Call `kiasumiles_list_cards` once per bank, match the card names internally, then call `kiasumiles_configure` once with the complete wallet.
3. For merchant recommendations, call `kiasumiles_lookup` with the user's exact merchant name. The locally saved wallet is included automatically; never ask the user to repeat it.
4. Pass `outlet`, `channel`, and `category` only when the user's wording provides them.
5. If `wallet_configured` is false, help the user configure their wallet before giving a final recommendation.
6. Present the result with card name, miles per dollar, `cap_summary`, and `reason_summary`. Include `routing_note` or `low_confidence_note` when present.
7. If the user asks which cards are saved, call `kiasumiles_get_wallet`.
8. If the user asks whether their card stack is good or what weak categories exist, call `kiasumiles_recommend_stack`; it uses the saved wallet automatically.

## User-Facing Rules

- Do not show card IDs, MCC codes, or raw technical fields unless the user asks for diagnostics.
- Do not show local wallet paths.
- Do not claim the hosted service stores the wallet. Persistence is local to the user's device.
- Do not use web search or general bank knowledge when the KiasuMiles lookup tool is available.
- If a merchant is unknown, explain that the result is category-inferred and should be verified.
- Use `gotchas` to warn about channel traps, merchant restrictions, minimum spend, or cap constraints.
- Keep the answer short enough to use at checkout.

## Useful Prompts

- "What card should I use at NTUC FairPrice?"
- "Which card for Grab, paying in app?"
- "What card should I add to my current stack?"
