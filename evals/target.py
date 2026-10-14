"""The evaluatorq target for your managed agent: `agent/<seat>-refund-agent@<version>`.

evaluatorq's built-in `agent:<key>` target already calls the agent through the Responses API and
orq runs the code tools server-side. One gap: the tool *results* come back in `orq:<tool>` items,
which evaluatorq 1.70 does not pair with their `function_call`, so it drops every tool call
("result is None") and the judge never sees that `issue_refund` was attempted. This subclass
copies each result onto its call. Nothing else changes: no tool runs on your machine.
"""

from __future__ import annotations

import json
from typing import Any

from evaluatorq.contracts import LLMCallConfig, ToolCallOutputItem
from evaluatorq.openresponses.target import OrqResponsesTarget
from openai import AsyncOpenAI

from app.refund_agent.config import settings


class ManagedAgentTarget(OrqResponsesTarget):
    """One `responses.create(model="agent/<key>@<version>")` per simulated turn, tool results kept."""

    def _normalise_response(self, response: Any, **kwargs: Any):
        out = super()._normalise_response(response, **kwargs)
        results = {}
        for item in response.output or []:
            raw = item if isinstance(item, dict) else item.model_dump()
            if str(raw.get("type", "")).startswith("orq:"):  # orq ran this tool; `result` is its return value
                results[raw.get("call_id")] = raw.get("result", raw.get("status"))
        items, seen = [], set()
        for item in out.output:
            if isinstance(item, ToolCallOutputItem):
                if item.call_id in seen:  # the orq:<tool> item parses as a second copy of the call
                    continue
                seen.add(item.call_id)
                if item.result is None and item.call_id in results:
                    item = item.model_copy(update={"result": json.dumps(results[item.call_id])})
            items.append(item)
        return out.model_copy(update={"output": items})


def agent_target(version: str = "latest") -> ManagedAgentTarget:
    """Your agent at one version. `latest` is the newest; `1.0.0` pins the first draft."""
    model = f"agent/{settings.agent_key}" + ("" if version == "latest" else f"@{version}")
    router = AsyncOpenAI(base_url=settings.router_url, api_key=settings.api_key)
    return ManagedAgentTarget(LLMCallConfig(model=model, client=router), client=router, require_orq=True)
