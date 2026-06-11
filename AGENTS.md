## Project

KiasuMiles is a local-first Python MCP server for Singapore credit-card miles recommendations.
Keep the query path offline: no web calls from lookup, wallet, merchant matching, or card ranking.

## Architecture

- `kiasumiles/server.py` is the FastMCP adapter. Keep it thin.
- `kiasumiles/tools.py` contains reusable tool handlers for Codex, tests, and future hosted ChatGPT Apps SDK adapters.
- `kiasumiles/agent_contract.py` is the agent-facing contract: tool descriptions, accepted categories, and display rules.
- `kiasumiles/engine/` owns merchant matching, wallet storage, and card ranking.
- `kiasumiles/data/` owns bundled CSV loading.

## Commands

- Run tests with `.venv/bin/python -m pytest`.
- Run a local MCP server with `.venv/bin/kiasumiles-mcp`.
- Check packaging metadata with `.venv/bin/python -m pip show kiasumiles-mcp`.

## Agent Behavior

- Do not show users `card_id`, MCC codes, wallet paths, or raw technical fields unless they ask for diagnostics.
- Prefer `cap_summary` when displaying recommendation caps.
- If `wallet_configured` is false, configure the wallet before giving a final recommendation.
- Treat `routing_note` and `low_confidence_note` as user-visible caveats.
