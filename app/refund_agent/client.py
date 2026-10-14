"""The orq SDK client and the one call this workshop makes to the agent.

The agent lives in orq: its instructions, model and tools are an entity with versions, and orq
runs the tools as code. Talking to it is one Responses API call with `model="agent/<key>"`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from orq_ai_sdk import Orq

from .config import settings


def make_orq() -> Orq:
    """The native orq SDK: agents, tools, datasets, evaluators, responses."""
    settings.require_key()
    return Orq(api_key=settings.api_key, server_url=settings.base_url)


@dataclass
class ToolCall:
    name: str  # without the seat prefix: lookup_order, issue_refund, get_policy
    arguments: dict[str, Any]
    result: Any = None  # what the code tool returned; None if orq reports no result


@dataclass
class Turn:
    answer: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    trace_id: str | None = None
    version: str = "latest"

    @property
    def tool_names(self) -> list[str]:
        return [call.name for call in self.tool_calls]


def model_id(version: str = "latest") -> str:
    """`agent/<seat>-refund-agent`, pinned with `@1.0.0` unless `latest`."""
    return f"agent/{settings.agent_key}" + ("" if version in ("", "latest") else f"@{version}")


def _field(item: Any, name: str) -> Any:
    return item.get(name) if isinstance(item, dict) else getattr(item, name, None)


def parse_turn(response: Any, version: str = "latest") -> Turn:
    """Answer text, every tool call with its arguments and result, and the trace id.

    A tool call arrives as a `function_call` item; orq runs it and adds an `orq:<tool key>` item
    with the same `call_id` carrying `result` (or `status: failed`).
    """
    calls: dict[str, ToolCall] = {}
    texts: list[str] = []
    for item in _field(response, "output") or []:
        kind = str(_field(item, "type") or "")
        call_id = _field(item, "call_id")
        if kind == "message":
            texts += [_field(part, "text") or "" for part in _field(item, "content") or []]
        elif kind == "function_call" or kind.startswith("orq:"):
            call = calls.get(call_id)
            if call is None:
                raw_args = _field(item, "arguments") or "{}"
                call = calls[call_id] = ToolCall(
                    name=str(_field(item, "name") or "").removeprefix(f"{settings.prefix}-"),
                    arguments=json.loads(raw_args) if isinstance(raw_args, str) else raw_args,
                )
            if kind.startswith("orq:"):
                result = _field(item, "result")
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except ValueError:
                        pass  # a plain string result stays a string
                call.result = result if result is not None else {"ok": False, "status": _field(item, "status")}
    telemetry = _field(response, "telemetry") or {}
    return Turn(
        answer="".join(texts).strip(),
        tool_calls=list(calls.values()),
        trace_id=_field(telemetry, "trace_id"),
        version=version,
    )


def ask_agent(
    input: str | list[dict[str, Any]], version: str = "latest", orq: Orq | None = None, **extra: Any
) -> Turn:
    """One turn with your agent. `input` is a message, or the whole conversation as role/content dicts."""
    orq = orq or make_orq()
    response = orq.responses.create(model=model_id(version), input=input, **extra)
    return parse_turn(response, version)
