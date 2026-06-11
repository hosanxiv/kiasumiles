from kiasumiles import hosted
from kiasumiles.agent_contract import HOSTED_TOOL_DESCRIPTIONS
from kiasumiles.tools import lookup_hosted, data_version
from starlette.testclient import TestClient


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
    assert result["data_backend"] in {"demo_csv", "private_csv", "supabase"}


def test_hosted_exports_asgi_app():
    assert hosted.app is not None


def test_landing_page_and_media_routes_are_served():
    with TestClient(hosted.app) as client:
        landing = client.get("/")
        hero = client.get("/kiasumiles/hero.png")
        video = client.get("/kiasumiles/product-demo-60s.mp4")

    assert landing.status_code == 200
    assert "Your cards. Your merchants. Your best answer." in landing.text
    assert "https://kiasumiles.space/mcp" in landing.text
    assert "does not store a wallet" in landing.text
    assert hero.status_code == 200
    assert hero.headers["content-type"] == "image/png"
    assert video.status_code == 200
    assert video.headers["content-type"] == "video/mp4"
