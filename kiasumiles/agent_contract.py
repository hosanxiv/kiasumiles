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

CONVERSATION_FLOW = (
    "Reuse cards and resolved names already supplied in this conversation. Ask which cards the user "
    "has only when missing; offer banks as a fallback. Fetch the supported list once for multiple "
    "banks and filter internally. Accept unambiguous named cards without reconfirming the full stack; "
    "ask the user to choose when a name has multiple variants or they supplied only banks. "
    "If payment method is unspecified, compare methods in one call and briefly show physical-card "
    "and mobile-wallet options. Ask only if missing information materially changes the answer and "
    "cannot be covered by alternatives. Treat spend progress as optional and show bonus conditions "
    "and guaranteed fallbacks when it is unknown. Lead with card, rate and essential conditions, "
    "including uncertainty and fallback where relevant. Expand only on request. "
    "Do not repeat setup or discovery for each purchase or promise memory across conversations."
)

HOSTED_DISPLAY_RULES: tuple[str, ...] = (
    CONVERSATION_FLOW,
    "Use kiasumiles_lookup for Singapore card and merchant recommendations when this hosted MCP server is available.",
    "Before the first lookup in a conversation, ask which cards the user carries if the client has not already supplied a card stack.",
    "Ask which cards the user carries; offer banks as a fallback if they do not know the names. Reuse cards already supplied in the conversation. Clarify ambiguous variants only; do not reconfirm an explicit, unambiguous card list.",
    "Keep wallet data client-side. Pass the user's card IDs in the cards parameter for each lookup or stack recommendation.",
    "Never show card_id values, MCC codes, or raw technical fields unless the user asks for diagnostics.",
    "Display recommendations with card name, earn_rate_mpd, cap_summary, and reason_summary.",
    "If the user has not provided cards, ask which cards they carry before making a final recommendation.",
    "Treat routing_note and low_confidence_note as user-visible caveats.",
    "Treat recommendations as guaranteed fallbacks when spend progress is unknown. Show conditional_recommendations separately and state their conditions.",
    "When the user provides a transaction amount, pass amount_sgd and display estimated_miles.",
    "Use kiasumiles_recommend_stack when the user asks whether their current card stack has weak categories.",
    "Do not present kiasumiles_recommend_stack as a card acquisition recommender; hosted recommendations are scoped to cards supplied in the current request.",
)

