# Refund agent

| | |
|---|---|
| **Prerequisites** | onboarding done |
| **You will have** | your own refund agent at v1.0.0 with three code tools, talked to it in a browser, called it from Python, curl and the CLI, and read one trace |

## Why

The refund agent is a fully managed, versioned orq.ai agent: your app sends one message and gets one response, while orq.ai runs both the model loop and the code tools. The tools come from `app/refund_agent/tools.py`; instructions come from `app/data/instructions.md`.

Read [Business logic](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/02-logic/) for the policy, tool contracts, and v1 design. Then read [Refund agent concepts](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/02-concepts/) for the managed loop, response items, and versions.

## Steps

### Step 1 · Create your agent

Thirty people share this workspace. Your seat prefix from the email (`WS_PREFIX=ws07`) goes in front of every entity you create, so nobody overwrites anybody:

```bash {.terminal}
uv run python -m app.refund_agent.entities seed
```

This runs the `seed` command in `app/refund_agent/entities.py`. It creates the code tools, agent, dataset, and judge only when they do not already exist. `make seed-workspace` is the optional shortcut for the same command.

```text
── Seed · create this seat's entities ─────────────────
seat     : ws07 → <your project>/workshop
tools    : ws07-lookup_order, ws07-issue_refund,
           ws07-get_policy (code tools, run by orq.ai)
agent    : ws07-refund-agent v1.0.0
dataset  : ws07-refund-eval (01M4…)
judge    : ws07-refund-policy-judge (01M4…)
```

The dataset and the judge are for the fix-and-eval module. The seed command is safe to run again: it only creates what is missing and never changes an existing agent. It refuses to run with an empty or made-up `WS_PREFIX`. `uv run python -m app.refund_agent.entities reset` deletes your seat's entities, and only those.

**What the seeder teaches.** `app/refund_agent/entities.py` is deliberately an infrastructure boundary. It turns the local source files into durable orq.ai entities once: `tools.py` becomes code tools, `instructions.md` becomes the initial agent version, and `dataset.jsonl` becomes the evaluation dataset. The rest of the application uses their keys; it does not carry API payloads or tool implementations around.

```python {.code-frame}
from app.refund_agent.entities import ensure_tools

# The agent configuration stores references to hosted code tools.
tool_keys = ensure_tools(orq)
settings={"},{
    "max_iterations": 8,
    "max_execution_time": 120,
    "tools": [{"type": "code", "key": tool_key} for tool_key in tool_keys],
}
```

That boundary is useful beyond this workshop: seed or provision entities in a controlled path, then make product code invoke stable keys.

### Step 2 · Talk to it

```bash {.terminal}
uv run python -m app.web
# Then open http://127.0.0.1:8002
```

This starts the local FastHTML chat application. `make agent-chat-ui` is its shortcut.

The left panel, **Backend (mock) · read-only**, shows the data the code tools were built from: **Orders** (what `lookup_order` and `issue_refund` see) and **Policies** (what `get_policy` returns). The right panel is the chat. Click a **Try these** prompt, or write your own. Each answer shows a chip per tool call (a red chip is a tool that returned an error) and a **trace** link.

![The chat UI: the mock backend on the left with the six orders of the logged-in customer, the chat on the right with an answer, its tool chips and the trace link.](assets/chat-ui.png)

Open a trace link. The trace shows the model calls and one span per tool call, run in orq.ai.

![A refund trace in the Studio: the agent span, two gpt-6-luna calls and the lookup_order and issue_refund tool spans with a sandbox execute; the issue_refund span shows its arguments and the result amount_refunded 89.](assets/agent-trace.png)

### Step 3 · Inspect and call it from Python

Open `modules/02-refund-agent/run.py`. It has two TODOs: the call itself, and printing each tool result.

```bash {.terminal}
uv run python modules/02-refund-agent/run.py
```

`make invoke-agent` is the shortcut for this exact file.

Expected output once the TODOs are done:

```text
── Step 1 · Inspect the agent ─────────────────────────
agent    : ws07-refund-agent v1.0.0
model    : openai/gpt-6-luna
tools    : ws07-lookup_order, ws07-issue_refund, ws07-get_policy
limits   : max_iterations 8, max_execution_time 120s
── Step 2 · Call it and read the output items ─────────
question : Please refund ord_a2, the dock does not fit my laptop.
call     : ws07-lookup_order({"order_id":"ord_a2"})
result   : ws07-lookup_order -> {"ok": true, "order": {
             "amount": 89, "delivered_days_ago": 15, ...
           }}
call     : ws07-issue_refund(
             {"order_id":"ord_a2", "post_window_exception":false,
              "reason":"dock does not fit laptop"}
           )
result   : ws07-issue_refund -> {"amount_refunded": 89,
             "currency": "EUR", "ok": true, "order_id": "ord_a2"}
answer   : Your refund of €89 for order ord_a2 has been issued
           to your original payment method.
trace    : 879452279575c96235e1da68b34cd543
```

A tool call is a `function_call` output item; orq.ai runs it and adds an `orq:<tool key>` item with the same `call_id` and the `result`. Stuck? See the hint at the end of this page.

**What to read in `run.py`.** The call itself is intentionally one line. The important learning is the response shape: application code should preserve the final answer, structured calls, structured results, and trace ID rather than flattening everything into text. That same structured record powers the chat UI, traces, simulations, and regression scorers later.

