"""The three refund tools: pure functions over an in-memory order store.

Tools are structured outputs: the model emits JSON, a function runs it. Every tool returns a dict
with `ok`; on failure `error` is a short snake_case string the model can act on, never a stack
trace. The business rules live here and nowhere else: when a refund "outside policy" is
attempted it is a prompt problem, not a tool problem (`tests/test_tools.py` pins that down).

You never run these locally in the workshop: `make seed-workspace` copies them into orq as code
tools (`entities.hosted_tool_code`), and orq runs them on every agent call. This file stays the
single source, so the tests here test what orq runs.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .config import DATA_DIR

WINDOW_DAYS = 30  # the standard refund window, counted from delivery
REFUND_LIMIT_EUR = 500.0  # above this a human reviews
KB_DIR = DATA_DIR / "kb"  # one markdown file per policy topic, returned by get_policy
POLICY_TOPICS = ("refund_basics", "post_window_exceptions", "abuse_patterns", "shipping_and_scope")
POST_WINDOW_REASONS = ("damaged_in_transit", "never_received", "defective_on_arrival")

# Ten orders with traps: over-limit, post-window, already refunded, PII in `notes`,
# and orders that belong to another customer.
_FIXTURE = json.loads((DATA_DIR / "orders.json").read_text())


class OrderStore:
    """Per-conversation mutable state. Create a fresh one per simulated customer.

    `session_user_id` is who is logged in. It is never a tool argument: a customer cannot pick
    an identity, so the store decides what "my order" means.
    """

    def __init__(self, session_user_id: str | None = None) -> None:
        self.session_user_id = session_user_id or _FIXTURE["session_user_id"]
        self.orders: dict[str, dict[str, Any]] = {
            order["id"]: deepcopy(order) for order in _FIXTURE["orders"]
        }

    def owned(self, order_id: str) -> dict[str, Any] | None:
        """The order if it exists AND belongs to the session user; None either way otherwise."""
        order = self.orders.get(order_id)
        if order is None or order["owner_id"] != self.session_user_id:
            return None
        return order


def lookup_order(store: OrderStore, order_id: str) -> dict[str, Any]:
    """Return an order the session user owns, without its internal fields.

    Rules, in the order they run:
      1. Unknown order id, or an order owned by someone else: `not_found`. The two cases are
         deliberately indistinguishable, so the tool cannot be used to probe other customers.
      2. `owner_id` and `notes` (which may hold PII) never leave the store.
      3. `within_standard_window` is computed here so the model does not do date arithmetic.
    """
    order = store.owned(order_id)
    if order is None:
        return {"ok": False, "error": "not_found"}
    public = {key: value for key, value in order.items() if key not in ("owner_id", "notes")}
    public["within_standard_window"] = order["delivered_days_ago"] <= WINDOW_DAYS
    return {"ok": True, "order": public}


def issue_refund(
    store: OrderStore, order_id: str, reason: str, post_window_exception: bool = False
) -> dict[str, Any]:
    """Refund an order in full, once, if policy allows.

    Rules, in the order they run (the first failing one is the error returned):
      1. Ownership: the order must exist and belong to the session user, else `not_found`.
      2. No double refund: `already_refunded`.
      3. The EUR 500 limit: above it, `above_limit_needs_human_review` (with the limit).
      4. The 30-day window: outside it, `outside_window` unless `post_window_exception` is set,
         and then `reason` must be one of POST_WINDOW_REASONS, else `reason_not_in_exception_list`.
    On success the store is updated and the refunded amount comes back in EUR.
    """
    order = store.owned(order_id)
    if order is None:
        return {"ok": False, "error": "not_found"}
    if order["refunded"]:
        return {"ok": False, "error": "already_refunded"}
    if order["amount"] > REFUND_LIMIT_EUR:
        return {
            "ok": False,
            "error": "above_limit_needs_human_review",
            "limit_eur": REFUND_LIMIT_EUR,
        }
    if order["delivered_days_ago"] > WINDOW_DAYS:
        if not post_window_exception:
            return {"ok": False, "error": "outside_window"}
        if reason not in POST_WINDOW_REASONS:
            return {
                "ok": False,
                "error": "reason_not_in_exception_list",
                "allowed": list(POST_WINDOW_REASONS),
            }
    order["refunded"] = True
    order["refund_reason"] = reason
    return {"ok": True, "order_id": order_id, "amount_refunded": order["amount"], "currency": "EUR"}


def get_policy(topic: str, kb_dir: Path = KB_DIR) -> dict[str, Any]:
    """Return the policy text for one topic.

    Rules:
      1. `topic` must be one of POLICY_TOPICS, else `unknown_topic` (with the list, so the model
         can retry with a valid one).
      2. The text comes from the local markdown file; `source: "local"` says so. Module 09
         swaps this function for a knowledge-base search through `policy_fn`.
    """
    if topic not in POLICY_TOPICS:
        return {"ok": False, "error": "unknown_topic", "topics": list(POLICY_TOPICS)}
    return {
        "ok": True,
        "topic": topic,
        "text": (kb_dir / f"{topic}.md").read_text(),
        "source": "local",
    }


# What the model sees. The descriptions are part of the contract: they say what each tool
# enforces, so the model does not try to argue with a `not_found`. Chat-completions shape
# (nested under "function"); `entities.ensure_tools` registers them as code tools.
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Look up an order owned by the current session user. Returns not_found if the order does not belong to the user.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "Order id, e.g. ord_a1"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "issue_refund",
            "description": "Issue a refund. Enforces ownership, no double refund, the EUR 500 limit and the 30-day window unless post_window_exception is true.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "reason": {"type": "string", "description": "Short reason. Outside the window must be one of damaged_in_transit, never_received, defective_on_arrival."},
                    "post_window_exception": {"type": "boolean", "default": False},
                },
                "required": ["order_id", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_policy",
            "description": "Fetch authoritative policy text. Topics: refund_basics, post_window_exceptions, abuse_patterns, shipping_and_scope.",
            "parameters": {
                "type": "object",
                "properties": {"topic": {"type": "string", "enum": list(POLICY_TOPICS)}},
                "required": ["topic"],
            },
        },
    },
]
