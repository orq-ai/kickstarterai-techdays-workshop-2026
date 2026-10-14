"""Seat checks, versioning and reset, against a fake orq client. No network."""

from dataclasses import replace
from types import SimpleNamespace as NS

import pytest

from app.refund_agent import config, entities


def _seat(monkeypatch, **changes):
    seat = replace(config.settings, **{"api_key": "k", "prefix": "ws07", "project": "p", **changes})
    monkeypatch.setattr(entities, "settings", seat)
    monkeypatch.setattr(entities, "K", seat.key)
    return seat


@pytest.mark.parametrize("prefix", ["", "ws", "ws7", "orq", "ws07-x"])
def test_seed_and_reset_reject_a_missing_or_default_prefix(monkeypatch, prefix):
    _seat(monkeypatch, prefix=prefix)
    for command in (entities.seed, entities.reset):
        with pytest.raises(SystemExit, match="WS_PREFIX"):
            command(orq=object())  # fails before any call: object() has no API


def test_instructions_name_the_seat_tools(monkeypatch, tmp_path):
    _seat(monkeypatch)
    path = tmp_path / "i.md"
    path.write_text("Be nice.\n")
    assert entities.agent_instructions(path).endswith(
        "Your tools are named ws07-lookup_order, ws07-issue_refund, ws07-get_policy."
    )


class _Agents:
    def __init__(self, version, instructions):
        self.agent = {"version": version, "instructions": instructions}
        self.updates = []

    def retrieve(self, agent_key):
        return NS(model_dump=lambda: dict(self.agent))

    def update(self, **kw):
        self.updates.append(kw)
        major = int(self.agent["version"].split(".")[0]) + 1
        self.agent = {"version": f"{major}.0.0", "instructions": kw["instructions"]}
        return NS(version=self.agent["version"])


def test_publish_bumps_once_then_is_a_no_op(monkeypatch, tmp_path):
    _seat(monkeypatch)
    path = tmp_path / "i.md"
    path.write_text("v1")
    orq = NS(agents=_Agents("1.0.0", entities.agent_instructions(path)))
    assert entities.publish_version(orq, path) == ("1.0.0", False)
    path.write_text("v2")
    assert entities.publish_version(orq, path) == ("2.0.0", True)
    assert entities.publish_version(orq, path) == ("2.0.0", False)
    assert [u["version_increment"] for u in orq.agents.updates] == ["major"]


def test_versions_newest_first():
    assert entities.versions({"version": "3.0.0"}) == ["3.0.0", "2.0.0", "1.0.0"]
    assert entities.versions({"version": "2.1.0"}) == ["2.1.0", "2.0.0", "1.0.0"]
    assert entities.versions(None) == []


def _page(*keys, attr="key"):
    return lambda **kw: NS(data=[NS(**{attr: k, "id": k}) for k in keys])


def test_reset_touches_only_this_seat_and_reports_failures(monkeypatch):
    _seat(monkeypatch)
    deleted = []
    monkeypatch.setattr(entities, "rest", lambda method, path: deleted.append(path))

    def tool_delete(tool_id):
        if tool_id == "ws07-issue_refund":
            raise RuntimeError("403")
        deleted.append(tool_id)

    orq = NS(
        agents=NS(list=lambda **kw: NS(data=[
            NS(key="ws07-refund-agent", model_dump=lambda **k: {}),
            NS(key="ws070-refund-agent", model_dump=lambda **k: {}),  # another seat: ws070, not ws07
            NS(key="ws08-refund-agent", model_dump=lambda **k: {}),
        ])),
        tools=NS(list=_page("ws07-lookup_order", "ws07-issue_refund", "ws08-lookup_order"), delete=tool_delete),
        evals=NS(all=_page("ws07-refund-policy-judge"), delete=lambda id: deleted.append(id)),
        datasets=NS(list=_page("ws07-refund-eval", "other", attr="display_name"), delete=lambda dataset_id: deleted.append(dataset_id)),
    )
    assert entities.reset(orq) == 1  # the 403 on one tool is counted, not skipped
    assert deleted == [
        "/v2/agents/ws07-refund-agent",
        "ws07-lookup_order",
        "ws07-refund-policy-judge",
        "ws07-refund-eval",
    ]
