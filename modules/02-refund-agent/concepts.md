# Agent concepts

A managed agent begins with instructions and a model. Tools are optional; add them when the agent needs information or must take action.

Start with the hello agent from this repository. The refund case adds business rules only after the basic invocation makes sense.

## What an agent is

An agent is a model, instructions, and optional tools running in a loop until it can answer. The model decides whether it has enough information, needs a tool, or should respond to the customer.

### A hello agent

```python {.code-frame}
# Excerpt from modules/02-refund-agent/hello_agent.py
HELLO_KEY = settings.key("hello-agent")  # your seat's key
orq.agents.create(
    key=HELLO_KEY,
    display_name="Hello agent",
    role="Greeting assistant.",
    description="Greets a customer in one friendly sentence.",
    instructions="Greet the customer in one friendly sentence.",
    path=settings.path,
    model={"id": settings.model, "parameters": {"reasoning_effort": "none"}},
    settings={"max_iterations": 1, "max_execution_time": 30},
)
response = orq.responses.create(model=f"agent/{HELLO_KEY}", input="Hello")
```

The excerpt shows the two SDK operations; the runnable file checks whether the agent already exists before creating it.

The instructions tell the model what to do; the model supplies the language. The application sends one input and receives one response. That is already a managed agent, even without tools.

Run the minimal example:

```bash {.terminal}
uv run python modules/02-refund-agent/hello_agent.py
```

`hello_agent.py` creates `agent/<WS_PREFIX>-hello-agent` only when needed, sends it `Hello`, and prints its response and trace ID. It uses one instruction, one model, no tools, `max_iterations: 1`, and a 30-second limit.

![Inside orq.ai, the model either returns an answer or calls a code tool; the tool result returns to the model, and the loop ends on an answer or its configured limits.](assets/agent-loop.png)

### One simple tool call

Imagine attaching a hosted `get_weather(city)` tool. If a customer asks about the weather, the model can request it instead of guessing. This is a conceptual example: the runnable hello agent has no tools.

```python {.code-frame}
# The model asks for structured work.
{
    "type": "function_call",
    "name": "get_weather",
    "call_id": "call_1",
    "arguments": '{"city":"Paris"}',
}

# orq.ai executes the hosted tool and returns structured evidence.
{
    "type": "orq:get_weather",
    "call_id": "call_1",
    "result": {"temperature_c": 18, "condition": "clear"},
}
```

The important pattern is not weather. It is the loop: **model decision → tool result → model decision → answer**. The refund agent uses the same loop with business-specific tools.

## The loop orq.ai runs

Your application sends one customer message and receives one response. In between, orq.ai runs the model and the code tools in its sandbox. The result of each tool call is added to the model context before the next decision.

The loop ends when the model answers or reaches the limits set on the agent. The refund agent’s actual prompt, tools, and configuration appear in [Solution design](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/02-solution-design/) and the Tutorial.

## One turn on the wire

A hello turn is one `responses.create(model=f"agent/{HELLO_KEY}")` call. The response contains a `message` item and a `telemetry.trace_id`. The runnable file uses `parse_turn(response)` to print the answer and trace ID. It does not need a tool call to produce a trace.

When an agent has tools, the same response shape gains a `function_call` item with a name and arguments. orq.ai executes the hosted tool and adds an `orq:<tool>` item with the matching `call_id` and result before the final message. The refund solution uses that extended shape later.

![An application sends a message to a managed agent; the model requests a function call, orq.ai executes the code tool, returns an orq.ai tool-result item to the model, and returns a message with a trace ID.](assets/agent-turn-sequence.png)

## An entity with versions

A managed agent is an orq.ai entity containing instructions, a model, optional tools, limits, and versions. Pinning `@1.0.0` makes a call reproducible. Publishing a change creates a new version; there is no separate deployment to manage.

The important SDK distinction is **configuration versus invocation**. `orq.agents.create()` configures a durable entity. `orq.responses.create()` runs one turn against it. A workshop application should not rebuild an agent on every request.

The hello script creates its agent only if the seat-prefixed key is missing. Subsequent calls can use `agent/<key>` for the latest version, or `agent/<key>@1.0.0` to pin the first. The refund agent follows the same pattern with tools and additional limits.

![A managed agent entity in orq.ai contains its instructions, model, optional tools, limits, and version history; an application starts a conversation and receives its result.](assets/managed-agent-loop.png)

## Prompt guidance and tool evidence

A tool schema is a contract with the model: its name, argument shape, and description constrain what the model can request. The tool result is evidence the model can use in the next loop turn.

In the weather illustration, the prompt can decide **when** to ask `get_weather`. It cannot invent the weather result. The hosted tool returns structured data, and the model turns that data into a customer-facing answer. The refund solution applies the same separation to its business-specific policy tools.

## Next

Now apply this generic loop to the [Business case](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/02-logic/). It defines the refund requirements that the v1 [Solution design](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/02-solution-design/) must meet.

## Official docs

- [Build Agents](https://docs.orq.ai/ai-studio/ai-engineering/build-agents)
- [Create Tools](https://docs.orq.ai/ai-studio/ai-engineering/create-tools)
- [Run Agents](https://docs.orq.ai/ai-studio/ai-engineering/run-agents)
- [Responses API](https://docs.orq.ai/ai-gateway/features/responses-api)
- [Traces](https://docs.orq.ai/ai-studio/observability/traces)
