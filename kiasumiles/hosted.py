from __future__ import annotations

import json
import os
import time
from collections import defaultdict, deque
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse

from .agent_contract import HOSTED_TOOL_DESCRIPTIONS, hosted_agent_guide
from .landing import render_landing
from . import tools


STATIC_DIR = Path(__file__).resolve().parent / "static" / "kiasumiles"


def _port() -> int:
    return int(os.environ.get("KIASUMILES_PORT", "8000"))


mcp = FastMCP(
    "KiasuMiles Hosted",
    host=os.environ.get("KIASUMILES_HOST", "0.0.0.0"),
    port=_port(),
    streamable_http_path=os.environ.get("KIASUMILES_MCP_PATH", "/mcp"),
    stateless_http=True,
)


def kiasumiles_list_cards(bank: str | None = None) -> dict:
    return tools.list_cards(bank)


def kiasumiles_lookup(
    merchant: str,
    cards: list[str],
    outlet: str | None = None,
    channel: str | None = None,
    category: str | None = None,
) -> dict:
    return tools.lookup_hosted(merchant, cards, outlet, channel, category)


def kiasumiles_recommend_stack(cards: list[str], top_n: int = 3) -> dict:
    return tools.recommend_stack(cards, top_n)


def kiasumiles_data_version() -> dict:
    return tools.data_version()


def kiasumiles_agent_guide() -> dict:
    return hosted_agent_guide()


for _name, _description in HOSTED_TOOL_DESCRIPTIONS.items():
    _tool = globals()[_name]
    _tool.__doc__ = _description
    globals()[_name] = mcp.tool()(_tool)


@mcp.custom_route("/", methods=["GET"])
async def landing(_: Request) -> HTMLResponse:
    version = tools.data_version()
    return HTMLResponse(render_landing(version))


@mcp.custom_route("/kiasumiles/hero.png", methods=["GET"])
async def hero_image(_: Request) -> FileResponse:
    return FileResponse(STATIC_DIR / "hero.png", media_type="image/png")


@mcp.custom_route("/kiasumiles/product-demo-60s.mp4", methods=["GET"])
async def product_demo(_: Request) -> FileResponse:
    return FileResponse(STATIC_DIR / "product-demo-60s.mp4", media_type="video/mp4")


@mcp.custom_route("/privacy", methods=["GET"])
async def privacy(_: Request) -> HTMLResponse:
    return HTMLResponse(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>KiasuMiles Privacy Policy</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; color: #151515; background: #faf9f6; }
    main { max-width: 760px; margin: 0 auto; padding: 56px 24px; }
    h1 { font-size: 36px; margin: 0 0 16px; }
    h2 { margin-top: 32px; }
    p, li { font-size: 17px; line-height: 1.55; }
    a { color: #0f5b4f; }
  </style>
</head>
<body>
  <main>
    <h1>Privacy Policy</h1>
    <p>Last updated: 10 June 2026</p>
    <p>KiasuMiles provides Singapore credit-card miles recommendations through a hosted MCP service.</p>
    <h2>Wallet Data</h2>
    <p>KiasuMiles does not store user wallet data. When a client requests a recommendation, it may send card IDs for that request only so the service can rank cards against current rules.</p>
    <h2>Request Data</h2>
    <p>Requests may include merchant names, payment channel hints, and card IDs. The service uses this data only to compute recommendations and diagnostics for that request.</p>
    <h2>Logs</h2>
    <p>Operational logs are used to maintain reliability and debug errors. We aim to avoid logging raw wallet payloads or sensitive personal information.</p>
    <h2>Data Sources and Updates</h2>
    <p>KiasuMiles maintains its own merchant and card-rule database and may update it centrally without requiring users to reinstall software.</p>
    <h2>Contact</h2>
    <p>Questions or correction requests can be sent to <a href="mailto:hello@theaiburrow.xyz">hello@theaiburrow.xyz</a>.</p>
  </main>
</body>
</html>"""
    )


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", **tools.data_version()})


@mcp.custom_route("/robots.txt", methods=["GET"])
async def robots(_: Request) -> PlainTextResponse:
    return PlainTextResponse("User-agent: *\nDisallow: /mcp\n")


class RateLimitMiddleware:
    """Per-IP sliding-window rate limit on the MCP endpoint.

    In-memory, so on serverless each warm instance keeps its own window —
    a determined scraper can exceed the global limit across instances, but
    casual abuse and runaway clients are stopped without any shared state.
    Set KIASUMILES_RATE_LIMIT_REQUESTS=0 to disable.
    """

    def __init__(self, app, max_requests: int | None = None, window_seconds: int | None = None):
        self.app = app
        self.max_requests = max_requests if max_requests is not None else int(
            os.environ.get("KIASUMILES_RATE_LIMIT_REQUESTS", "30")
        )
        self.window_seconds = window_seconds if window_seconds is not None else int(
            os.environ.get("KIASUMILES_RATE_LIMIT_WINDOW_SECONDS", "60")
        )
        self._history: dict[str, deque[float]] = defaultdict(deque)

    def _client_ip(self, scope) -> str:
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        forwarded = headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        client = scope.get("client")
        return client[0] if client else "unknown"

    def _is_limited(self, ip: str) -> bool:
        now = time.time()
        history = self._history[ip]
        cutoff = now - self.window_seconds
        while history and history[0] < cutoff:
            history.popleft()
        if len(history) >= self.max_requests:
            return True
        history.append(now)
        return False

    async def __call__(self, scope, receive, send):
        is_mcp = scope.get("type") == "http" and scope.get("path", "").startswith("/mcp")
        if is_mcp and self.max_requests > 0 and self._is_limited(self._client_ip(scope)):
            body = json.dumps({
                "error": "rate_limited",
                "detail": f"Limit is {self.max_requests} requests per {self.window_seconds}s. Try again shortly.",
            }).encode()
            await send({
                "type": "http.response.start",
                "status": 429,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"retry-after", str(self.window_seconds).encode()),
                ],
            })
            await send({"type": "http.response.body", "body": body})
            return
        await self.app(scope, receive, send)


app = RateLimitMiddleware(mcp.streamable_http_app())


def main() -> None:
    mcp.run("streamable-http")


if __name__ == "__main__":
    main()
