from __future__ import annotations

import json
import os
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://kiasumiles.space"
JsonTransport = Callable[[str, str, dict[str, Any] | None], dict[str, Any]]


class HostedServiceError(RuntimeError):
    pass


def request_json(
    base_url: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        data=body,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "KiasuMiles-Local/1.0.2",
        },
    )
    try:
        with urlopen(request, timeout=10) as response:
            decoded = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise HostedServiceError("The KiasuMiles hosted service is unavailable.") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HostedServiceError("The KiasuMiles hosted service returned an invalid response.") from exc
    if not isinstance(decoded, dict):
        raise HostedServiceError("The KiasuMiles hosted service returned an invalid response.")
    return decoded


class HostedClient:
    def __init__(
        self,
        base_url: str | None = None,
        transport: JsonTransport | None = None,
    ) -> None:
        self.base_url = base_url or os.environ.get("KIASUMILES_BASE_URL", DEFAULT_BASE_URL)
        self._transport = transport

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self._transport is not None:
            return self._transport(method, path, payload)
        return request_json(self.base_url, method, path, payload)

    def list_cards(self, bank: str | None = None) -> dict[str, Any]:
        path = "/api/chatgpt/cards"
        if bank:
            path = f"{path}?{urlencode({'bank': bank})}"
        return self._request("GET", path)

    def inspect_wallet(self, cards: list[str]) -> dict[str, list[str]]:
        result = self._request(
            "POST",
            "/api/chatgpt/recommend-stack",
            {"cards": cards, "top_n": 1},
        )
        return {
            "cards": list(result.get("wallet_cards") or []),
            "unmatched_cards": list(result.get("unmatched_cards") or []),
        }

    def lookup(
        self,
        merchant: str,
        cards: list[str],
        outlet: str | None = None,
        channel: str | None = None,
        category: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"merchant": merchant, "cards": cards}
        for key, value in {
            "outlet": outlet,
            "channel": channel,
            "category": category,
        }.items():
            if value is not None:
                payload[key] = value
        return self._request("POST", "/api/chatgpt/lookup", payload)

    def recommend_stack(self, cards: list[str], top_n: int = 3) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/chatgpt/recommend-stack",
            {"cards": cards, "top_n": top_n},
        )

    def data_version(self) -> dict[str, Any]:
        return self._request("GET", "/health")
