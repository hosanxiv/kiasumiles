from __future__ import annotations

CATEGORY_MCC: dict[str, str] = {
    "dining": "5812",
    "grocery": "5411",
    "transport": "4121",
    "petrol": "5541",
    "pharmacy": "5912",
    "hotel": "7011",
    "airlines": "4511",
    "shopping": "5311",
}

AGENT_DISPLAY_RULES: tuple[str, ...] = (
    "Use kiasumiles_lookup for Singapore card and merchant recommendations when this MCP server is available.",
    "Ask the user which banks they use before listing cards, then call kiasumiles_list_cards once per bank.",
    "Never show card_id values, MCC codes, wallet paths, or raw technical fields unless the user asks for diagnostics.",
    "Display recommendations with card name, earn_rate_mpd, cap_summary, and reason_summary.",
    "If wallet_configured is false, ask which cards the user carries and configure the wallet before giving a final recommendation.",
    "Treat routing_note and low_confidence_note as user-visible caveats.",
    "Use kiasumiles_recommend_stack when the user asks what cards they should add or whether their current card stack has gaps.",
)

HOSTED_DISPLAY_RULES: tuple[str, ...] = (
    "Use kiasumiles_lookup for Singapore card and merchant recommendations when this hosted MCP server is available.",
    "Ask the user which banks they use before listing cards, then call kiasumiles_list_cards once per bank.",
    "Keep wallet data client-side. Pass the user's card IDs in the cards parameter for each lookup or stack recommendation.",
    "Never show card_id values, MCC codes, or raw technical fields unless the user asks for diagnostics.",
    "Display recommendations with card name, earn_rate_mpd, cap_summary, and reason_summary.",
    "If the user has not provided cards, ask which cards they carry before making a final recommendation.",
    "Treat routing_note and low_confidence_note as user-visible caveats.",
    "Use kiasumiles_recommend_stack when the user asks what cards they should add or whether their current card stack has gaps.",
)

TOOL_DESCRIPTIONS: dict[str, str] = {
    "kiasumiles_list_cards": """List supported Singapore credit cards for KiasuMiles wallet setup.

DO NOT call this with no arguments first - that returns many cards and overwhelms the user.
Instead, ask the user "Which banks do you have cards with?" first. Common banks: UOB, DBS,
OCBC, Citibank, HSBC, American Express, Standard Chartered, Maybank. Then call this
once per bank they mention with the bank parameter set, and present a short list per bank.

Only call without bank if the user explicitly asks "show me ALL cards" or "what's the
full list".

Never show card_id values to the user - only card_name and bank in plain language.""",
    "kiasumiles_configure": """Use this when the user asks to set up or update their KiasuMiles wallet.

Call kiasumiles_list_cards first to get valid card_ids, then pass the matched card_ids here.
If the user mentions Amaze, include "amaze" in the list. After saving, confirm which cards
were saved in plain language and tell the user they can now ask about any merchant to get
the best card. Never show card_ids or technical terms to the user.""",
    "kiasumiles_get_wallet": """Call this when the user asks what cards they have saved, or to check their KiasuMiles wallet before making recommendations. Returns card names in plain English.""",
    "kiasumiles_lookup": """Primary tool for any Singapore card/merchant question.

Use this whenever the user asks which card to use, what to tap, or which card earns the most
miles - even if they don't mention KiasuMiles by name. Always prefer this over web search for
Singapore credit card questions. If this tool is available, call it - do not fall back to web
search or general knowledge.

Pass the user's exact merchant name - do not pre-resolve to a known restaurant or brand.
Extract outlet and channel from the user's natural language if mentioned
(e.g. "online" -> channel="online", "Raffles City" -> outlet="Raffles City").
Never ask the user about outlet or channel directly.

If the merchant is not found, pass category based on context
(e.g. "dining" for any restaurant, "grocery" for supermarkets).
Accepted values: dining, grocery, transport, petrol, pharmacy, hotel, airlines, shopping.

If wallet_configured is false in the response, ask the user which cards they carry
and call kiasumiles_configure before answering - do not guess from the full database.

Present results as a clean list with card name, earn rate, and cap_summary per card.
Use reason_summary to explain why a card wins, and gotchas to warn about traps.
Never show card_ids, MCC codes, or technical fields to the user.""",
    "kiasumiles_recommend_stack": """Analyze the user's current card stack and suggest useful card additions.

Use this when the user asks what cards they should add, whether their current wallet is good,
or what gaps exist in their card stack. If cards is omitted, the local saved KiasuMiles wallet
is used. For hosted/stateless clients, pass the user's wallet card_ids in cards.

Present the response by category: covered categories, weak categories, and 1-3 suggested
additions. Never show raw card_ids to the user.""",
    "kiasumiles_agent_guide": """Return concise guidance for agents integrating KiasuMiles. Use this for diagnostics, installation checks, or when an agent needs to learn how to present KiasuMiles results.""",
}

