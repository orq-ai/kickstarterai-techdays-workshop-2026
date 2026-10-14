# Agent Design

The v1 solution combines a system prompt, policy-backed hosted code tools, and agent settings into one managed orq.ai agent.

## The v1 system

![Diagram: A customer message enters the version-one prompt and model; the model requests hosted code tools backed by policy and hard rules, receives structured results, and returns a response with a trace.](assets/refund-logic-system.png)

The prompt guides conversation and tool selection. Hosted code tools enforce the business rules. The model can request an action, but a structured tool result determines whether that action succeeded.

## One refund decision

```python {.code-frame}
# 1. Start with facts the customer cannot choose.
order = lookup_order(order_id)
if not order["ok"]:
    return explain("I cannot find that order")

# 2. Use policy text when the eligibility path is unclear.
if not order["order"]["within_standard_window"]:
    policy = get_policy("post_window_exceptions")
    if not eligible_exception(customer_reason, evidence, policy):
        return route_to_human_review()

# 3. Ask the enforcement tool to make the state change.
refund = issue_refund(order_id, reason, post_window_exception=exception)
return explain(refund)  # success and failure are structured results
```

The model chooses what to say and which tool to call next. It does not calculate ownership, invent eligibility, or mark an order refunded itself.

## Tool contracts and enforcement

`app/data/kb/` holds policy text. `app/refund_agent/tools.py` turns the non-negotiable parts into executable checks.

```python {.code-frame}
# app/refund_agent/tools.py — the tool is the hard boundary
# issue_refund(store: OrderStore, order_id: str, ...) -> dict
order = store.owned(order_id)
if order is None:
    return {"ok": False, "error": "not_found"}
if order["amount"] > REFUND_LIMIT_EUR:
    return {"ok": False, "error": "above_limit_needs_human_review"}
```

Tools enforce ownership, refund state, the EUR 500 ceiling, and the refund window. The prompt supplies judgment about how and when to use them. A tool schema is also a contract with the model: its name, argument shape, and description constrain what the model can request. Its returned `ok` and `error` fields are the contract with the rest of the system.

| Tool | Model asks for | Tool guarantees | Important result |
|---|---|---|---|
| `lookup_order` | an order ID | ownership check; internal fields removed; window computed | public order data or `not_found` |
| `get_policy` | a policy topic | one authoritative local policy document | policy text or `unknown_topic` |
| `issue_refund` | order ID, reason, exception flag | ownership, duplicate, limit, and window checks | `ok: true` and refunded amount, or an error |

```python {.code-frame}
# lookup_order: reveal only a session-owned, public order.
order = store.owned(order_id)
if order is None:
    return {"ok": False, "error": "not_found"}
return {"ok": True, "order": public_order(order)}
```

```python {.code-frame}
# app/refund_agent/tools.py
POLICY_TOPICS = (
    "refund_basics",
    "post_window_exceptions",
    "abuse_patterns",
    "shipping_and_scope",
)

def get_policy(topic: str) -> dict:
    if topic not in POLICY_TOPICS:
        return {"ok": False, "error": "unknown_topic"}
    return {"ok": True, "topic": topic, "text": policy_text(topic)}
```

The model supplies `topic` when it calls `get_policy`. The v1 instructions name the topics, and the tool schema exposes the same enum. For example, the model can ask for `refund_basics` before a standard decision or `post_window_exceptions` when the delivery window has passed.

```python {.code-frame}
# issue_refund: make the state change only after deterministic checks.
if not owned(order_id):
    return {"ok": False, "error": "not_found"}
if already_refunded(order_id):
    return {"ok": False, "error": "already_refunded"}
if amount(order_id) > REFUND_LIMIT_EUR:
    return {"ok": False, "error": "above_limit_needs_human_review"}
return issue_refund_result(order_id)
```

## The v1 instructions

`app/data/instructions.md` is the initial system prompt. This safe excerpt establishes the agent's role, available actions, policy baseline, and tone:

```text
You are the refund assistant for Lumen Goods.
Customers are already logged in to the storefront.

Tools:
- lookup_order: look up one of the customer's orders.
- get_policy: read the refund policy.
- issue_refund: refund an order.

How to work:
- Look up the order before you decide anything.
- Read the policy when you are not sure.
- Refunds are allowed within 30 days of delivery for any reason.
- Be warm and concise.
```

| Prompt element | What it gives the model | What it cannot guarantee |
|---|---|---|
| Role and scope | A customer-service role and refund-only task | Correct decisions in every ambiguous conversation |
| Tool descriptions | The actions it may request | That the requested action will succeed |
| Policy guidance | A natural-language starting point for eligibility | Deterministic enforcement of every rule |
| Tone instruction | A concise customer-facing style | Safe handling of every input by itself |

The full file is the artifact revised in Improve and Evaluate. The prompt shapes the model's choices; it does not replace policy source or code-tool checks.

## Next

[Build the Agent](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/02/) creates and invokes this managed agent, then lets you inspect its tool calls and traces.

## Official docs

- [Create Tools](https://docs.orq.ai/ai-studio/ai-engineering/create-tools): code-tool contracts and hosted execution
- [Build Agents](https://docs.orq.ai/ai-studio/ai-engineering/build-agents): instructions, tools, limits, and versions
- [Run Agents](https://docs.orq.ai/ai-studio/ai-engineering/run-agents): managed agent calls through the Responses API
- [Traces](https://docs.orq.ai/ai-studio/observability/traces): inspect model and tool execution
