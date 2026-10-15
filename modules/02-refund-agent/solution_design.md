# Agent Design

The v1 solution combines a system prompt, policy-backed hosted code tools, and agent settings into one managed orq.ai agent.

## The v1 system

![Diagram: A customer message enters the version-one prompt and model; the model requests hosted code tools backed by policy and hard rules, receives structured results, and returns a response with a trace.](assets/refund-logic-system.png)

The prompt guides conversation and tool selection. Hosted code tools enforce the business rules. The model can request an action, but a structured tool result determines whether that action succeeded.

## One refund decision

```python {.code-frame}
# 1. Check the order exists and belongs to this customer.
order = lookup_order(order_id)
if not order["ok"]:
    return explain("I cannot find that order")

# 2. Delivered more than 30 days ago? Read the exception policy
#    and check the reason and evidence before going further.
if not order["order"]["within_standard_window"]:
    policy = get_policy("post_window_exceptions")
    if not eligible_exception(customer_reason, evidence, policy):
        return route_to_human_review()

# 3. Issue the refund. The tool runs the final checks and says if it worked.
refund = issue_refund(order_id, reason, post_window_exception=exception)
return explain(refund)  # tell the customer what the tool returned
```

The model chooses what to say and which tool to call next. It does not calculate ownership, invent eligibility, or mark an order refunded itself.

## Tool contracts and enforcement

The policy text lives in `app/data/kb/`. The rules that must never bend live in `app/refund_agent/tools.py`. The prompt decides when to call a tool; the tool decides what is allowed.

| Tool | What it does |
|---|---|
| `lookup_order` | Finds one of the customer's own orders. Any other order is `not_found`. |
| `get_policy` | Returns the text of one policy topic, such as `refund_basics`. |
| `issue_refund` | Refunds the order, but only if every check below passes. |

`issue_refund` moves money, so it runs its checks in order and stops at the first one that fails:

```python {.code-frame}
# issue_refund, simplified from app/refund_agent/tools.py
if not owned(order_id):
    return {"ok": False, "error": "not_found"}
if already_refunded(order_id):
    return {"ok": False, "error": "already_refunded"}
if amount(order_id) > 500:
    return {"ok": False, "error": "above_limit_needs_human_review"}
if outside_30_days(order_id) and not valid_exception(reason):
    return {"ok": False, "error": "outside_window"}
return {"ok": True, "amount_refunded": amount(order_id)}
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
