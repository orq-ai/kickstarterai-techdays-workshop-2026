"""Seat checks, versioning and reset, against a fake orq client. No network."""

from types import SimpleNamespace as NS

import pytest

from app.refund_agent import config, entities


def _seat(monkeypatch, **changes):
    seat = config.settings.model_copy(update={"api_key": "k", "prefix": "ws07", "project": "p", **changes})
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


def test_seed_eval_dataset_is_created_once(monkeypatch, tmp_path):
    """Running seed-eval twice finds the dataset by key and adds no rows the second time."""
    _seat(monkeypatch)
    rows = tmp_path / "rows.jsonl"
    rows.write_text('{"inputs": {"message": "a"}}\n\n{"inputs": {"message": "b"}}\n')
    datasets, created, added = [], [], []

    def create(request):
        created.append(request)
        datasets.append(NS(display_name=request["display_name"], id="ds-1"))
        return NS(id="ds-1")

    orq = NS(datasets=NS(
        list=lambda **kw: NS(data=list(datasets)),
        create=create,
        create_datapoint=lambda dataset_id, request_body: added.append((dataset_id, request_body)),
        list_datapoints=lambda **kw: NS(data=[NS(id="dp-1")] if added else []),
    ))
    assert entities.ensure_dataset(orq, rows) == "ds-1"
    assert entities.ensure_dataset(orq, rows) == "ds-1"
    assert [r["display_name"] for r in created] == ["ws07-refund-eval"]
    assert added == [("ds-1", [{"inputs": {"message": "a"}}, {"inputs": {"message": "b"}}])]
def test_dataset_lookups_search_by_key(monkeypatch):
    """Lookups ask the API for this seat's datasets, so they are found beyond the first page."""
    _seat(monkeypatch)
    searches = []

    def list_datasets(limit, search=None):
        searches.append(search)
        return NS(data=[NS(display_name="ws07-refund-eval", id="ds-7")] if search and "ws07-" in search else [])

    has_rows = NS(data=[NS(id="dp-1")])
    orq = NS(datasets=NS(list=list_datasets, list_datapoints=lambda **kw: has_rows, create=None, create_datapoint=None))
    assert entities.ensure_dataset(orq) == "ds-7"  # found with rows, so nothing is created or added
    assert searches == ["ws07-refund-eval"]


def test_seed_eval_fills_a_dataset_left_empty_by_a_failed_seed(monkeypatch, tmp_path):
    """create() worked, create_datapoint() did not: the next seed-eval adds the rows instead of keeping it empty."""
    _seat(monkeypatch)
    rows = tmp_path / "rows.jsonl"
    rows.write_text('{"inputs": {"message": "a"}}\n')
    added = []
    orq = NS(datasets=NS(
        list=lambda **kw: NS(data=[NS(display_name="ws07-refund-eval", id="ds-7")]),
        list_datapoints=lambda **kw: NS(data=[]),
        create=None,
        create_datapoint=lambda dataset_id, request_body: added.append((dataset_id, request_body)),
    ))
    assert entities.ensure_dataset(orq, rows) == "ds-7"
    assert added == [("ds-7", [{"inputs": {"message": "a"}}])]
