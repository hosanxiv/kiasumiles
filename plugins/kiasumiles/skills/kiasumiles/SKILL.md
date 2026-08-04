---
name: kiasumiles
description: Use hosted KiasuMiles to recommend the best Singapore credit card from the cards the user supplies.
---

# KiasuMiles

Use this skill when the user asks which Singapore credit card to use, which card earns the most miles at a merchant, whether their selected cards have weak categories, or whether KiasuMiles is available.

## Workflow

1. Call `kiasumiles_agent_guide` when you need presentation rules or integration context.
2. Before the first lookup, ask which banks the user has cards with if the client has not already supplied a card stack. Call `kiasumiles_list_cards` once per bank and match the selected card names to internal IDs.
3. Keep the selected card stack in the agent or client only. Pass the selected card IDs in the `cards` parameter for each hosted lookup or stack review.
4. For merchant recommendations, call `kiasumiles_lookup` with the user's exact merchant name and selected card IDs.
5. Pass `outlet`, `channel`, and `category` only when the user's wording provides them.
6. If `wallet_configured` is false, ask which cards the user carries before giving a final recommendation.
7. Present the result with card name, miles per dollar, `cap_summary`, and `reason_summary`. Include `routing_note` or `low_confidence_note` when present.
8. If the user asks whether their selected cards have weak categories, call `kiasumiles_recommend_stack` with those card IDs.

## User-Facing Rules

- Do not show card IDs, MCC codes, or raw technical fields unless the user asks for diagnostics.
- Do not claim the hosted service stores a wallet. It receives the selected cards for the current request only.
- Do not claim the user's card selection persists unless the agent or client explicitly documents and confirms that behavior.
- Do not use web search or general bank knowledge when the KiasuMiles lookup tool is available.
- If a merchant is unknown, explain that the result is category-inferred and should be verified.
- Use `gotchas` to warn about channel traps, merchant restrictions, minimum spend, or cap constraints.
- Keep the answer short enough to use at checkout.

## Useful Prompts

- "What card should I use at NTUC FairPrice?"
- "Which card for Grab, paying in app?"
- "Does my selected card stack have any weak categories?"
