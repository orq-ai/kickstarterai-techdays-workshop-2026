"""A minimal managed agent: create it once, invoke it once, print the trace.

Run from the repository root:
    uv run python modules/02-refund-agent/hello_agent.py

The agent uses your WS_PREFIX, so it is isolated from other participants. It has no
hosted tools: this is the smallest managed-agent example before the refund-agent tutorial.
"""

from app.refund_agent.client import make_orq, parse_turn
from app.refund_agent.config import settings

HELLO_KEY = settings.key("hello-agent")


def ensure_hello_agent(orq) -> None:
    """Create the small agent only when this seat does not already have it."""
    try:
        orq.agents.retrieve(agent_key=HELLO_KEY)
        return
    except Exception:  # The SDK raises for a missing key; create the first version below.
        pass

    orq.agents.create(
        key=HELLO_KEY,
        display_name="Hello agent",
        role="Greeting assistant.",
        description="Greets a customer in one friendly sentence.",
        instructions="Greet the customer in one friendly sentence.",
        path=settings.path,
        model={"id": settings.model, "parameters": {"reasoning_effort": "none"}},
        settings={"max_iterations": 1, "max_execution_time": 30},
    )


def main() -> None:
    settings.require_seat()
    orq = make_orq()
    ensure_hello_agent(orq)
    response = orq.responses.create(model=f"agent/{HELLO_KEY}", input="Hello")
    turn = parse_turn(response)

    print("── Hello agent ─────────────────────────────────────")
    print(f"agent    : {HELLO_KEY}")
    print(f"model    : {settings.model}")
    print(f"answer   : {turn.answer}")
    print(f"trace    : {turn.trace_id}")


if __name__ == "__main__":
    main()
