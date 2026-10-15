"""Simulation reporting and saved-case replay, without model or platform calls."""

import asyncio
import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from evaluatorq.simulation.contracts import SimulationDatapoint, SimulationResult, SimulationRun

spec = importlib.util.spec_from_file_location(
    "simulation_runner", Path(__file__).resolve().parents[1] / "modules/03-simulation/run.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def result(*, stop="judge", verified=True, audited=True, passed=True, evaluator_errors=None):
    return SimulationResult(
        messages=[], terminated_by=stop, reason="test reason", goal_achieved=False,
        goal_completion_score=0, rules_broken=[], turn_count=1, token_usage={}, turn_metrics=[],
        criteria_verified=verified,
        metadata={
            "persona": "Saved persona", "scenario": "Saved scenario",
            "criteria_meta": [{"description": "A required action", "audited": audited, "passed": passed}],
            "evaluator_errors": evaluator_errors or {},
        },
    )


def test_all_held_requires_a_successful_execution_and_complete_audit():
    assert runner.rule_status(result()) == ("all held", False, False)


@pytest.mark.parametrize("stop", ["error", "timeout"])
def test_execution_failure_never_reports_all_held(stop):
    label, broken, unknown = runner.rule_status(result(stop=stop))
    assert "UNKNOWN" in label and stop in label
    assert unknown and not broken


@pytest.mark.parametrize("verified,audited", [(False, True), (None, True), (True, False), (True, None)])
def test_unknown_or_partial_audits_never_report_all_held(verified, audited):
    label, _, unknown = runner.rule_status(result(verified=verified, audited=audited))
    assert unknown and "UNKNOWN" in label


def test_a_confirmed_violation_survives_a_later_error():
    label, broken, unknown = runner.rule_status(result(stop="error", passed=False))
    assert broken and unknown
    assert "BROKEN: A required action" in label and "UNKNOWN" in label


def test_failed_evaluator_is_not_a_pass():
    assert runner.rule_status(result(evaluator_errors={"criteria_met": "no score"}))[2]


def test_missing_criteria_metadata_is_unknown():
    r = result()
    r.metadata["criteria_meta"] = []
    assert runner.rule_status(r)[2]


@pytest.fixture
def fake_run(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(runner, "settings", SimpleNamespace(
        require_seat=lambda: None, key=lambda name: "ws07-" + name, agent_key="ws07-refund-agent"
    ))
    monkeypatch.setenv("EVALUATORQ_DIR", str(tmp_path / ".evaluatorq"))

    async def simulate(**kwargs):
        calls.append(kwargs)
        kwargs["report_path"].parent.mkdir(parents=True, exist_ok=True)
        kwargs["report_path"].write_text("{}")
        return [result()]

    monkeypatch.setattr(runner, "simulate", simulate)
    return calls


def saved_run(path, *, cases=True):
    datapoint = SimulationDatapoint(
        id="saved-case", persona=runner.PERSONAS[0], scenario=runner.SCENARIOS[0],
        user_system_prompt="Saved simulator instructions", first_message="Saved opening message",
    )
    run = SimulationRun(
        run_name="v1-baseline", created_at=datetime.now(timezone.utc), mode="simulate", target_kind="callback",
        evaluator_names=["goal_achieved", "criteria_met"], total_results=1, scorer_averages={},
        results=[], datapoints=[datapoint] if cases else None, max_turns=5,
    )
    path.write_text(run.model_dump_json())


def test_replay_uses_the_saved_cases_and_budget_and_keeps_baseline(fake_run, tmp_path, capsys):
    baseline = tmp_path / "v1.json"
    saved_run(baseline)
    original = baseline.read_bytes()
    asyncio.run(runner.main(["2.0.0", "--replay", str(baseline)]))
    call = fake_run[0]
    assert call["previous_run"] == str(baseline)
    assert "personas" not in call and "scenarios" not in call
    assert call["max_turns"] == 5 and call["target"] == "agent:ws07-refund-agent@2.0.0"
    assert baseline.read_bytes() == original
    output = capsys.readouterr().out
    assert "saved    : " + str(call["report_path"]) in output
    assert "stop   : judge" in output and "missing  :" not in output
    assert "0/1 incomplete or unverified" in output


def test_old_reports_without_cases_fail_before_model_calls(fake_run, tmp_path):
    baseline = tmp_path / "legacy.json"
    saved_run(baseline, cases=False)
    with pytest.raises(SystemExit, match="no replayable cases"):
        asyncio.run(runner.main(["2.0.0", "--replay", str(baseline)]))
    assert not fake_run


def test_missing_cases_are_reported_as_incomplete(fake_run, monkeypatch, capsys):
    monkeypatch.setattr(runner, "PERSONAS", runner.PERSONAS * 2)
    asyncio.run(runner.main(["1.0.0"]))
    assert "coverage : INCOMPLETE" in capsys.readouterr().out
    assert "previous_run" not in fake_run[0]


@pytest.mark.parametrize("version,target", [
    ("1.0.0", "agent:ws07-refund-agent@1.0.0"),
    ("latest", "agent:ws07-refund-agent"),
])
def test_native_target_selects_the_requested_agent_version(fake_run, version, target):
    asyncio.run(runner.main([version]))
    assert fake_run[0]["target"] == target
