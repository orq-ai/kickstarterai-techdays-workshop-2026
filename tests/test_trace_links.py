"""Response telemetry must open the matching trace in its Studio workspace."""

from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest
from orq_ai_sdk.models.responsetelemetry import ResponseTelemetry

from app import web
from app.refund_agent.client import parse_turn
from app.refund_agent.config import WORKSHOP_WORKSPACE, Settings

TRACE = "0ab923725ff5b3419b26ebe72a46a258"
SPAN = "1dbc5a2821bc2730"


@pytest.mark.parametrize("workspace", [None, "", "  "])
def test_missing_or_blank_workspace_uses_workshop(monkeypatch, workspace):
    if workspace is None:
        monkeypatch.delenv("ORQ_WORKSPACE", raising=False)
    else:
        monkeypatch.setenv("ORQ_WORKSPACE", workspace)
    assert Settings().workspace == WORKSHOP_WORKSPACE


def test_workspace_override(monkeypatch):
    monkeypatch.setenv("ORQ_WORKSPACE", "other-workspace")
    assert Settings().workspace == "other-workspace"


@pytest.mark.parametrize("sdk_object", [False, True])
def test_response_telemetry_reaches_the_studio_link(monkeypatch, sdk_object):
    telemetry = {"trace_id": TRACE, "span_id": SPAN}
    response = {"output": [], "telemetry": telemetry}
    if sdk_object:
        response = SimpleNamespace(output=[], telemetry=ResponseTelemetry(**telemetry))
    turn = parse_turn(response)
    monkeypatch.setattr(web, "settings", web.settings.model_copy(update={"base_url": "https://my.orq.ai", "workspace": WORKSHOP_WORKSPACE}))
    assert turn.span_id == SPAN
    assert web.trace_url(turn.trace_id) == (
        "https://my.orq.ai/kickstartai-workshop-2026/traces/"
        "(trace:0ab923725ff5b3419b26ebe72a46a258)"
    )


def test_trace_only_and_missing_telemetry(monkeypatch):
    monkeypatch.setattr(web, "settings", web.settings.model_copy(update={"base_url": "https://my.orq.ai", "workspace": "other-workspace"}))
    link = urlsplit(web.trace_url(TRACE))
    assert link.path == f"/other-workspace/traces/(trace:{TRACE})"
    assert link.query == ""
    turn = parse_turn({"output": []})
    assert turn.span_id is None
    assert web.trace_url(turn.trace_id) is None
