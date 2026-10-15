"""Keep workshop environment loading and setup checks intact across settings changes."""

import os
import subprocess

import pytest

from app.refund_agent.config import Settings


def test_dotenv_overrides_shell_and_initializes_downstream_environment(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "ORQ_API_KEY=fixture-key\nWS_PREFIX=ws07\nORQ_PROJECT=fixture-project\n"
        "MODEL=fixture/model\nJUDGE_MODEL=fixture/judge\nIDENTITY_ID=fixture-user\n"
        "ORQ_BASE_URL=https://fixture.example/\n"
    )
    code = """
import os
from app.refund_agent.config import settings
assert settings.api_key == os.environ['ORQ_API_KEY'] == 'fixture-key'
assert settings.prefix == 'ws07'
assert settings.project == 'fixture-project'
assert settings.model == 'fixture/model'
assert settings.judge_model == 'fixture/judge'
assert settings.identity_id == 'fixture-user'
assert settings.router_url == 'https://fixture.example/v3/router'
settings.require_seat()
"""
    result = subprocess.run(
        ["uv", "run", "python", "-c", code],
        env={**os.environ, "ORQ_ENV_FILE": str(env_file), "ORQ_API_KEY": "stale-key"},
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr


def test_values_are_trimmed_and_path_override_remains_dynamic(monkeypatch):
    monkeypatch.setenv("WS_PREFIX", " ws07 ")
    monkeypatch.setenv("ORQ_PROJECT", " project ")
    monkeypatch.delenv("ORQ_PATH", raising=False)
    settings = Settings(api_key="fixture-key")
    assert settings.agent_key == "ws07-refund-agent"
    assert settings.path == "project/workshop"
    monkeypatch.setenv("ORQ_PATH", " custom/workshop ")
    assert settings.path == "custom/workshop"


def test_setup_checks_remain_explicit_and_friendly(monkeypatch):
    monkeypatch.delenv("ORQ_PATH", raising=False)
    with pytest.raises(SystemExit, match="ORQ_API_KEY is empty"):
        Settings(api_key="").require_key()
    settings = Settings(api_key="fixture-key", prefix="ws07", project="")
    with pytest.raises(SystemExit, match="ORQ_PROJECT is empty"):
        settings.require_seat()
    monkeypatch.setenv("ORQ_PATH", "custom/workshop")
    assert settings.require_seat() is settings
