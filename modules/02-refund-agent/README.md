# Designing an agent

| | |
|---|---|
| **Prerequisites** | onboarding done |
| **You will have** | your own refund agent at v1.0.0 with three code tools, talked to it in a browser, called it from Python, and read one trace; curl and CLI calls are optional |

## Why

The refund agent is a fully managed, versioned orq.ai agent: your app sends one message and gets one response, while orq.ai runs both the model loop and the code tools. The tools come from `app/refund_agent/tools.py`; instructions come from `app/data/instructions.md`.

Read [Agent concepts](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/02-concepts/) for the managed loop, response items, and versions. Then read the [Business case](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/02-logic/) for the policy requirements and [Solution design](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/02-solution-design/) for the v1 prompt, tools, and configuration.

### Where the agent runs

![Diagram: the chat and simulation run on your laptop and call the Orq AI Gateway. The highlighted managed refund agent and all three code tools run inside Orq, with traces in the Studio. Your coding agent can also connect through the gateway and MCP server.](assets/managed-agent-map.svg)


[Open full-size Agent architecture diagram](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/assets/managed-agent-map.svg)

The chat UI and its read-only order panel run locally. The **highlighted agent and code tools run in Orq**: the laptop sends a request and receives the answer, tool arguments and results. The order panel displays fixture data; it is not a live database that updates after a refund.

## Steps

### Step 1 · Run a hello agent

Run the smallest managed-agent example before adding refund policy or tools:

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

`hello_agent.py` creates `agent/<WS_PREFIX>-hello-agent` only if it does not exist, then sends it `Hello`. Its configuration has one instruction, one model, no tools, `max_iterations: 1`, and a 30-second limit. The response includes a trace ID, just like the refund agent will.

### Step 2 · Create the refund agent

Your seat prefix from the email (`WS_PREFIX=ws07`) goes in front of every entity you create, keeping your agent and evaluation resources separate from other participants:

The seed script creates the code tools, agent, dataset and judge only when they do not already exist. `make seed-workspace` runs `uv run python -m app.refund_agent.entities seed`.

Example session (your seat prefix and entity IDs will differ):

<!-- termynal -->

```console
$ make seed-workspace
── Seed · create this seat's entities ─────────────────
seat     : ws07 → <your project>/workshop
tools    : ws07-lookup_order, ws07-issue_refund, ws07-get_policy (code tools, run by orq)
agent    : ws07-refund-agent v1.0.0
dataset  : ws07-refund-eval (01M4…)
judge    : ws07-refund-policy-judge (01M4…)
```

The dataset and the judge are for the fix-and-eval module. The seed command is safe to run again: it only creates what is missing and never changes an existing agent. It refuses to run with an empty or made-up `WS_PREFIX`. `uv run python -m app.refund_agent.entities reset` deletes your seat's entities, and only those.

### What this command creates

The seed script reads the local source files and creates the matching orq.ai resources:

| Local source | Resource created in orq.ai |
|---|---|
| `app/refund_agent/tools.py` | Three hosted code tools |
| `app/data/instructions.md` | The first refund-agent version |
| `app/data/dataset.jsonl` | The regression-evaluation dataset |
| `app/data/judge_prompt.md` | The policy evaluator |

Afterward, the chat UI and scripts use the resource keys. They invoke the managed agent; they do not run the tool implementation on your laptop.

### What seed configures

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

This v1 agent does not configure fallback models, memory stores, knowledge bases, cost caps, or interactive tool gates. That boundary is useful beyond this workshop: seed or provision entities in a controlled path, then make product code invoke stable keys.

### Step 3 · Inspect and call it from Python

Open `modules/02-refund-agent/run.py`. It has two TODOs: the call itself, and printing each tool result.

Run `make invoke-agent` (or `uv run python modules/02-refund-agent/run.py`). Expected session once the TODOs are done; your seat, model, answer and trace ID can differ:

<!-- termynal -->

```console
$ make invoke-agent
uv run python modules/02-refund-agent/run.py
── Step 1 · Inspect the agent ─────────────────────────
agent    : ws07-refund-agent v1.0.0
model    : <configured model>
tools    : ws07-lookup_order, ws07-issue_refund, ws07-get_policy
limits   : max_iterations 8, max_execution_time 120s
── Step 2 · Call it and read the output items ─────────
question : Please refund ord_a2, the dock does not fit my laptop.
call     : ws07-lookup_order({"order_id":"ord_a2"})
result   : ws07-lookup_order -> {"ok": true, "order": {"id": "ord_a2", "amount": 89.0, "item": "Charging dock Duo", "delivered_days_
call     : ws07-issue_refund({"order_id":"ord_a2","reason":"dock does not fit laptop","post_window_exception":false})
result   : ws07-issue_refund -> {"ok": true, "order_id": "ord_a2", "amount_refunded": 89.0, "currency": "EUR"}
answer   : Your refund of €89 for order ord_a2 has been issued to your original payment method.
trace    : <your trace id>
next     : open the trace in the Studio; the tool spans ran in orq, not on your laptop
```

A tool action has two records: the model proposes a call (`function_call`), then orq executes it and returns a result (`orq:<tool key>`). Their matching `call_id` connects the request to its result. The final answer is a `message` item. TODO 2 asks you to print those result records so you can see what the tools actually did, alongside what the agent said.

A result such as `{"ok": false, "error": "outside_window"}` is a tool refusing an action under its business rules. It does not mean the tool crashed. Read the arguments and result together when you inspect a trace.

