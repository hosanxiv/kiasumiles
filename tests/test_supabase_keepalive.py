from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from urllib.error import HTTPError

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / ".github" / "supabase_keepalive.py"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "supabase-keep-awake.yml"


def _load_script():
    assert SCRIPT.exists(), "The Supabase keep-awake script is missing"
    spec = importlib.util.spec_from_file_location("supabase_keepalive", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return self._payload


def test_script_performs_one_small_read_only_supabase_query():
    module = _load_script()
    requests = []

    def fake_open(request, timeout):
        requests.append((request, timeout))
        return FakeResponse([{"card_id": "present"}])

    module.query_supabase(
        "https://project.supabase.co",
        "test-service-role-key",
        opener=fake_open,
    )

    assert len(requests) == 1
    request, timeout = requests[0]
    assert request.get_method() == "GET"
    assert request.full_url == (
        "https://project.supabase.co/rest/v1/card_rules?select=card_id&limit=1"
    )
    assert request.get_header("Apikey") == "test-service-role-key"
    assert request.get_header("Authorization") == "Bearer test-service-role-key"
    assert timeout == 15


def test_missing_credentials_fail_before_any_network_request(capsys):
    module = _load_script()
    network_called = False

    def unexpected_open(request, timeout):
        nonlocal network_called
        network_called = True
        raise AssertionError("network should not be called")

    exit_code = module.main(environ={}, opener=unexpected_open)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert network_called is False
    assert captured.out == ""
    assert "credentials are not configured" in captured.err.lower()


def test_failure_is_visible_without_printing_credentials(capsys):
    module = _load_script()
    secret = "do-not-print-this-service-role-key"
    environ = {
        "KIASUMILES_SUPABASE_URL": "https://project.supabase.co",
        "KIASUMILES_SUPABASE_SERVICE_ROLE_KEY": secret,
    }

    def failing_open(request, timeout):
        raise HTTPError(request.full_url, 401, "Unauthorized", {}, None)

    exit_code = module.main(environ=environ, opener=failing_open)

    captured = capsys.readouterr()
    combined_output = captured.out + captured.err
    assert exit_code == 1
    assert "HTTP 401" in captured.err
    assert secret not in combined_output
    assert environ["KIASUMILES_SUPABASE_URL"] not in combined_output


def test_workflow_runs_three_times_daily_and_supports_manual_checks():
    assert WORKFLOW.exists(), "The scheduled Supabase keep-awake workflow is missing"
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    triggers = workflow.get("on", workflow.get(True))

    assert triggers["schedule"] == [{"cron": "17 0,8,16 * * *"}]
    assert triggers["workflow_dispatch"] is None
    assert workflow["permissions"] == {"contents": "read"}

    job = workflow["jobs"]["keep-awake"]
    assert job["timeout-minutes"] == 5
    run_step = next(step for step in job["steps"] if "run" in step)
    assert run_step["run"] == "python .github/supabase_keepalive.py"
    assert run_step["env"] == {
        "KIASUMILES_SUPABASE_URL": "${{ secrets.KIASUMILES_SUPABASE_URL }}",
        "KIASUMILES_SUPABASE_SERVICE_ROLE_KEY": (
            "${{ secrets.KIASUMILES_SUPABASE_SERVICE_ROLE_KEY }}"
        ),
    }
    assert "kiasumiles.space/health" not in WORKFLOW.read_text(encoding="utf-8")
