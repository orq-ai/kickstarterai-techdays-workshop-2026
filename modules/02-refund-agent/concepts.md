# Refund agent concepts

A managed agent combines a model's judgment with tools that enforce the business rules.

Read [Refund logic](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/02-logic/) for the policy, tool contracts, and v1 design this agent uses.

## What an agent is

An agent is a model, instructions, and tools running in a loop until it can answer. The model decides whether it has enough information, needs a tool, or should respond to the customer.

![Inside orq.ai, the model either returns an answer or calls a code tool; the tool result returns to the model, and the loop ends on an answer or its configured limits.](assets/agent-loop.png)

## The loop orq.ai runs

Your application sends one customer message and receives one response. In between, orq.ai runs the model and the code tools in its sandbox. The result of each tool call is added to the model context before the next decision.

The refund agent stops when it answers, after `max_iterations: 8`, or after `max_execution_time: 120` seconds. Those limits are part of `entities.ensure_agent`.

| Setting | v1 value | Why it matters |
|---|---|---|
| Model | `settings.model` from `MODEL` in `.env` | The workshop can choose a model without editing module code. |
| Reasoning effort | `none` | Required by the selected model when it uses hosted code tools. |
| Maximum iterations | `8` | Caps model/tool-loop turns. |
| Maximum execution time | `120` seconds | Caps the entire managed-agent run. |
| Tools | three hosted `code` tools | orq.ai executes the order, policy, and refund code. |
| Versioning | major increments on publish | Pins a complete agent configuration for comparison. |

```python {.code-frame}
# app/refund_agent/entities.py
orq.agents.create(
    key=settings.agent_key,
    instructions=agent_instructions(),
    path=settings.path,
    model={
        "id": settings.model,
        "parameters": {"reasoning_effort": "none"},
    },
    settings={
        "max_iterations": 8,
        "max_execution_time": 120,
        "tools": [
            {"type": "code", "key": tool_key}
            for tool_key in tool_keys
        ],
    },
)
```

This v1 agent does not configure fallback models, memory stores, knowledge bases, cost caps, or interactive tool gates. The application does not dispatch its tools itself: it gives orq.ai the agent configuration; orq.ai owns the loop and the sandbox execution.

## One turn on the wire

A turn is one `responses.create(model="agent/<key>@1.0.0")` call. Its output items show the work: a `function_call` with a name and arguments, an `orq:<tool>` item with the result and the same `call_id`, then a `message` and `telemetry.trace_id`.

`client.parse_turn` pairs those items; the chat UI renders the paired calls as tool chips. For example, a refund request can lead to `lookup_order`, `get_policy`, and `issue_refund` before the final message.

```python {.code-frame}
# app/refund_agent/client.py
from app.refund_agent.client import make_orq
from app.refund_agent.config import settings

orq = make_orq()
response = orq.responses.create(
    model=f"agent/{settings.agent_key}@1.0.0",
    input="Please refund ord_a2.",
)

# A function_call requests work; orq:<tool> supplies its result.
if kind == "function_call":
    calls[call_id] = ToolCall(name=name, arguments=arguments)
elif kind.startswith("orq:"):
    calls[call_id].result = result
```

![An application sends a message to a managed agent; the model requests a function call, orq.ai executes the code tool, returns an orq.ai tool-result item to the model, and returns a message with a trace ID.](assets/agent-turn-sequence.png)

## An entity with versions

The refund agent is an orq.ai entity containing instructions, a model, tool schemas, generated code tools, limits, and versions. Pinning `@1.0.0` makes a call reproducible. Publishing changed instructions creates a new major version; there is no separate deployment to manage.

The important SDK distinction is **configuration versus invocation**. `orq.agents.create()` configures a durable entity. `orq.responses.create()` runs one turn against it. A workshop application should not rebuild an agent on every request.

```python {.code-frame}
from app.refund_agent.client import make_orq
from app.refund_agent.config import settings

orq = make_orq()

# Configure once: app/refund_agent/entities.py
orq.agents.create(key=settings.agent_key, instructions=instructions, ...)

# Invoke many times: app/refund_agent/client.py
turn = orq.responses.create(
    model=f"agent/{settings.agent_key}@1.0.0",
    input=customer_message,
)
```

![The managed refund-agent entity in orq.ai contains its instructions, model, tool schemas, code tools, limits, and version history; the application only starts a conversation and receives its result.](assets/managed-agent-loop.png)

## Where the rules live

Tools enforce hard constraints: order ownership, one refund only, the EUR 500 ceiling, and the refund window. The prompt supplies judgment about how and when to use them. That separation matters: the prompt can make a bad decision even while a tool correctly refuses the resulting call.

A tool schema is also a contract with the model: its name, argument shape, and description constrain what the model can request. Its returned `ok` and `error` fields are the contract with the rest of the system. This is why traces and evaluators inspect structured tool results instead of guessing from prose.

```python {.code-frame}
# app/refund_agent/tools.py — the tool is the hard boundary
# issue_refund(store: OrderStore, order_id: str, ...) -> dict
order = store.owned(order_id)
if order is None:
    return {"ok": False, "error": "not_found"}
if order["amount"] > REFUND_LIMIT_EUR:
    return {"ok": False, "error": "above_limit_needs_human_review"}
```

## Official docs

- [Build Agents](https://docs.orq.ai/ai-studio/ai-engineering/build-agents)
- [Create Tools](https://docs.orq.ai/ai-studio/ai-engineering/create-tools)
- [Run Agents](https://docs.orq.ai/ai-studio/ai-engineering/run-agents)
- [Responses API](https://docs.orq.ai/ai-gateway/features/responses-api)
- [Traces](https://docs.orq.ai/ai-studio/observability/traces)
