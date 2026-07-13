from kiasumiles import hosted
from kiasumiles.agent_contract import HOSTED_TOOL_DESCRIPTIONS
from kiasumiles.tools import lookup_hosted, data_version
from starlette.testclient import TestClient


PROOF_ASSETS = (
    ("kiasumiles-real-life-720.webp", "image/webp"),
    ("kiasumiles-real-life-1460.webp", "image/webp"),
    ("kiasumiles-real-life-1460.jpg", "image/jpeg"),
)


def test_hosted_contract_excludes_local_wallet_tools():
    assert "kiasumiles_configure" not in HOSTED_TOOL_DESCRIPTIONS
    assert "kiasumiles_get_wallet" not in HOSTED_TOOL_DESCRIPTIONS
    assert "kiasumiles_lookup" in HOSTED_TOOL_DESCRIPTIONS


def test_hosted_lookup_is_stateless():
    result = lookup_hosted(
        merchant="NTUC FairPrice",
        cards=["uob_ppv", "citi_rewards_mc"],
        channel="mobile_contactless",
    )

    assert result["wallet_stored"] is False
    assert result["wallet_configured"] is True
    assert result["data_version"]
    assert result["recommendations"][0]["reason_summary"]


def test_hosted_agent_guide_is_stateless():
    guide = hosted.kiasumiles_agent_guide()

    assert guide["runtime"]["wallet_stored"] is False
    assert "kiasumiles_configure" not in {tool["name"] for tool in guide["tools"]}
    assert "kiasumiles_get_wallet" not in {tool["name"] for tool in guide["tools"]}
    assert not any("configure the wallet" in rule for rule in guide["display_rules"])


def test_data_version_has_counts():
    result = data_version()

    assert result["data_version"] != "unknown"
    assert result["cards"] >= 1
    assert result["merchants"] >= 1
    assert result["data_backend"] in {"demo_csv", "supabase"}


def test_hosted_exports_asgi_app():
    assert hosted.app is not None


def test_mcp_endpoint_is_rate_limited_per_ip():
    async def ok_app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    limited = hosted.RateLimitMiddleware(ok_app, max_requests=3, window_seconds=60)
    # No `with` block: the dummy app has no lifespan handler, and the
    # middleware needs no startup.
    client = TestClient(limited)
    statuses = [client.get("/mcp").status_code for _ in range(5)]
    landing_status = client.get("/").status_code

    assert statuses[:3] == [200, 200, 200]
    assert statuses[3:] == [429, 429]
    # Only /mcp is throttled — landing page and media stay open.
    assert landing_status == 200


def test_hosted_app_is_wrapped_in_rate_limiter():
    assert isinstance(hosted.app, hosted.RateLimitMiddleware)


def test_landing_page_and_media_routes_are_served():
    with TestClient(hosted.app) as client:
        landing = client.get("/")
        hero = client.get("/kiasumiles/hero.png")
        video = client.get("/kiasumiles/product-demo-60s.mp4")
        logo = client.get("/assets/logos/grab-colour.svg")
        namespaced_logo = client.get("/kiasumiles/assets/logos/grab-colour.svg")
        blocked = client.get("/assets/logos/../secret.txt")

    assert landing.status_code == 200
    assert "The right card, before you tap." in landing.text
    assert "Install KiasuMiles MCP for me" in landing.text
    assert "https://kiasumiles.space/mcp" in landing.text
    assert "Your agent or local client holds your selected card products" in landing.text
    assert "Hosted KiasuMiles ranks that request and does not store your stack." in landing.text
    assert "Wallet stays client-side" not in landing.text
    assert hero.status_code == 200
    assert hero.headers["content-type"] == "image/png"
    assert video.status_code == 200
    assert video.headers["content-type"] == "video/mp4"
    assert logo.status_code == 200
    assert logo.headers["content-type"] == "image/svg+xml"
    assert namespaced_logo.status_code == 200
    assert namespaced_logo.headers["content-type"] == "image/svg+xml"
    assert blocked.status_code == 404


def test_proof_assets_are_served_with_immutable_caching():
    client = TestClient(hosted.app)
    responses = [
        client.get(f"/kiasumiles/assets/proof/{filename}")
        for filename, _ in PROOF_ASSETS
    ]

    for response, (_, media_type) in zip(responses, PROOF_ASSETS):
        assert response.status_code == 200
        assert response.headers["content-type"] == media_type
        assert response.headers["etag"]
        assert response.headers["cache-control"] == "public, max-age=31536000, immutable"


def test_proof_asset_route_rejects_unknown_and_encoded_traversal_paths():
    client = TestClient(hosted.app)
    unknown = client.get("/kiasumiles/assets/proof/not-a-proof.webp")
    traversal = client.get(
        "/kiasumiles/assets/proof/%2e%2e%2fkiasumiles-real-life-720.webp"
    )

    assert unknown.status_code == 404
    assert traversal.status_code == 404


def test_favicon_is_served_with_immutable_caching():
    client = TestClient(hosted.app)
    response = client.get("/favicon.svg")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert response.headers["etag"]
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"


def test_landing_page_requires_revalidation():
    client = TestClient(hosted.app)
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=0, must-revalidate"


def test_privacy_page_is_request_scoped_and_requires_revalidation():
    client = TestClient(hosted.app)
    response = client.get("/privacy")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=0, must-revalidate"
    assert 'href="/"' in response.text
    assert "hello@theaiburrow.xyz" in response.text
    assert "supplies selected card products for each lookup" in response.text
    assert "does not store the stack" in response.text
    assert "card IDs" not in response.text
