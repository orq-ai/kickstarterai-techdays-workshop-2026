"""Edge cases for the refund tools: the business rules, with no model and no network.

Run: `make test` (or `uv run pytest -q`). Each test builds a fresh OrderStore, so refunds in one
test never leak into another.
"""

from app.refund_agent.entities import hosted_tool_code
from app.refund_agent.tools import OrderStore, get_policy, issue_refund, lookup_order


def test_lookup_hides_other_users_orders():
    """Another customer's order is `not_found`, and the PII in `notes` never leaves the store."""
    store = OrderStore()
    assert lookup_order(store, "ord_a1")["ok"]
    assert lookup_order(store, "ord_b1") == {"ok": False, "error": "not_found"}
    assert "notes" not in lookup_order(store, "ord_a5")["order"]


def test_in_window_refund_once():
    """An in-window order refunds in full, and only once."""
    store = OrderStore()
    assert issue_refund(store, "ord_a1", "changed mind")["amount_refunded"] == 24.99
    assert issue_refund(store, "ord_a1", "again")["error"] == "already_refunded"


def test_window_and_exception_rules():
    """Outside 30 days a refund needs the exception flag and a reason from the allowed list."""
    store = OrderStore()
    assert issue_refund(store, "ord_a3", "changed mind")["error"] == "outside_window"
    assert (
        issue_refund(store, "ord_a3", "goodwill", post_window_exception=True)["error"]
        == "reason_not_in_exception_list"
    )
    assert issue_refund(store, "ord_a3", "damaged_in_transit", post_window_exception=True)["ok"]


def test_limit():
    """Above EUR 500 goes to a human."""
    store = OrderStore()
    assert issue_refund(store, "ord_a6", "changed mind")["error"] == "above_limit_needs_human_review"


def test_code_tools_match_the_local_functions():
    """The code orq runs (generated from this file) answers like the functions it was copied from."""
    cases = [
        ("lookup_order", {"order_id": "ord_a5"}, lookup_order(OrderStore(), "ord_a5")),
        ("issue_refund", {"order_id": "ord_a3", "reason": "goodwill", "post_window_exception": True},
         issue_refund(OrderStore(), "ord_a3", "goodwill", True)),
        ("get_policy", {"topic": "abuse_patterns"}, {**get_policy("abuse_patterns"), "source": "orq_code_tool"}),
    ]
    for name, params, expected in cases:
        scope = {"params": params}
        exec(hosted_tool_code(name), scope)  # noqa: S102  our own generated code
        assert scope["result"] == expected, name


def test_policy_topics():
    """A known topic resolves; an unknown one is `unknown_topic`."""
    assert get_policy("refund_basics")["ok"]
    assert get_policy("vip")["error"] == "unknown_topic"


def _store_with(order_id, **fields):
    store = OrderStore()
    store.orders[order_id].update(fields)
    return store


def test_window_boundary_is_inclusive():
    """Day 30 is still inside the window; day 31 is not."""
    assert lookup_order(_store_with("ord_a1", delivered_days_ago=30), "ord_a1")["order"]["within_standard_window"]
    assert issue_refund(_store_with("ord_a1", delivered_days_ago=30), "ord_a1", "changed mind")["ok"]
    assert issue_refund(_store_with("ord_a1", delivered_days_ago=31), "ord_a1", "changed mind")["error"] == "outside_window"


def test_limit_boundary_is_inclusive():
    """EUR 500.00 refunds automatically; one cent more goes to a human."""
    assert issue_refund(_store_with("ord_a1", amount=500.0), "ord_a1", "changed mind")["ok"]
    assert (
        issue_refund(_store_with("ord_a1", amount=500.01), "ord_a1", "changed mind")["error"]
        == "above_limit_needs_human_review"
    )
