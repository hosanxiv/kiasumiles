---
name: kiasumiles
description: Use KiasuMiles to recommend the best Singapore credit card for a merchant or explain the hosted MCP workflow.
---

# KiasuMiles

Use this skill when the user asks which Singapore credit card to use, which card earns the most miles at a merchant, or whether the KiasuMiles MCP server is available.

## Workflow

1. If KiasuMiles MCP tools are available, call `kiasumiles_agent_guide` when you need presentation rules or integration context.
2. Ask which banks the user has cards with before listing cards. Call `kiasumiles_list_cards` once per bank, then gather the user's card IDs client-side for later requests.
3. For merchant recommendations, call `kiasumiles_lookup` with the user's exact merchant name and the card IDs they provided. Pass `outlet`, `channel`, and `category` only when the user's wording provides them.
4. If `wallet_configured` is false, ask which cards the user carries before giving a final recommendation.
5. Present the result with card name, miles per dollar, `cap_summary`, and `reason_summary`. Include `routing_note` or `low_confidence_note` when present.
6. If the user asks whether their card stack is good, what cards to add, or what gaps they have, call `kiasumiles_recommend_stack` with their card IDs.

## User-Facing Rules

- Do not show card IDs, MCC codes, or raw technical fields unless the user asks for diagnostics.
- Do not use web search or general bank knowledge when the KiasuMiles lookup tool is available.
- If a merchant is unknown, explain that the result is category-inferred and should be verified.
- Use `gotchas` to warn about channel traps, merchant restrictions, minimum spend, or cap constraints.
- Keep the answer short enough to use at checkout.

## Useful Prompts

- "What card should I use at NTUC FairPrice?"
- "Which card for Grab, paying in app?"
- "What card should I add to my current stack?"
