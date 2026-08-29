from __future__ import annotations

import os
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from . import tools


_PUBLIC_FORBIDDEN_KEYS = {"card_id", "mcc", "mcc_category", "reason_codes"}


def _public_base_url() -> str:
    return os.environ.get("KIASUMILES_PUBLIC_BASE_URL", "https://kiasumiles.space").rstrip("/")


def _public_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _public_json(child)
            for key, child in value.items()
            if key not in _PUBLIC_FORBIDDEN_KEYS
        }
    if isinstance(value, list):
        return [_public_json(child) for child in value]
    return value


def _card_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {"amaze": "amaze"}
    for card in tools._loader.cards():
        lookup[card.card_id.lower()] = card.card_id
        lookup[card.card_name.lower()] = card.card_id
    return lookup


def _resolve_card_inputs(cards: list[Any]) -> tuple[list[str], list[str]]:
    lookup = _card_lookup()
    resolved: list[str] = []
    unmatched: list[str] = []

    for raw in cards:
        if not isinstance(raw, str):
            unmatched.append(str(raw))
            continue
        normalized = raw.strip().lower()
        card_id = lookup.get(normalized)
        if card_id:
            resolved.append(card_id)
        else:
            unmatched.append(raw)

    return resolved, unmatched


def _openapi_spec() -> dict:
    base_url = _public_base_url()
    card_array_schema = {
        "type": "array",
        "items": {"type": "string"},
        "description": "Names of cards the user says they carry for this request only.",
    }
    lookup_body = {
        "type": "object",
        "required": ["merchant", "cards"],
        "properties": {
            "merchant": {"type": "string"},
            "cards": card_array_schema,
            "outlet": {"type": "string"},
            "channel": {"type": "string", "enum": ["online", "contactless", "mobile_contactless"]},
            "category": {
                "type": "string",
                "enum": ["dining", "grocery", "transport", "petrol", "pharmacy", "hotel", "airlines", "shopping"],
            },
            "amount_sgd": {"type": "number", "exclusiveMinimum": 0},
        },
    }
    stack_body = {
        "type": "object",
        "required": ["cards"],
        "properties": {
            "cards": card_array_schema,
            "top_n": {"type": "integer", "minimum": 1, "maximum": 5, "default": 3},
        },
    }
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "KiasuMiles ChatGPT Action",
            "version": "1.1.0",
            "description": "Stateless Singapore credit-card miles recommendations for cards supplied in the current request.",
        },
        "servers": [{"url": base_url}],
        "paths": {
            "/api/chatgpt/cards": {
                "get": {
                    "operationId": "listCards",
                    "summary": "List supported cards by bank without exposing internal IDs.",
                    "parameters": [
                        {
                            "name": "bank",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "Supported card names"}},
                }
            },
            "/api/chatgpt/lookup": {
                "post": {
                    "operationId": "lookupMerchant",
                    "summary": "Recommend the best supplied card for a merchant.",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": lookup_body}},
                    },
                    "responses": {"200": {"description": "Stateless recommendation result"}},
                }
            },
            "/api/chatgpt/compare-payment-methods": {
                "post": {
                    "operationId": "comparePaymentMethods",
                    "summary": "Compare payment methods for the supplied cards.",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": lookup_body}},
                    },
                    "responses": {"200": {"description": "Payment-method comparison"}},
                }
            },
            "/api/chatgpt/changes": {
                "get": {
                    "operationId": "listRuleChanges",
                    "summary": "List source-neutral rule changes since a date.",
                    "parameters": [
                        {"name": "since", "in": "query", "required": True, "schema": {"type": "string", "format": "date"}},
                        {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20}},
                    ],
                    "responses": {"200": {"description": "Rule change history"}},
                }
            },
            "/api/chatgpt/recommend-stack": {
                "post": {
                    "operationId": "reviewCardStack",
                    "summary": "Review weak categories for the supplied cards.",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": stack_body}},
                    },
                    "responses": {"200": {"description": "Supplied-card stack review"}},
                }
            },
        },
    }


def register_chatgpt_action_routes(mcp) -> None:
    @mcp.custom_route("/api/chatgpt/openapi.json", methods=["GET"])
    async def chatgpt_openapi(_: Request) -> JSONResponse:
        return JSONResponse(_openapi_spec())

    @mcp.custom_route("/api/chatgpt/cards", methods=["GET"])
    async def chatgpt_cards(request: Request) -> JSONResponse:
        result = tools.list_cards(request.query_params.get("bank"))
        cards = [
            {
                "card_name": card["card_name"],
                "bank": card["bank"],
                "network": card["network"],
            }
            for card in result["cards"]
        ]
        return JSONResponse({
            "cards": cards,
            "total": len(cards),
            "filtered_by_bank": result["filtered_by_bank"],
        })

    @mcp.custom_route("/api/chatgpt/lookup", methods=["POST"])
    async def chatgpt_lookup(request: Request) -> JSONResponse:
        body = await request.json()
        cards, unmatched = _resolve_card_inputs(body.get("cards") or [])
        try:
            result = tools.lookup_hosted(
                str(body.get("merchant") or ""),
                cards,
                body.get("outlet"),
                body.get("channel"),
                body.get("category"),
                body.get("amount_sgd"),
            )
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        if unmatched:
            result["unmatched_cards"] = unmatched
        return JSONResponse(_public_json(result))

    @mcp.custom_route("/api/chatgpt/compare-payment-methods", methods=["POST"])
    async def chatgpt_compare_payment_methods(request: Request) -> JSONResponse:
        body = await request.json()
        cards, unmatched = _resolve_card_inputs(body.get("cards") or [])
        try:
            result = tools.compare_payment_methods(
                str(body.get("merchant") or ""),
                cards,
                body.get("amount_sgd"),
                body.get("outlet"),
                body.get("category"),
            )
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        if unmatched:
            result["unmatched_cards"] = unmatched
        return JSONResponse(_public_json(result))

    @mcp.custom_route("/api/chatgpt/changes", methods=["GET"])
    async def chatgpt_changes(request: Request) -> JSONResponse:
        try:
            result = tools.changes_since(
                request.query_params.get("since") or "",
                int(request.query_params.get("limit") or 20),
            )
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        return JSONResponse(_public_json(result))

    @mcp.custom_route("/api/chatgpt/recommend-stack", methods=["POST"])
    async def chatgpt_recommend_stack(request: Request) -> JSONResponse:
        body = await request.json()
        cards, unmatched = _resolve_card_inputs(body.get("cards") or [])
        result = tools.recommend_stack(cards, int(body.get("top_n") or 3))
        if unmatched:
            result["unmatched_cards"] = unmatched
        result["wallet_stored"] = False
        return JSONResponse(_public_json(result))
