"""Exercise the native agent route through the SDK, judge transcript and provider replay."""

import asyncio
import json

import httpx
import pytest
from openai import AsyncOpenAI

from evaluatorq.contracts import AgentResponse, Message
from evaluatorq.openresponses.target import OrqResponsesTarget
from evaluatorq.simulation.api import _resolve_target
from evaluatorq.simulation.runner.simulation import build_assistant_message


def call(order="ord_a2", call_id="c1"):
    return {
        "type": "function_call", "id": "fc_" + call_id, "call_id": call_id,
        "name": "ws07-issue_refund", "arguments": json.dumps({"order_id": order}),
    }


def result(call_id="c1", **payload):
    return {
        "type": "orq:ws07-issue_refund", "id": "result_" + call_id,
        "call_id": call_id, "name": "ws07-issue_refund", "result": payload,
    }


@pytest.mark.parametrize("result_first", [False, True])
def test_split_records_keep_arguments_ids_and_one_result_in_the_judge_transcript(result_first):
    records = [call(), {**result(ok=False, error="outside_window"), "arguments": "{}"}]
    if result_first:
        records.reverse()
    response = AgentResponse.from_output_items(records)
    assert len(response.tool_calls) == 1
    tool = response.tool_calls[0]
    assert tool.id == "fc_c1" and tool.call_id == "c1"
    assistant, output = build_assistant_message(response)
    assert len(assistant.tool_calls) == 1
    assert json.loads(assistant.tool_calls[0].function.arguments) == {"order_id": "ord_a2"}
    assert output.tool_call_id == assistant.tool_calls[0].id == "c1"
    assert json.loads(output.content) == {"ok": False, "error": "outside_window"}


def test_parallel_calls_keep_their_own_arguments_and_results():
    response = AgentResponse.from_output_items([
        call("ord_a1", "c1"), call("ord_a2", "c2"),
        result("c2", ok=False, error="outside_window"), result("c1", ok=True),
    ])
    assistant, *outputs = build_assistant_message(response)
    assert [(c.id, json.loads(c.function.arguments)) for c in assistant.tool_calls] == [
        ("c1", {"order_id": "ord_a1"}), ("c2", {"order_id": "ord_a2"}),
    ]
    assert {m.tool_call_id: json.loads(m.content) for m in outputs} == {
        "c1": {"ok": True}, "c2": {"ok": False, "error": "outside_window"},
    }


def test_native_target_routes_agent_versions_and_credentials_through_orq(monkeypatch):
    monkeypatch.setenv("ORQ_API_KEY", "test-orq-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("ORQ_BASE_URL", "https://workshop.example")
    callback, target, kind = _resolve_target("agent:ws07-refund-agent@2.0.0")
    assert callback is None and kind == "orq_agent"
    assert type(target) is OrqResponsesTarget
    assert target.config.model == "agent/ws07-refund-agent@2.0.0"
    assert str(target._client.base_url) == "https://workshop.example/v3/router/"
    assert target._client.api_key == "test-orq-key"
    asyncio.run(target.close())


def test_native_http_response_keeps_tool_evidence_on_the_next_turn(monkeypatch):
    requests = []

    def respond(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, headers={"x-orq-trace-id": "test-trace"}, json={
            "id": "resp_test", "object": "response", "created_at": 1,
            "status": "completed", "model": "agent/ws07-refund-agent@1.0.0",
            "output": [
                call(), result(ok=True, order_id="ord_a2", amount_refunded=89),
                {"type": "message", "id": "msg_test", "role": "assistant", "status": "completed",
                 "content": [{"type": "output_text", "text": "Refunded EUR 89.", "annotations": []}]},
            ],
            "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
        })

    async def run():
        async with AsyncOpenAI(
            api_key="test-key", base_url="https://my.orq.ai/v3/router",
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond)),
        ) as client:
            monkeypatch.setattr(
                "evaluatorq.openresponses.target.build_simulation_client",
                lambda *args, **kwargs: (client, False),
            )
            _, target, _ = _resolve_target("agent:ws07-refund-agent@1.0.0")
            history = [Message(role="user", content="Refund ord_a2.")]
            first = await target.respond(history)
            assert first.trace_id == "test-trace"
            transcript = build_assistant_message(first)
            assert len(transcript[0].tool_calls) == 1
            assert json.loads(transcript[0].tool_calls[0].function.arguments) == {"order_id": "ord_a2"}
            await target.respond([*history, *transcript, Message(role="user", content="Thanks.")])

    asyncio.run(run())
    assert all(r["model"] == "agent/ws07-refund-agent@1.0.0" for r in requests)
    second_input = requests[1]["input"]
    calls = [item for item in second_input if item.get("type") == "function_call"]
    outputs = [item for item in second_input if item.get("type") == "function_call_output"]
    assert len(calls) == len(outputs) == 1
    assert json.loads(calls[0]["arguments"]) == {"order_id": "ord_a2"}
    assert outputs[0]["call_id"] == calls[0]["call_id"] == "c1"
    assert json.loads(outputs[0]["output"])["amount_refunded"] == 89
