"""The regression scorers and the turn parser, on hand-made outputs. No network."""

import asyncio
from types import SimpleNamespace as NS

from app.refund_agent.client import parse_turn
from evals import scorers


def _params(calls, expected="refuse", allowed="", answer="ok"):
    data = NS(inputs={"expected_decision": expected, "allowed_refunds": allowed})
    return {"output": {"answer": answer, "tool_calls": calls}, "data": data}


def _refund(order, result):
    return {"name": "issue_refund", "arguments": {"order_id": order}, "result": result}


def run(scorer, params):
    return asyncio.run(scorer(params)).pass_


def test_a_call_is_not_a_refund():
    rejected = [_refund("ord_a1", {"ok": False, "error": "outside_window"})]
    assert not run(scorers.refund_outcome, _params(rejected, "refund", "ord_a1"))
    assert run(scorers.refund_outcome, _params([_refund("ord_a1", {"ok": True})], "refund", "ord_a1"))


def test_an_attempt_fails_even_when_the_tool_rejects_it():
    rejected = [_refund("ord_a5", {"ok": False, "error": "reason_not_in_exception_list"})]
    assert run(scorers.refund_outcome, _params(rejected))  # nothing was refunded...
    assert not run(scorers.no_unauthorized_attempt, _params(rejected))  # ...but it tried
    assert run(scorers.no_unauthorized_attempt, _params([_refund("ord_a1", {"ok": True})], "refund", "ord_a1"))


def test_missing_tool_evidence_fails_closed():
    assert not run(scorers.refund_outcome, _params([_refund("ord_a1", None)], "refund", "ord_a1"))


def test_multi_order_row_allows_only_its_orders():
    calls = [_refund("ord_a1", {"ok": True}), _refund("ord_a3", {"ok": False})]
    assert run(scorers.refund_outcome, _params(calls, "route_human", "ord_a1,ord_a2"))
    assert not run(scorers.no_unauthorized_attempt, _params(calls, "route_human", "ord_a1,ord_a2"))


def test_pii_in_the_answer_text():
    assert not run(scorers.no_pii_leak, _params([], answer="Sent to sam@example.org"))
    assert not run(scorers.no_pii_leak, _params([], answer="Call +31 6 1234 5678"))
    assert run(scorers.no_pii_leak, _params([], answer="Tracking 3SABC1234567890, delivered 2026-07-02"))


def test_parse_turn_pairs_orq_results_with_calls():
    response = {
        "output": [
            {"type": "function_call", "call_id": "c1", "name": "ws01-issue_refund", "arguments": '{"order_id": "ord_a3"}'},
            {"type": "orq:ws01-issue_refund", "call_id": "c1", "name": "ws01-issue_refund",
             "arguments": '{"order_id": "ord_a3"}', "result": {"ok": False, "error": "outside_window"}},
            {"type": "message", "content": [{"type": "output_text", "text": "Sorry."}]},
        ],
        "telemetry": {"trace_id": "t"},
    }
    turn = parse_turn(response)
    assert turn.answer == "Sorry." and turn.trace_id == "t"
    assert len(turn.tool_calls) == 1
    call = turn.tool_calls[0]
    assert call.name.endswith("issue_refund") and call.result == {"ok": False, "error": "outside_window"}


def test_a_second_successful_refund_of_the_same_order_fails():
    """The code tool forgets state between calls, so only the scorer can catch a double payout."""
    twice = [_refund("ord_a1", {"ok": True}), _refund("ord_a1", {"ok": True})]
    assert not run(scorers.refund_outcome, _params(twice, "refund", "ord_a1"))
    retried = [_refund("ord_a1", {"ok": False, "error": "outside_window"}), _refund("ord_a1", {"ok": True})]
    assert run(scorers.refund_outcome, _params(retried, "refund", "ord_a1"))  # one refund after a rejection is fine


def test_policy_judge_reads_the_verdict_and_fails_closed(monkeypatch):
    monkeypatch.setattr(scorers, "judge_id", lambda: "judge-1")
    params = _params([], answer="Refunded EUR 24.99.")
    params["data"].inputs["message"] = "Refund ord_a1"
    params["data"].expected_output = "refund"
    for verdict, expected in [
        ({"passed": True, "explanation": "follows policy"}, True),
        ({"passed": False, "explanation": "promised a refund it cannot give"}, False),
        ({"value": True}, True),  # some evaluator replies carry `value` instead of `passed`
        ({}, False),  # no verdict at all is a fail, not a pass
    ]:
        monkeypatch.setattr(scorers, "rest", lambda method, path, body, v=verdict: v)
        assert run(scorers.policy_judge, params) is expected, verdict
