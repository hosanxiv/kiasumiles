#!/usr/bin/env python3
"""Run one tiny read-only query against the KiasuMiles Supabase database."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable, Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


SUPABASE_URL_ENV = "KIASUMILES_SUPABASE_URL"
SUPABASE_KEY_ENV = "KIASUMILES_SUPABASE_SERVICE_ROLE_KEY"
TIMEOUT_SECONDS = 15


class KeepAliveError(RuntimeError):
    """A safe-to-print keep-awake failure that never contains credentials."""


def query_supabase(
    supabase_url: str,
    service_role_key: str,
    *,
    opener: Callable[..., Any] = urlopen,
) -> None:
    """Select one identifier through Supabase's Data API without changing data."""
    base_url = supabase_url.strip().rstrip("/")
    parsed_url = urlparse(base_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise KeepAliveError("Supabase URL must be a valid HTTPS URL.")
    if not service_role_key.strip():
        raise KeepAliveError("Supabase credentials are not configured.")

    query = urlencode({"select": "card_id", "limit": 1})
    request = Request(
        f"{base_url}/rest/v1/card_rules?{query}",
        headers={
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
            "Accept": "application/json",
            "User-Agent": "kiasumiles-supabase-keep-awake/1.0",
        },
        method="GET",
    )

    try:
        with opener(request, timeout=TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise KeepAliveError(
            f"Supabase keep-awake query failed with HTTP {exc.code}."
        ) from None
    except (URLError, TimeoutError):
        raise KeepAliveError("Supabase keep-awake query could not reach the database.") from None
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise KeepAliveError("Supabase keep-awake query returned invalid JSON.") from None

    if not isinstance(payload, list) or not payload:
        raise KeepAliveError("Supabase keep-awake query returned no card-rule rows.")


def main(
    environ: Mapping[str, str] | None = None,
    *,
    opener: Callable[..., Any] = urlopen,
) -> int:
    env = os.environ if environ is None else environ
    supabase_url = env.get(SUPABASE_URL_ENV, "").strip()
    service_role_key = env.get(SUPABASE_KEY_ENV, "").strip()

    if not supabase_url or not service_role_key:
        print("Supabase credentials are not configured.", file=sys.stderr)
        return 1

    try:
        query_supabase(supabase_url, service_role_key, opener=opener)
    except KeepAliveError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("Supabase keep-awake query succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