```python {.code-frame}
from app.refund_agent.client import ask_agent

turn = ask_agent(QUESTION, version="1.0.0")
print(turn.answer)
for call in turn.tool_calls:
    print(call.name, call.arguments, call.result)
print(turn.trace_id)
```

### Step 4 · The same call from Python, curl and the CLI

=== "Python SDK"

    Use this in application code. `make_orq()` reads the API key and router URL from `.env`; `parse_turn()` is the workshop helper that gives you a clean answer, tool calls, results, and trace ID.

    ```python {.code-frame}
    from app.refund_agent.client import ask_agent

    turn = ask_agent(
        "Refund ord_a1, I changed my mind.",
        version="1.0.0",  # pin the version
    )

    print(turn.answer)
    for call in turn.tool_calls:
        print(call.name, call.arguments, call.result)
    print(turn.trace_id)
    ```

=== "curl"

    Use this to inspect the raw Responses API request and raw output items. It assumes you completed the once-per-terminal environment setup in Onboarding.

    ```bash {.terminal}
    curl -s https://my.orq.ai/v3/router/responses \
      -H "Authorization: Bearer $ORQ_API_KEY" \
      -H "Content-Type: application/json" \
      --data "{
        \"model\": \"agent/${WS_PREFIX}-refund-agent@1.0.0\",
        \"input\": \"Refund ord_a1, I changed my mind.\"
      }" \
      | jq '.output[] | {type, name, arguments, result}'
    ```

=== "orq.ai CLI"

    Use this to reproduce the same request quickly from a terminal without writing a script.

    ```bash {.terminal}
    orq responses create \
      --model "agent/${WS_PREFIX}-refund-agent@1.0.0" \
      --input '"Refund ord_a1, I changed my mind."' \
      -o json
    ```

These are three views of one contract:

| Surface | What you write | When it is useful |
|---|---|---|
| Python SDK | `orq.responses.create(...)` | product code; typed entity and response helpers |
| curl | HTTP method, headers, JSON body | inspect the exact gateway request and response |
| `orq` CLI | model and input flags | reproduce a call quickly from a terminal |

In every case, `model="agent/<key>[@<version>]"` selects the managed agent, `input` starts the turn, and `output` contains the message plus the intermediate work. The API key stays in `.env`; none of these examples require copying it into source code.

`agent/<key>` is the latest version. `agent/<key>@1.0.0` pins one; the chat UI's version picker does the same.

The Python SDK, raw HTTP call, and CLI all use the same Responses API contract. Use the SDK in application code for typed clients and convenient entity management; use HTTP or the CLI when debugging an exact request, automating a shell workflow, or comparing raw output items.

### Step 5 · Read the resources in the Studio

Open **Agents** > your `-refund-agent` > **Versions**. There is one version today. Then open one tool under **Tools**: the Python that orq.ai runs, generated from `tools.py`.

**Agent view — read configuration, not source code.** On the agent version, inspect these fields in order: the **model** answers the question “which model is called?”, **instructions** answers “what is it told to do?”, **tools** answers “what actions can it request?”, and **limits** answers “when does the loop stop?”. An agent is a composed resource, so this is the best screen for understanding a version as a whole.

![The agent's settings in the Studio: role, description, model gpt-6-luna and the three code tools ws01-lookup_order, ws01-issue_refund, ws01-get_policy.](assets/agent-tools.png)

**Code-tool view — read the executable policy.** Open `issue_refund` and look for its parameters first, then the ordered early returns, then the successful result. The schema is what the model may request; the Python is what orq.ai actually executes. The fixture is deliberately visible here so you can recognize the boundary between example data and enforcement logic.

![The ws01-issue_refund code tool in the Studio: the generated header comment, the window and limit constants, and the start of the order fixture.](assets/tool-code.png)

A model has no equivalent code editor: it is selected as a configuration value on the agent. The code you can inspect lives in the tool resource; the prompt you can inspect lives in the agent version; the request and result you can inspect live in the trace.

## Hint

??? tip "TODO 1 and 2"
    The call is `orq.responses.create(model=f"agent/{settings.agent_key}", input=QUESTION)`. For TODO 2, `item["result"]` is a dict; `json.dumps` it. The complete file is on the public `solution` branch: `git show origin/solution:modules/02-refund-agent/run.py`.

## Official docs

- [Build Agents](https://docs.orq.ai/ai-studio/ai-engineering/build-agents): instructions, model, tools, versions
- [Create Tools](https://docs.orq.ai/ai-studio/ai-engineering/create-tools): Python (code) tools, HTTP and function tools
- [Run Agents](https://docs.orq.ai/ai-studio/ai-engineering/run-agents): `agent/<key>` on the Responses API, from Python, curl and the CLI
- [orq.ai Python SDK](https://github.com/orq-ai/orq-python): the `orq_ai_sdk` package and API examples
- [Responses API](https://docs.orq.ai/ai-gateway/features/responses-api): output items, streaming, conversation state
- [Traces](https://docs.orq.ai/ai-studio/observability/traces): the agent's spans and tool calls

## Done when

`uv run python modules/02-refund-agent/run.py` prints every tool call with its result, and you have opened one trace in the Studio.
