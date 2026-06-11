# KiasuMiles Context

## Domain Terms

- **KiasuMiles**: Local-first MCP server that recommends the best Singapore credit card for a merchant.
- **Merchant**: User-facing business name, optionally narrowed by outlet and payment channel.
- **MCC**: Merchant category code used by card issuers to decide bonus eligibility.
- **Card Rule**: One supported card's earn-rate logic, caps, eligibility MCCs, channel limits, merchant limits, and caveats.
- **Wallet**: The user's saved card IDs in `~/.kiasumiles/wallet.yaml`.
- **Recommendation**: A ranked card result with display-ready earn rate, cap summary, caveat, and verification metadata.
- **Agent Contract**: The tool descriptions and display rules that teach MCP clients how to call and present KiasuMiles.
- **MCP Adapter**: The FastMCP registration layer in `kiasumiles/server.py`.
- **Tool Handler**: Reusable Python functions in `kiasumiles/tools.py` that implement KiasuMiles behavior without depending on MCP transport.

## Architectural Direction

KiasuMiles should keep query-time recommendations offline and local. Hosted or app-store surfaces should adapt the existing tool handlers rather than reimplement card routing, wallet behavior, or merchant matching.

The MCP adapter should stay thin: register tools, attach descriptions, and run stdio. Domain behavior belongs in the data, engine, and tool handler modules.
