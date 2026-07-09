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

HOSTED_DISPLAY_RULES: tuple[str, ...] = (
    "Use kiasumiles_lookup for Singapore card and merchant recommendations when this hosted MCP server is available.",
    "Before the first lookup in a conversation, ask which cards the user carries if the client has not already supplied a card stack.",
    "Ask the user which banks they use before listing cards, then call kiasumiles_list_cards once per bank.",
    "Keep wallet data client-side. Pass the user's card IDs in the cards parameter for each lookup or stack recommendation.",
    "Never show card_id values, MCC codes, or raw technical fields unless the user asks for diagnostics.",
    "Display recommendations with card name, earn_rate_mpd, cap_summary, and reason_summary.",
    "If the user has not provided cards, ask which cards they carry before making a final recommendation.",
    "Treat routing_note and low_confidence_note as user-visible caveats.",
    "Use kiasumiles_recommend_stack when the user asks whether their current card stack has weak categories.",
    "Do not present kiasumiles_recommend_stack as a card acquisition recommender; hosted recommendations are scoped to cards supplied in the current request.",
)

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

Do not call this tool until you have a card stack for this request. If the client has not
already supplied cards, ask which cards the user carries first. Use kiasumiles_list_cards
to map the user's card names to stable card IDs, then call kiasumiles_lookup with those IDs.

Pass the user's exact merchant name. Extract outlet and channel from natural language if present.
If the merchant is not found, pass category when context makes it obvious.
Accepted values: dining, grocery, transport, petrol, pharmacy, hotel, airlines, shopping.

Present card name, earn_rate_mpd, cap_summary, and reason_summary. Use gotchas to warn about
wrong payment channel, merchant-only bonus rules, minimum spend, and cap constraints. Never show
raw card IDs, MCC codes, or technical fields unless the user asks for diagnostics.""",
    "kiasumiles_recommend_stack": """Analyze a stateless wallet card list for weak categories.

Use this when the user asks whether their current card stack is good or what weak categories exist.
The cards parameter is required for hosted usage and is not stored. This hosted tool only evaluates
cards supplied in the current request; it does not suggest cards outside that request.
If the client has not already supplied cards, ask which cards the user carries first.

Present covered and weak categories. Never show raw card IDs to the user.""",
    "kiasumiles_data_version": """Return the current KiasuMiles data version and row counts for diagnostics and freshness checks.""",
    "kiasumiles_agent_guide": """Return concise hosted integration guidance for agents. Use this for diagnostics, installation checks, or when an agent needs presentation rules.""",
}

LOCAL_DISPLAY_RULES: tuple[str, ...] = (
    "Use kiasumiles_configure once when the user sets up or changes their wallet.",
    "Use kiasumiles_lookup for merchant recommendations; the saved local wallet is added automatically.",
    "Use kiasumiles_get_wallet when the user asks which cards are saved.",
    "Ask which banks the user uses before listing cards, then call kiasumiles_list_cards once per bank.",
    "Never show card IDs, MCC codes, wallet paths, or raw technical fields unless the user asks for diagnostics.",
    "Display recommendations with card name, earn_rate_mpd, cap_summary, and reason_summary.",
    "Treat routing_note and low_confidence_note as user-visible caveats.",
)

LOCAL_TOOL_DESCRIPTIONS: dict[str, str] = {
    "kiasumiles_list_cards": """List supported Singapore credit cards for local wallet setup.

Ask which banks the user has cards with first, then call this once per bank. Present card names
only. Do not expose internal card IDs.""",
    "kiasumiles_configure": """Save or replace the user's KiasuMiles wallet on this device.

Use this after matching the card names the user carries. Include Amaze when mentioned. Confirm
the saved card names in plain English. The hosted service does not store this wallet.""",
    "kiasumiles_get_wallet": """Show the card names saved in the local KiasuMiles wallet.""",
    "kiasumiles_lookup": """Recommend the best saved card for a Singapore merchant.

The local wallet is attached automatically. Pass the exact merchant name plus outlet, channel,
or category only when the user provides them. Never ask the user to repeat their saved cards.""",
    "kiasumiles_recommend_stack": """Review weak categories in the locally saved wallet.""",
    "kiasumiles_data_version": """Return the current hosted card and merchant data version.""",
    "kiasumiles_agent_guide": """Return guidance for the persistent local KiasuMiles workflow.""",
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


def local_agent_guide() -> dict:
    return {
        "name": "KiasuMiles Local",
        "summary": "Local wallet persistence with live hosted KiasuMiles recommendations.",
        "runtime": {
            "transport": "stdio MCP",
            "query_time_network": True,
            "wallet_stored_locally": True,
            "wallet_stored_on_server": False,
        },
        "display_rules": list(LOCAL_DISPLAY_RULES),
        "accepted_categories": dict(CATEGORY_MCC),
        "tools": [
            {
                "name": name,
                "description": description.splitlines()[0],
            }
            for name, description in LOCAL_TOOL_DESCRIPTIONS.items()
        ],
    }
