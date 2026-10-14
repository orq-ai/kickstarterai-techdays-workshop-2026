"""Improve and evaluate: replay the customer messages your simulation broke on, on two versions side by side.

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
    # TODO: paste the first customer message of each conversation that broke a rule.
    #   - Where to find them: `make evaluatorq-dashboard` and open your baseline run (the
    #     transcripts show each conversation turn by turn), or the saved baseline JSON under
    #     `.evaluatorq/sim-runs/` (`uv run eq sim runs` lists the runs).
    #   - Take only the customer's opening message, the very first one. Not the agent's reply,
    #     not later turns: the replay starts a fresh conversation from that message.
    #   - Add one string per broken conversation, separated by commas. Copy the text exactly:
    #     a reworded message can change what the agent does, which defeats the comparison.
    #   - Two to four messages are plenty. Prefer ones that broke different rules over several
    #     that failed the same way.
    #   - Use double quotes around each string; messages often contain apostrophes.
    #   - Then run `make compare-versions VERSION=<your version>` and read the `tools` line under
    #     each version: the same message should now lead to different calls or results.
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
