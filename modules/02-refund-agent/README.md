# Refund agent

!!! abstract "12-Factor Agents · Factor 4: tools are structured outputs"
    The model never touches the order database. It emits a JSON call (`issue_refund(order_id, reason, post_window_exception)`), and code decides: ownership, the 30-day window, the EUR 500 limit. Here that code runs inside orq as a code tool, next to the agent.

| | |
|---|---|
| **Time** | 15 min |
| **Prerequisites** | onboarding done |
| **You will have** | talked to your agent in a browser, called it from Python, curl and the CLI, and read one trace |

## Why

The refund agent for Lumen Goods is 100 % managed: instructions, model, three tools and limits are one entity in orq, with versions. Your laptop sends a message; orq runs the model loop *and* the tools, and returns every tool call with its result. That is also what makes it testable from the outside, which the next two modules do.

| Tool | What it does |
|---|---|
| `lookup_order(order_id)` | one of the logged-in customer's orders; another customer's order is `not_found` |
| `get_policy(topic)` | the refund policy text, by topic |
| `issue_refund(order_id, reason, post_window_exception)` | refunds once, within 30 days and EUR 500, or outside the window for a listed reason |

The tools are generated from `app/refund_agent/tools.py` by `make seed-workspace`. One ceiling to know: each tool call starts from the same orders, so a refund is not remembered between calls.

## Steps

### Step 1 · Talk to it

```bash
make agent-chat-ui              # then open http://127.0.0.1:8002
```

The left panel, **Backend (mock) · read-only**, shows the data the code tools were built from: **Orders** (what `lookup_order` and `issue_refund` see) and **Policies** (what `get_policy` returns). The right panel is the chat. Click a **Try these** prompt, or write your own. Each answer shows a chip per tool call (a red chip is a tool that returned an error) and a **trace** link.

![The chat UI: the mock backend on the left with the six orders of the logged-in customer, the chat on the right with an answer, its tool chips and the trace link.](assets/chat-ui.png)

Open a trace link. The trace shows the model calls and one span per tool call, run in orq.

### Step 2 · Inspect and call it from Python

Open `modules/02-refund-agent/run.py`. It has two TODOs: the call itself, and printing each tool result.

```bash
make invoke-agent               # or: uv run python modules/02-refund-agent/run.py
```

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
result   : ws07-lookup_order -> {"ok": true, "order": {"amount": 89, "delivered_days_ago": 15, ...
call     : ws07-issue_refund({"order_id":"ord_a2","post_window_exception":false,"reason":"dock does not fit laptop"})
result   : ws07-issue_refund -> {"amount_refunded": 89, "currency": "EUR", "ok": true, "order_id": "ord_a2"}
answer   : Your refund of €89 for order ord_a2 has been issued to your original payment method.
trace    : 879452279575c96235e1da68b34cd543
```

A tool call is a `function_call` output item; orq runs it and adds an `orq:<tool key>` item with the same `call_id` and the `result`. Stuck? See the hint at the end of this page.

### Step 3 · The same call from curl and the CLI

```bash
set -a; source .env; set +a
curl -s https://my.orq.ai/v3/router/responses \
  -H "Authorization: Bearer $ORQ_API_KEY" -H "Content-Type: application/json" \
  -d "{\"model\": \"agent/${WS_PREFIX}-refund-agent\", \"input\": \"Refund ord_a1, I changed my mind.\"}" | jq '.output[] | {type, name, result}'

orq responses create --model "agent/${WS_PREFIX}-refund-agent" --input '"Refund ord_a1, I changed my mind."' -o json
```

`agent/<key>` is the latest version. `agent/<key>@1.0.0` pins one; the chat UI's version picker does the same.

### Step 4 · Versions in the Studio

Open **Agents** > your `-refund-agent` > **Versions**. There is one version today. Then open one tool under **Tools**: the Python that orq runs, generated from `tools.py`.

## Hint

??? tip "TODO 1 and 2"
    The call is `orq.responses.create(model=f"agent/{settings.agent_key}", input=QUESTION)`. For TODO 2, `item["result"]` is a dict; `json.dumps` it. The complete file is on the public `solution` branch: `git show origin/solution:modules/02-refund-agent/run.py`.

## Done when

`make invoke-agent` prints every tool call with its result, and you have opened one trace in the Studio.
