"""make smoke-test: one turn to your managed agent. The last setup check.

What: one in-window refund request to `agent/<seat>-refund-agent`. orq runs the model and the
code tools; this script only sends the message and prints what came back.
Why: if this passes, the key, the seat prefix, the seeded agent and its tools all work. The trace
id is the proof the call went through orq.
How: `make smoke-test` (or `uv run python -m app.smoke`). Exits non-zero when a check fails.
"""

from app.refund_agent.client import ask_agent
from app.refund_agent.config import settings

QUESTION = "Hi, I want a refund for order ord_a1, I changed my mind."


def main() -> None:
    settings.require_seat()
    turn = ask_agent(QUESTION)

    print("── Smoke test · one turn to your agent ────────────────")
    print(f"agent    : {settings.agent_key}")
    print(f"question : {QUESTION}")
    print(f"answer   : {turn.answer[:120]}")
    print(f"tools    : {' → '.join(turn.tool_names) or 'none'}")
    print(f"trace    : {turn.trace_id}")

    assert turn.trace_id, "no trace id: the call did not go through orq"
    assert "lookup_order" in turn.tool_names, "the agent did not call lookup_order: run `make seed-workspace`"

    print("verdict  : OK, orq ran your agent and its tools")
    print("next     : open Traces in the Studio and search the trace id")


if __name__ == "__main__":
    main()
