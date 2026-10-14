"""Refund agent: inspect your managed agent, then call it once from Python.

The agent lives in orq: instructions, model and three code tools, versioned. Calling it is one
Responses API call with `model="agent/<seat>-refund-agent"`; orq runs the model loop AND the
tools, and returns every tool call with its result next to the answer.

Fill in the two TODOs. The script runs as is and tells you what is missing.
Run it with `make invoke-agent` (or `uv run python modules/02-refund-agent/run.py`).
"""

from app.refund_agent.client import make_orq
from app.refund_agent.config import settings

QUESTION = "Please refund ord_a2, the dock does not fit my laptop."

orq = make_orq()

# ── Step 1 · Inspect the agent ──
# One entity: the version, the model, the tools. Reads show tools as {action_type, key, ...};
# the create call in app/refund_agent/entities.py wrote them as {"type": "code", "key": ...}.
agent = orq.agents.retrieve(agent_key=settings.agent_key)
print("── Step 1 · Inspect the agent ─────────────────────────")
print(f"agent    : {agent.key} v{agent.version}")
print(f"model    : {agent.model.id}")
print(f"tools    : {', '.join(tool.key for tool in agent.settings.tools)}")
print(f"limits   : max_iterations {agent.settings.max_iterations}, max_execution_time {agent.settings.max_execution_time}s")

# ── Step 2 · Call it ──
# The same call works from curl and the CLI (see the README). `@latest` is implied; pin a
# version with `agent/<key>@1.0.0`.
# TODO 1: call your agent with QUESTION and keep the result in `response`.
#   - Call `orq.responses.create(...)` with two keyword arguments, `model` and `input`.
#   - `input` is just the text in QUESTION.
#   - `model` is not a model name here. It is the agent's address: the string "agent/" followed
#     by your agent key. `settings.agent_key` already holds the key with your seat prefix, so
#     build it with an f-string. Add "@1.0.0" to the end only if you want to pin a version.
#   - hello_agent.py in this folder makes the same kind of call, if you want to see one.
#   - Replace `response = None` with the call. Nothing else in this step changes.
response = None
if response is None:
    raise SystemExit("TODO 1: call orq.responses.create with model=f\"agent/{settings.agent_key}\" and input=QUESTION")

# ── Step 3 · Read what it did ──
# Each tool call is a `function_call` item, followed by an `orq:<tool key>` item with the same
# call_id that carries the result orq computed. The answer is the `message` item.
print("── Step 2 · Call it and read the output items ─────────")
print(f"question : {QUESTION}")
for item in response.model_dump()["output"]:
    kind = item["type"]
    if kind == "function_call":
        print(f"call     : {item['name']}({item['arguments']})")
    # TODO 2: print each tool result, so every `call` line is followed by a matching `result` line.
    #   - Add one more branch here, written like the ones around it: `elif kind.startswith("orq:"):`
    #     (the result item's type is "orq:" plus the tool key, so you cannot compare it with ==).
    #   - Inside it, print a line in the same style as the others, e.g. "result   : ...", with
    #     the tool's `item["name"]` and its `item["result"]`.
    #   - `item["result"]` is usually a dict; wrap it in json.dumps(...) (add `import json` at the
    #     top) and cut it with [:100] if you want to keep long results on one line.
    #   - Stuck? Temporarily `print(item)` for an unknown kind to see the raw item. The call item
    #     and its result item share a `call_id`, which is how orq pairs them.
    elif kind == "message":
        print(f"answer   : {''.join(part.get('text', '') for part in item['content'])}")
print(f"trace    : {response.telemetry.trace_id}")
print("next     : open the trace in the Studio; the tool spans ran in orq, not on your laptop")
