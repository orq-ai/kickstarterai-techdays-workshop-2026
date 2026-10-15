"""A minimal managed agent: create it once, invoke it once, print the trace.

Run from the repository root:
    uv run python modules/02-refund-agent/hello_agent.py

The agent uses your WS_PREFIX, so it is isolated from other participants. It has no
hosted tools: this is the smallest managed-agent example before the refund-agent tutorial.
"""

from app.refund_agent.client import make_orq
from app.refund_agent.config import settings

HELLO_KEY = settings.key("hello-agent")


def ensure_hello_agent(orq) -> None:
    """Create the small agent only when this seat does not already have it."""
    try:
        orq.agents.retrieve(agent_key=HELLO_KEY)
        return
    except Exception:  # The SDK raises for a missing key; create the first version below.  # noqa: S110
        pass

    orq.agents.create(
        key=HELLO_KEY,
        role="Friendly customer greeter.",
        description="A minimal managed agent that greets the customer without tools.",
        instructions="Greet the customer in one friendly sentence.",
        path=settings.path,
        model={"id": settings.model, "parameters": {"reasoning_effort": "none"}},
        settings={"max_iterations": 8, "max_execution_time": 120, "tools": []},
    )


def main() -> None:
    settings.require_seat()
    orq = make_orq()
    ensure_hello_agent(orq)
    response = orq.responses.create(model=f"agent/{HELLO_KEY}", input="Hello")

    print("── Hello agent ─────────────────────────────────────")
    print(f"agent    : {HELLO_KEY}")
    print(f"model    : {settings.model}")
    for item in response.model_dump()["output"]:
        if item["type"] == "message":
            print(f"answer   : {''.join(part.get('text', '') for part in item['content'])}")
    print(f"trace    : {response.telemetry.trace_id}")


if __name__ == "__main__":
    main()
