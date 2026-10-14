"""Fix and eval: replay the customer messages your simulation broke on, on two versions side by side.

Each message goes to `@1.0.0` and to the version you published, each in a fresh conversation, so
the two answers start from the same input. Tool calls are printed with their result: a call to
issue_refund that the tool rejected is still a call.

Fill in PROMPTS first.
Run it with `make compare-versions` (or `uv run python modules/04-fix-and-eval/run.py 2.0.0`).
"""

import os
import sys

from app.refund_agent.client import ask_agent, make_orq
from app.refund_agent.config import settings

NEW = (sys.argv[1:] or [os.environ.get("VERSION") or "latest"])[0]
VERSIONS = ["1.0.0", NEW]

# The opening messages of the conversations that broke a rule in `make simulate-agent`.
PROMPTS: list[str] = [
    # TODO: paste the first customer message of each conversation that broke a rule
]

settings.require_seat()
if not PROMPTS:
    raise SystemExit("TODO: add the customer messages from your broken simulation runs to PROMPTS")
orq = make_orq()
for prompt in PROMPTS:
    print(f"── {prompt[:70]} ".ljust(55, "─"))
    for version in VERSIONS:
        turn = ask_agent(prompt, version, orq)
        calls = ", ".join(
            f"{c.name}({c.arguments.get('order_id', c.arguments.get('topic', ''))})"
            + ("" if not isinstance(c.result, dict) else " ok" if c.result.get("ok") else f" {c.result.get('error')}")
            for c in turn.tool_calls
        )
        print(f"@{version:<7}: {turn.answer[:150]!r}")
        print(f"  tools  : {calls or 'none'}")
print("next     : `make regression-eval VERSION=<your version>` runs the whole dataset")
