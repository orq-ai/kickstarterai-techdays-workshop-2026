# Build the Agent

| | |
|---|---|
| **Prerequisites** | onboarding done |
| **You will have** | a versioned refund agent with three hosted code tools, one completed Python call, and an inspected trace |

## Why

The refund agent is a fully managed, versioned orq.ai agent: your app sends one message and gets one response, while orq.ai runs both the model loop and the code tools. The tools come from `app/refund_agent/tools.py`; instructions come from `app/data/instructions.md`.

Foundations covers the generic agent loop; [Use Case](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/02-logic/) defines the refund requirements and [Agent Design](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/02-solution-design/) shows the v1 approach.

## Steps

### Step 1 · Create the refund agent

Your seat prefix from the email (`WS_PREFIX=ws07`) goes in front of every entity you create, keeping your agent and evaluation resources separate from other participants:

The seed command creates the code tools and refund agent only when they do not already exist. `make seed-workspace` runs `uv run python -m app.refund_agent.entities seed`.

Example session (your seat prefix and entity IDs will differ):

<!-- termynal -->

```console
$ make seed-workspace
── Seed · create this seat's agent ───────────────────
seat     : ws07 → <your project>/workshop
tools    : ws07-lookup_order, ws07-issue_refund, ws07-get_policy (code tools, run by orq)
agent    : ws07-refund-agent v1.0.0
```

The dataset and policy judge are introduced in Improve and Evaluate. The seed command is safe to run again: it only creates what is missing and never changes an existing agent. It refuses to run with an empty or made-up `WS_PREFIX`. `uv run python -m app.refund_agent.entities reset` deletes your seat's entities, and only those.

### What this command creates

The seed script reads the local agent sources and creates the matching orq.ai resources:

| Local source | Resource created in orq.ai |
|---|---|
| `app/refund_agent/tools.py` | Three hosted code tools |
| `app/data/instructions.md` | The first refund-agent version |

Afterward, the chat UI and scripts use the resource keys. They invoke the managed agent; they do not run the tool implementation on your laptop. Improve and Evaluate creates its dataset and policy judge when that module needs them.

??? info "Optional: Inspect the SDK calls and agent settings"
    **The SDK calls behind seed**

    `ensure_tools()` creates each hosted code tool from the local Python source. `ensure_agent()` attaches those tool keys to the managed agent.

    ```python {.code-frame}
    # app/refund_agent/entities.py: one hosted code tool per schema
    orq.tools.create(
        request={
            "type": "code",
            "key": settings.key(function["name"]),
            "path": settings.path,
            "description": function["description"],
            "code_tool": {
                "language": "python",
                "code": hosted_tool_code(function["name"]),
                "parameters": strict_parameters(function),
            },
        },
    )
    ```

    **What seed configures**

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

### Step 2 · Read the resources in the Studio

Open [**Agents** in the workshop workspace](https://my.orq.ai/kickstartai-workshop-2026/agents), search for your `WS_PREFIX`, and open `-refund-agent`. Everything below is read-only; the full v1 instructions are left for the Improve and Evaluate module, after Agent Simulation.

| Where in the Studio | What to check |
|---|---|
| **Settings** tab of the agent | The role and description, the model, and three attached tools: `lookup_order`, `issue_refund` and `get_policy`. |
| **Versions** tab | A single version, v1.0.0. The limits show up here after your first call. |
| **Tools** → `issue_refund` → **Tool Definition** | The Python that orq.ai runs, generated from `tools.py`. |

**Code-tool view: read the executable policy.** The schema is what the model may request; the Python is what orq.ai actually executes. Open `issue_refund` and read it top to bottom:

1. A header comment: the code is generated by `make seed-workspace`, and orq passes the call's arguments in `params`.
2. Three constants: the 30-day window, the EUR 500 limit and the allowed post-window reasons.
3. `_FIXTURE`, the sample orders. It is long, so scroll past it; it is visible on purpose, so you can tell example data from enforcement logic.
4. `OrderStore`, which decides whether an order belongs to the signed-in customer.
5. `issue_refund(...)`: the ordered early returns (`not_found`, `already_refunded`, `above_limit_needs_human_review`, `outside_window`) and then the successful result. This is the part that decides.
6. The last line calls it with `params` and leaves the outcome in `result`.

A model has no equivalent code editor: it is selected as a configuration value on the agent. The code you can inspect lives in the tool resource; the prompt you can inspect lives in the agent version; the request and result you can inspect live in the trace.

### Step 3 · Inspect and call it from Python

Open `modules/02-refund-agent/run.py`. Complete these two TODOs before you run it:

| TODO | Where | What to implement | Done when |
|---|---|---|---|
| 1 | `response = None` | Call `orq.responses.create()` with `model=f"agent/{settings.agent_key}"` and `input=QUESTION`. | The script reaches the output-item loop instead of stopping with `TODO 1`. |
| 2 | The `for item in response...` loop | Add the branch for an item whose type starts with `orq:` and print its `name` and `result`. | Every `call` line in the output has a matching `result` line. |

Do not change the inspection code or the message branch. The exercise is about seeing the raw Responses API output shape: request items, managed tool results, final message, and trace ID.

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

Search the printed trace ID in **Observability** > **Traces**. The trace shows model calls and one span per hosted tool call; compare its arguments and results with the lines your script printed.

![A refund trace in Studio shows the agent, model calls, and lookup_order and issue_refund tool spans, including the result amount_refunded 89.](assets/agent-trace.png)

### Optional · Chat with the agent

```bash {.terminal}
uv run python -m app.web
# Then open http://127.0.0.1:8002
```

This starts the local chat application. `make agent-chat-ui` is its shortcut.

The **Workshop orders** panel shows the read-only data the code tools were built from: **Orders** (what `lookup_order` and `issue_refund` see) and **Policies** (what `get_policy` returns). On a small screen, open it with **Reference data**. In the chat, choose one of the welcome prompt cards or write your own. Each answer shows a chip per tool call and an **Open trace** link.

![The chat UI: Workshop orders on the left with six read-only order cards, and a v1.0.0 refund conversation on the right with tool chips and an Open trace link.](assets/chat-ui.png)

The chat UI offers another way to open the same traces when you have more time.

### Optional · Call through Python, curl or the CLI

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



## Official docs

- [Build Agents](https://docs.orq.ai/ai-studio/ai-engineering/build-agents): instructions, model, tools, versions
- [Create Tools](https://docs.orq.ai/ai-studio/ai-engineering/create-tools): Python (code) tools, HTTP and function tools
- [Run Agents](https://docs.orq.ai/ai-studio/ai-engineering/run-agents): `agent/<key>` on the Responses API, from Python, curl and the CLI
- [orq.ai Python SDK](https://github.com/orq-ai/orq-python): the `orq_ai_sdk` package and API examples
- [Responses API](https://docs.orq.ai/ai-gateway/features/responses-api): output items, streaming, conversation state
- [Traces](https://docs.orq.ai/ai-studio/observability/traces): the agent's spans and tool calls

## Done when

`make invoke-agent` prints every tool call with its result, and you have inspected its trace in Studio. The chat UI and other API surfaces are optional.

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
