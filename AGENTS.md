## Project

KiasuMiles is a hosted Python MCP service for Singapore credit-card miles recommendations.
Keep lookup, merchant matching, and card ranking deterministic: no web calls from the recommendation path.

## Architecture

- `kiasumiles/hosted.py` is the FastMCP adapter. Keep it thin.
- `kiasumiles/tools.py` contains reusable tool handlers for Codex, tests, and future hosted ChatGPT Apps SDK adapters.
- `kiasumiles/agent_contract.py` is the agent-facing contract: tool descriptions, accepted categories, and display rules.
- `kiasumiles/engine/` owns merchant matching and card ranking.
- `kiasumiles/data/` owns bundled CSV loading.

## Commands

- Run tests with `.venv/bin/python -m pytest`.
- Run the hosted MCP server locally with `.venv/bin/kiasumiles-hosted`.
- Check packaging metadata with `.venv/bin/python -m pip show kiasumiles-mcp`.

## Agent Behavior

- Do not show users `card_id`, MCC codes, or raw technical fields unless they ask for diagnostics.
- Prefer `cap_summary` when displaying recommendation caps.
- If `wallet_configured` is false, ask which cards the user carries before giving a final recommendation.
- Treat `routing_note` and `low_confidence_note` as user-visible caveats.