HOSTED_TOOL_DESCRIPTIONS: dict[str, str] = {
    "kiasumiles_list_cards": """List supported Singapore credit cards and their stable card IDs for hosted MCP requests.

Skip bank questions when cards are already named. Reuse mappings from this conversation.
For one bank, filter by bank. For multiple banks or named cards, call once without bank and
filter internally. Show relevant cards only. Clarify ambiguous variants rather than guessing.

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
Use channel="app" only for an order placed in the merchant's own app. For CHAGEE,
this distinction is required for the yuu bonus; website or tap payments are not equivalent.
If the merchant is not found, pass category when context makes it obvious.
Accepted values: dining, grocery, transport, petrol, pharmacy, hotel, airlines, shopping.

Pass is_recurring=true for confirmed automatic payments authorised once and charged
at fixed intervals; false for a confirmed one-off purchase. Omit when unknown.
Pass revolution_ega_eligible=true only after confirming at least
S$50,000 average daily SGD deposits in the user's sole HSBC Everyday Global Account
for the posting month; joint accounts do not qualify. Otherwise omit this flag.
For Revolution, supply revolution_prior_eligible_spend_sgd only when the user confirms
the bonus-eligible amount already posted in that calendar month across primary and
supplementary cards, excluding this purchase. Omit if unknown; never assume zero.
Standard Chartered recurring payments do not earn rewards. Do not infer recurring
status merely because the user shops with the same merchant regularly.

For DBS Vantage, pass vantage_miles_selected=true only when the user confirms Miles
is selected in digibank; false for Cashback, or omit when unknown. Do not assume the
default is still selected. Cashback automatically consumes points next month.

For PRVI Miles and BOC Elite Miles, supply transaction_currency and payment_gateway_country only when
confirmed (uppercase currency and country codes, e.g. MYR and MY). The processing
country is not necessarily the merchant's location. Omit unknown details; never
promise the overseas or regional rate based on foreign currency alone.

For Chocolate Visa, pass chocolate_eligible=true only when the user confirms the card
is linked and verified on HeyMax and both accounts use the same email. From October 2026, also require confirmation of at least S$5,000
prior-month average daily SGD balance; September 2026 has no balance check. Pass false
when ineligible; omit when unknown. Never infer eligibility from owning the card.
When requires_clarification is returned, ask for the outlet/payment details instead of guessing.
For Smart, pass smart_statement_spend_sgd only for user-confirmed total eligible spending
in this statement month, including this purchase and supplementary cards. Do not use
a forecast, calendar-month total, or the purchase amount alone. Omit when unknown.
For PPS cards, pps_prior_spend_sgd maps each card ID to its confirmed prior eligible
calendar-month SGD-equivalent spending, excluding this purchase. Use only the same
currency bucket (SGD or foreign currency); never combine cards or currency totals.
If pps_sia_group_eligible=true, use the separate qualifying SIA Group spending bucket
instead. Confirm direct SGD purchase and Singapore departure for flights; Pelago
digital-wallet purchases do not qualify. Omit the flag if uncertain. Omit unknown totals.
PPS estimates with unknown spending are lower/upper bounds, not exact awards.
The monthly calculation may complete an earlier partial S$10 block. Explain this
when the incremental miles appear large relative to a small purchase.

Present card name, earn_rate_mpd, cap_summary, and reason_summary. Use gotchas to warn about
wrong payment channel, merchant-only bonus rules, minimum spend, and cap constraints. Never show
raw card IDs, MCC codes, or technical fields unless the user asks for diagnostics.

""" + CONVERSATION_FLOW,
    "kiasumiles_compare_payment_methods": """Compare payment methods for the same merchant and supplied card stack.

Use this when payment method is unspecified or the user asks whether to pay by mobile wallet, physical contactless card, online, or
through Amaze. Pass amount_sgd when known. Amaze is compared only when the user supplied it.
For Chocolate, chocolate_eligible requires the card linked and verified on HeyMax
with matching account emails; from October 2026 it also requires prior-month SGD balance eligibility. Omit it when unknown,
or pass false when ineligible.
For Smart, smart_statement_spend_sgd is the user-confirmed eligible statement-month
total including this purchase and supplementary cards; omit if unknown, never forecast it.
PPS comparisons use unknown-spending bounds. Once payment is chosen, use lookup
with the confirmed spending in that payment's applicable monthly bucket.
For DBS Vantage, pass vantage_miles_selected only for the user's confirmed digibank
reward choice (true for Miles, false for Cashback); omit when unknown.
Pass is_recurring for confirmed automatic fixed-interval payments (true), or confirmed
one-off purchases (false). Pass revolution_ega_eligible=true only with confirmed
S$50,000 average daily SGD deposits in a sole HSBC Everyday Global Account for the
posting month; otherwise omit it. Omit recurring-payment status when unknown.
For Revolution, pass revolution_prior_eligible_spend_sgd only for confirmed eligible
spending already posted that calendar month across primary and supplementary cards,
excluding this purchase. Omit if unknown; zero must be confirmed.
Repeated shopping alone is not recurring.
Present the best guaranteed and conditional result for each method with conditions and caveats.
Show a returned message when no recommendation is available; never invent a merchant match.""",
    "kiasumiles_changes_since": """Summarize source-neutral card and merchant rule changes since an ISO date.

Use this when the user asks what changed or whether the data was updated. Present changed_on,
effective_on when present, entity_name, and summary. Do not infer or disclose private sources.""",
    "kiasumiles_recommend_stack": """Analyze a stateless wallet card list for weak categories.

Use this when the user asks whether their current card stack is good or what weak categories exist.
The cards parameter is required for hosted usage and is not stored. This hosted tool only evaluates
cards supplied in the current request; it does not suggest cards outside that request.
If the client has not already supplied cards, ask which cards the user carries first.

Present covered and weak categories. Never show raw card IDs to the user.""",
    "kiasumiles_data_version": """Return record verification dates and row counts. data_version is the newest individual
record verification date, not the last database edit or a full-database review date.
For recent updates, call kiasumiles_changes_since. Never describe all rules as verified
on data_version; individual records may be older.""",
    "kiasumiles_agent_guide": """Return concise hosted integration guidance for agents. Use this for diagnostics, installation checks, or when an agent needs presentation rules.""",
}

LOCAL_DISPLAY_RULES: tuple[str, ...] = (
    "Reuse saved cards. Clarify ambiguous variants only. Keep answers brief with essential conditions and uncertainty; do not ask for optional spend progress.",
    "Use kiasumiles_configure once when the user sets up or changes their wallet.",
    "Use kiasumiles_lookup for merchant recommendations; the saved local wallet is added automatically.",
    "Use kiasumiles_get_wallet when the user asks which cards are saved.",
    "Skip bank questions when cards are named. List cards once for multiple banks and filter internally.",
    "Never show card IDs, MCC codes, wallet paths, or raw technical fields unless the user asks for diagnostics.",
    "Display recommendations with card name, earn_rate_mpd, cap_summary, and reason_summary.",
    "Treat routing_note and low_confidence_note as user-visible caveats.",
)

LOCAL_TOOL_DESCRIPTIONS: dict[str, str] = {
    "kiasumiles_list_cards": """List supported Singapore credit cards for local wallet setup.

Reuse known mappings. Ask for banks only if the user does not know their card names.
For multiple banks, list once and filter internally. Present relevant card names only.""",
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