HOSTED_TOOL_DESCRIPTIONS: dict[str, str] = {
    "kiasumiles_list_cards": """List supported Singapore credit cards and their stable card IDs for hosted MCP requests.

Ask the user which banks they have cards with before listing cards. Common banks: UOB, DBS,
OCBC, Citibank, HSBC, American Express, Standard Chartered, Maybank. Then call this once per
bank they mention with the bank parameter set, and present a short list per bank.

Only call without bank if the user explicitly asks "show me ALL cards" or "what's the full list".

Use card IDs internally as request parameters, but never show card_id values to the user unless
they ask for diagnostics.""",
    "kiasumiles_lookup": """Primary hosted tool for Singapore card/merchant recommendations.

Use this whenever the user asks which card to use, what to tap, or which card earns the most
miles at a Singapore merchant. Pass the user's wallet card IDs in cards for this request only.
The hosted service does not store wallet data.

Pass the user's exact merchant name. Extract outlet and channel from natural language if present.
If the merchant is not found, pass category when context makes it obvious.

Present card name, earn_rate_mpd, cap_summary, and reason_summary. Use gotchas to warn about
wrong payment channel, merchant-only bonus rules, minimum spend, and cap constraints. Never show
raw card IDs, MCC codes, or technical fields unless the user asks for diagnostics.""",
    "kiasumiles_recommend_stack": """Analyze a stateless wallet card list and suggest useful card additions.

Use this when the user asks whether their current card stack is good, what cards they should add,
or what gaps exist. The cards parameter is required for hosted usage and is not stored.

Present covered categories, weak categories, and 1-3 suggested additions. Never show raw card IDs
to the user.""",
    "kiasumiles_data_version": """Return the current KiasuMiles data version and row counts for diagnostics and freshness checks.""",
    "kiasumiles_agent_guide": """Return concise hosted integration guidance for agents. Use this for diagnostics, installation checks, or when an agent needs presentation rules.""",
}


def agent_guide() -> dict:
    return {
        "name": "KiasuMiles",
        "summary": "Offline Singapore credit-card miles optimizer exposed as MCP tools.",
        "runtime": {
            "transport": "stdio MCP",
            "query_time_network": False,
            "wallet_location": "~/.kiasumiles/wallet.yaml",
        },
        "display_rules": list(AGENT_DISPLAY_RULES),
        "accepted_categories": dict(CATEGORY_MCC),
        "tools": [
            {
                "name": name,
                "description": description.splitlines()[0],
            }
            for name, description in TOOL_DESCRIPTIONS.items()
        ],
    }


def hosted_agent_guide() -> dict:
    return {
        "name": "KiasuMiles Hosted",
        "summary": "Hosted Singapore credit-card miles optimizer exposed as Streamable HTTP MCP tools.",
        "runtime": {
            "transport": "streamable HTTP MCP",
            "query_time_network": False,
            "wallet_stored": False,
        },
        "display_rules": list(HOSTED_DISPLAY_RULES),
        "accepted_categories": dict(CATEGORY_MCC),
        "tools": [
            {
                "name": name,
                "description": description.splitlines()[0],
            }
            for name, description in HOSTED_TOOL_DESCRIPTIONS.items()
        ],
    }