**What to read in `run.py`.** The call itself is intentionally one line. The important learning is the response shape: application code should preserve the final answer, structured calls, structured results, and trace ID rather than flattening everything into text. That same structured record powers the chat UI, traces, simulations, and regression scorers later.

```python {.code-frame}
from app.refund_agent.client import ask_agent

turn = ask_agent(QUESTION, version="1.0.0")
print(turn.answer)
for call in turn.tool_calls:
    print(call.name, call.arguments, call.result)
print(turn.trace_id)
```

### Step 4 · Talk to it

```bash {.terminal}
uv run python -m app.web
# Then open http://127.0.0.1:8002
```

This starts the local chat application. `make agent-chat-ui` is its shortcut.

The **Workshop orders** panel shows the read-only data the code tools were built from: **Orders** (what `lookup_order` and `issue_refund` see) and **Policies** (what `get_policy` returns). On a small screen, open it with **Reference data**. In the chat, choose one of the welcome prompt cards or write your own. Each answer shows a chip per tool call and an **Open trace** link.

![The chat UI: Workshop orders on the left with six read-only order cards, and a v1.0.0 refund conversation on the right with tool chips and an Open trace link.](assets/chat-ui.png)

Open a trace link. The trace shows the model calls and one span per tool call, run in orq.ai.

![A refund trace in the Studio: the agent span, two gpt-6-luna calls and the lookup_order and issue_refund tool spans with a sandbox execute; the issue_refund span shows its arguments and the result amount_refunded 89.](assets/agent-trace.png)

### Step 5 · The same call from Python, curl and the CLI

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
      | jq '.output[] | {type, name, call_id, arguments, result}'
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

### Step 6 · Read the resources in the Studio

Open [**Agents** in the workshop workspace](https://my.orq.ai/kickstartai-workshop-2026/agents) > your `-refund-agent` > **Versions**. There is one version today. Then open one tool under **Tools**: the Python that orq.ai runs, generated from `tools.py`.

**Agent view — read configuration, not source code.** On the agent version, inspect these fields in order: the **model** answers the question “which model is called?”, **instructions** answers “what is it told to do?”, **tools** answers “what actions can it request?”, and **limits** answers “when does the loop stop?”. An agent is a composed resource, so this is the best screen for understanding a version as a whole.

![The agent's settings in the Studio: role, description, model gpt-6-luna and the three code tools ws01-lookup_order, ws01-issue_refund, ws01-get_policy.](assets/agent-tools.png)

**Code-tool view — read the executable policy.** Open `issue_refund` and look for its parameters first, then the ordered early returns, then the successful result. The schema is what the model may request; the Python is what orq.ai actually executes. The fixture is deliberately visible here so you can recognize the boundary between example data and enforcement logic.

![The ws01-issue_refund code tool in the Studio: the generated header comment, the window and limit constants, and the start of the order fixture.](assets/tool-code.png){ .tool-code-crop }

A model has no equivalent code editor: it is selected as a configuration value on the agent. The code you can inspect lives in the tool resource; the prompt you can inspect lives in the agent version; the request and result you can inspect live in the trace.

## Official docs

- [Build Agents](https://docs.orq.ai/ai-studio/ai-engineering/build-agents): instructions, model, tools, versions
- [Create Tools](https://docs.orq.ai/ai-studio/ai-engineering/create-tools): Python (code) tools, HTTP and function tools
- [Run Agents](https://docs.orq.ai/ai-studio/ai-engineering/run-agents): `agent/<key>` on the Responses API, from Python, curl and the CLI
- [orq.ai Python SDK](https://github.com/orq-ai/orq-python): the `orq_ai_sdk` package and API examples
- [Responses API](https://docs.orq.ai/ai-gateway/features/responses-api): output items, streaming, conversation state
- [Traces](https://docs.orq.ai/ai-studio/observability/traces): the agent's spans and tool calls

## Done when

`make invoke-agent` prints every tool call with its result, and you have opened one trace in the Studio.

The completed [solution script](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/solution/modules/02-refund-agent/run.py) produces a session shaped like this. Your seat, configured model, tool sequence, answer and trace ID can differ. Result lines are truncated to 100 characters by the script.

<!-- termynal -->

```console
$ make invoke-agent
uv run python modules/02-refund-agent/run.py
── Step 1 · Inspect the agent ─────────────────────────
agent    : ws07-refund-agent v1.0.0
model    : <configured model>
tools    : ws07-lookup_order, ws07-issue_refund, ws07-get_policy
limits   : max_iterations 8, max_execution_time 120s
── Step 2 · Call it and read the output items ─────────
question : Please refund ord_a2, the dock does not fit my laptop.
call     : ws07-lookup_order({"order_id":"ord_a2"})
result   : ws07-lookup_order -> {"ok": true, "order": {"id": "ord_a2", "amount": 89.0, "item": "Charging dock Duo", "delivered_days_
call     : ws07-issue_refund({"order_id":"ord_a2","reason":"dock does not fit laptop","post_window_exception":false})
result   : ws07-issue_refund -> {"ok": true, "order_id": "ord_a2", "amount_refunded": 89.0, "currency": "EUR"}
answer   : Your refund of €89 for order ord_a2 has been issued to your original payment method.
trace    : <your trace id>
next     : open the trace in the Studio; the tool spans ran in orq, not on your laptop
```
