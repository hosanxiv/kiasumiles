from starlette.testclient import TestClient

from kiasumiles import hosted


def test_openai_apps_challenge_uses_environment_token(monkeypatch):
    monkeypatch.setenv("KIASUMILES_OPENAI_APPS_CHALLENGE", "verification-token")

    response = TestClient(hosted.app).get("/.well-known/openai-apps-challenge")

    assert response.status_code == 200
    assert response.text == "verification-token"
    assert response.headers["cache-control"] == "no-store"
