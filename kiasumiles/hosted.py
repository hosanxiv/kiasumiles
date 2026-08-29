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
from .chatgpt_action import register_chatgpt_action_routes
from . import tools


STATIC_DIR = Path(__file__).resolve().parent / "static" / "kiasumiles"
PROOF_ASSETS = {
    "kiasumiles-real-life-720.webp": "image/webp",
    "kiasumiles-real-life-1460.webp": "image/webp",
    "kiasumiles-real-life-1460.jpg": "image/jpeg",
    "kiasumiles-cold-storage-chat.jpg": "image/jpeg",
}
IMMUTABLE_CACHE_CONTROL = "public, max-age=31536000, immutable"
REVALIDATE_CACHE_CONTROL = "public, max-age=0, must-revalidate"


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
    amount_sgd: float | None = None,
) -> dict:
    return tools.lookup_hosted(merchant, cards, outlet, channel, category, amount_sgd)


def kiasumiles_compare_payment_methods(
    merchant: str,
    cards: list[str],
    amount_sgd: float | None = None,
    outlet: str | None = None,
    category: str | None = None,
) -> dict:
    return tools.compare_payment_methods(merchant, cards, amount_sgd, outlet, category)


def kiasumiles_changes_since(since: str, limit: int = 20) -> dict:
    return tools.changes_since(since, limit)


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


register_chatgpt_action_routes(mcp)


@mcp.custom_route("/", methods=["GET"])
async def landing(_: Request) -> HTMLResponse:
    return HTMLResponse(
        (STATIC_DIR / "index.html").read_text(encoding="utf-8"),
        headers={"Cache-Control": REVALIDATE_CACHE_CONTROL},
    )


@mcp.custom_route("/favicon.svg", methods=["GET"])
async def favicon(_: Request) -> FileResponse:
    return FileResponse(
        STATIC_DIR / "favicon.svg",
        media_type="image/svg+xml",
        headers={"Cache-Control": IMMUTABLE_CACHE_CONTROL},
    )


@mcp.custom_route("/kiasumiles/hero.png", methods=["GET"])
async def hero_image(_: Request) -> FileResponse:
    return FileResponse(STATIC_DIR / "hero.png", media_type="image/png")


@mcp.custom_route("/kiasumiles/product-demo-60s.mp4", methods=["GET"])
async def product_demo(_: Request) -> FileResponse:
    return FileResponse(STATIC_DIR / "product-demo-60s.mp4", media_type="video/mp4")


@mcp.custom_route("/kiasumiles/assets/proof/{filename}", methods=["GET"])
async def proof_asset(request: Request) -> FileResponse | PlainTextResponse:
    filename = request.path_params["filename"]
    media_type = PROOF_ASSETS.get(filename)
    if media_type is None:
        return PlainTextResponse("Not found", status_code=404)
    return FileResponse(
        STATIC_DIR / "assets" / "proof" / filename,
        media_type=media_type,
        headers={"Cache-Control": IMMUTABLE_CACHE_CONTROL},
    )


@mcp.custom_route("/assets/logos/{filename:path}", methods=["GET"])
@mcp.custom_route("/kiasumiles/assets/logos/{filename:path}", methods=["GET"])
async def logo_asset(request: Request) -> FileResponse:
    filename = request.path_params["filename"]
    path = (STATIC_DIR / "assets" / "logos" / filename).resolve()
    logos_dir = (STATIC_DIR / "assets" / "logos").resolve()
    if not path.is_file() or logos_dir not in path.parents:
        return PlainTextResponse("Not found", status_code=404)
    return FileResponse(path)


@mcp.custom_route("/privacy", methods=["GET"])
async def privacy(_: Request) -> HTMLResponse:
    return HTMLResponse(
        (STATIC_DIR / "privacy.html").read_text(encoding="utf-8"),
        headers={"Cache-Control": REVALIDATE_CACHE_CONTROL},
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
