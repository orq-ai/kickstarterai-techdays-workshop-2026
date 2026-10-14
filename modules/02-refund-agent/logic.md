# Refund logic

The refund agent is a small customer-service system: the prompt handles conversation, while code tools enforce what may happen.

## The business problem

Lumen Goods sells home and tech accessories to customers in the EU and UK. A customer is already signed in when they talk to the agent, so the system has a session identity but the model does not receive a customer ID as a tool argument.

The agent handles refund requests only. Shipping status, billing disputes, account changes, and product advice go to human support. This narrow scope keeps the tools and evaluation focused on one business decision: whether a specific order can be refunded automatically.

## The refund policy

The standard path is deliberately simple:

| Check | Automatic outcome |
|---|---|
| Order belongs to the signed-in customer | Continue |
| Delivered within 30 days | Refund for any reason |
| Already refunded | Refuse |
| Above EUR 500 | Route to human review |
| Outside 30 days | Require one listed exception and supporting evidence |

The listed post-window exceptions are damaged in transit, never received, and defective on arrival. Each needs evidence appropriate to the claim. If a request is outside the refund agent's scope, or cannot be established from the available evidence, it goes to human support rather than becoming a new automatic rule.

## Where the rules live

`app/data/kb/` holds the policy text. `app/refund_agent/tools.py` turns the non-negotiable parts into executable checks. The model can request an action, but it cannot bypass a tool's result.

```python {.code-frame}
# app/refund_agent/tools.py
order = store.owned(order_id)
if order is None:
    return {"ok": False, "error": "not_found"}
if order["refunded"]:
    return {"ok": False, "error": "already_refunded"}
if order["amount"] > REFUND_LIMIT_EUR:
    return {
        "ok": False,
        "error": "above_limit_needs_human_review",
    }
```

The error value is part of the business contract. It lets the model explain the outcome without exposing internal records, and lets an evaluator distinguish a successful refund from a failed request.

## The three tool contracts

| Tool | Model asks for | Tool guarantees | Important result |
|---|---|---|---|
| `lookup_order` | an order ID | ownership check; internal fields removed; window computed | public order data or `not_found` |
| `get_policy` | a policy topic | one authoritative local policy document | policy text or `unknown_topic` |
| `issue_refund` | order ID, reason, exception flag | ownership, duplicate, limit, and window checks | `ok: true` and refunded amount, or an error |

The schemas describe these contracts to the model. The hosted code tools are generated from the same local source, so the unit-tested rules in this repository are the rules orq.ai executes.

```python {.code-frame}
# app/refund_agent/tools.py
issue_refund_schema = TOOL_SCHEMAS[1]["function"]

issue_refund_schema["parameters"]["required"]
# ["order_id", "reason"]

issue_refund_schema["parameters"]["properties"]
# order_id, reason, post_window_exception
```

## The v1 design

`app/data/instructions.md` is the initial system prompt. It tells the model to look up an order before deciding, read policy when needed, apply the stated eligibility rules, and communicate warmly and concisely.

The prompt is intentionally a **baseline**, not the source of truth. It guides the model through ambiguous language and tool selection. The tools enforce deterministic boundaries, and the next modules test whether the complete v1 system makes the right decisions and communicates them safely.

```python {.code-frame}
from app.refund_agent.config import settings

# app/refund_agent/entities.py
orq.agents.create(
    key=settings.agent_key,
    instructions=agent_instructions(),
    model={"id": settings.model},
    settings={"tools": [{"type": "code", "key": tool_key}]},
)
```

Take away this separation: **policy text explains**, **prompt instructions guide**, and **tool code enforces**. A later evaluation can inspect both the final customer message and the tool-result trail.

## Official docs

- [Create Tools](https://docs.orq.ai/ai-studio/ai-engineering/create-tools): code-tool contracts and hosted execution
- [Build Agents](https://docs.orq.ai/ai-studio/ai-engineering/build-agents): instructions, tools, limits, and versions
- [Run Agents](https://docs.orq.ai/ai-studio/ai-engineering/run-agents): managed agent calls through the Responses API
- [Traces](https://docs.orq.ai/ai-studio/observability/traces): inspect model and tool execution
