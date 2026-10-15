# Foundations

## The agent loop

An agent is a model with instructions and, optionally, tools. orq.ai runs it in a loop: the model either answers or asks for a tool; orq.ai runs the tool and hands the result back; this repeats until the model answers or hits the agent's limits.

![Diagram: Inside orq.ai, the model either returns an answer or calls a code tool; the tool result returns to the model, and the loop ends on an answer or its configured limits.](assets/agent-loop.png)

### A hello agent

```python {.code-frame}
# Simplified from modules/02-refund-agent/hello_agent.py
orq.agents.create(
    key="your-unique-hello-agent-key",  # the script uses your seat: ws07-hello-agent
    instructions="Greet the customer in one friendly sentence.",
    path=settings.path,
    model={"id": settings.model, "parameters": {"reasoning_effort": "none"}},
)
response = orq.responses.create(model="agent/your-unique-hello-agent-key", input="Hello")
```

The instructions tell the model what to do; the model supplies the language. The application sends one input and receives one response. That is already a managed agent, even without tools.

Run the minimal example:

Example session (the answer, configured model and trace ID will vary):

<!-- termynal -->

```console
$ uv run python modules/02-refund-agent/hello_agent.py
── Hello agent ─────────────────────────────────────
agent    : ws07-hello-agent
model    : <configured model>
answer   : Hello! How can I help you today?
trace    : <your trace id>
```

The script creates `agent/<WS_PREFIX>-hello-agent` on first run, sends it `Hello`, and prints the answer and trace ID.

### One simple tool call

Imagine attaching a hosted `get_weather(city)` tool. If a customer asks about the weather, the model can request it instead of guessing. This is a conceptual example: the runnable hello agent has no tools. orq.ai ships built-in server tools such as `current_date` and `google_search`; `get_weather` here stands for any custom tool you create (a code tool, an HTTP tool, or an MCP tool), like the refund agent's tools.

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

A tool schema is a contract with the model: its name, argument shape, and description constrain what the model can request. The prompt decides **when** to ask `get_weather`; it cannot invent the weather result. The important pattern is not weather. It is the loop: **model decision → tool result → model decision → answer**. The refund agent uses the same loop with business-specific tools.

## One turn on the wire

A hello turn is one `responses.create(model="agent/<key>")` call: a `message` item plus a `telemetry.trace_id`. With tools, the same shape gains a `function_call` item and an `orq:<tool>` result item before the final message.

The agent itself is a durable entity, not something your app rebuilds per request: `orq.agents.create()` configures it; `responses.create()` runs one turn. Pinning `agent/<key>@1.0.0` makes a call reproducible; the simulation module relies on it.

![Diagram: An application sends a message to a managed agent; the model requests a function call, orq.ai executes the code tool, returns an orq.ai tool-result item to the model, and returns a message with a trace ID.](assets/agent-turn-sequence.png)

## Next

Now apply this generic loop to the [Use Case](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/02-logic/). It defines the refund requirements that the v1 [Agent Design](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/02-solution-design/) must meet.

## Official docs

- [Build Agents](https://docs.orq.ai/ai-studio/ai-engineering/build-agents)
- [Create Tools](https://docs.orq.ai/ai-studio/ai-engineering/create-tools)
- [Run Agents](https://docs.orq.ai/ai-studio/ai-engineering/run-agents)
- [Responses API](https://docs.orq.ai/ai-gateway/features/responses-api)
- [Traces](https://docs.orq.ai/ai-studio/observability/traces)
