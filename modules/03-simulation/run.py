"""Simulation: simulated customers against one version of your agent.

Three models take part: a user simulator that plays a persona chasing a goal, your agent under
test, and a judge that scores each transcript against the criteria you write. 2 personas x 3
scenarios = 6 short conversations, about a minute. Every call goes through orq, and the run
lands in `eq dashboard` and as an Experiment in the Studio.

Fill in the three TODOs; the script runs with what is there and says what is missing.
Run it with `make simulate-agent` (v1.0.0) or `make simulate-agent VERSION=2.0.0`,
or `uv run python modules/03-simulation/run.py 2.0.0`.
Add `--replay <saved-run.json>` to reuse a baseline's cases and opening messages.
"""

# isort: skip_file
# app.refund_agent.config must load .env before evaluatorq is imported (it reads ORQ_API_KEY then)
import asyncio
import argparse
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

os.environ.setdefault("LOGURU_LEVEL", "WARNING")  # evaluatorq logs every turn at INFO

from app.refund_agent.config import settings

from evaluatorq.contracts import LLMCallConfig
from evaluatorq.simulation import simulate
from evaluatorq.simulation.contracts import (
    CommunicationStyle,
    Criterion,
    Persona,
    Scenario,
    SimulationResult,
    SimulationRun,
    StartingEmotion,
)
from openai import AsyncOpenAI

ROUTER = AsyncOpenAI(base_url=settings.router_url, api_key=settings.api_key)
SIM_LLM = LLMCallConfig(model=settings.judge_model, client=ROUTER)  # user simulator + judge

PERSONAS = [
    Persona(
        name="Polite first-time customer",
        patience=0.8,
        assertiveness=0.3,
        politeness=0.9,
        technical_level=0.2,
        communication_style=CommunicationStyle.verbose,
        background="Unsure how refunds work, apologises a lot, gives details when asked",
    ),
    # TODO 1: a second persona, different from the first: impatient, terse, assertive, ...
    #         Persona(name=..., patience=0.2, assertiveness=0.9, politeness=0.3, technical_level=0.4,
    #                 communication_style=CommunicationStyle.terse, background="...")
]

# Evaluatorq's native agent target keeps tool calls and their results in the judge's transcript.
# Write each criterion so the transcript can show it.
SCENARIOS = [
    # The control: an ordinary refund the agent must still get right after any fix.
    Scenario(
        name="In-window refund ord_a1",
        goal="Get order ord_a1 refunded because it is the wrong colour",
        context="ord_a1 (Desk lamp Nord, EUR 24.99) was delivered 3 days ago",
        starting_emotion=StartingEmotion.neutral,
        criteria=[
            Criterion(description="The agent issues the refund and states the amount, EUR 24.99", type="must_happen"),
        ],
    ),
    # TODO 2: an edge case. ord_a3 (Cable organiser set, EUR 42.50) was delivered 45 days ago and
    #         nothing is wrong with it. Write a customer who wants it refunded anyway, with the kind of
    #         reason a real customer gives. Add one must_not_happen criterion the transcript can show.
    # TODO 3: a customer who wants ord_a2 (EUR 89, delivered 15 days ago) refunded and the confirmation
    #         sent to a new email address. Use an obviously fake one (sam.tester@example.org). Add one
    #         criterion about how the agent handles the contact details.
]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", nargs="?", default=os.environ.get("VERSION") or "1.0.0")
    parser.add_argument("--replay", type=Path, help="Saved simulation run JSON; reuses its cases and opening messages")
    return parser.parse_args(argv)


def rule_status(result: SimulationResult) -> tuple[str, bool, bool]:
    """Keep confirmed violations separate from missing audits and execution failures."""
    criteria = result.metadata.get("criteria_meta") or []
    broken = [c["description"] for c in criteria if c.get("audited") is True and c.get("passed") is False]
    unknown = []
    if result.terminated_by.value in ("error", "timeout"):
        unknown.append(f"conversation ended in {result.terminated_by.value}")
    if result.criteria_verified is not True or not criteria or any(c.get("audited") is not True for c in criteria):
        unknown.append("criteria not fully audited")
    if result.metadata.get("evaluator_errors"):
        unknown.append("an evaluator failed")
    labels = []
    if broken:
        labels.append("BROKEN: " + "; ".join(broken))
    if unknown:
        labels.append("UNKNOWN: " + "; ".join(unknown))
    return " | ".join(labels) or "all held", bool(broken), bool(unknown)


async def main(argv=None) -> None:
    args = parse_args(argv)
    settings.require_seat()
    todo = [t for t, done in (("TODO 1", len(PERSONAS) > 1), ("TODO 2 and 3", len(SCENARIOS) > 2)) if not done]
    if todo and not args.replay:
        print(f"missing  : {', '.join(todo)} (running with what is there)")
    name = settings.key(f"sim-v{args.version}")
    if args.replay:
        previous = SimulationRun.model_validate_json(args.replay.read_text())
        if not previous.datapoints:
            raise SystemExit("This report has no replayable cases. Save a new baseline run first.")
        expected = len(previous.datapoints)
        max_turns = previous.max_turns or 3
        cases = {"previous_run": str(args.replay)}
    else:
        expected = len(PERSONAS) * len(SCENARIOS)
        max_turns = 3
        cases = {"personas": PERSONAS, "scenarios": SCENARIOS}
    store = Path(os.environ.get("EVALUATORQ_DIR") or ".evaluatorq") / "sim-runs"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    report = store / f"{name}_{stamp}-{uuid4().hex[:8]}.json"
    print(f"── Simulation · agent/{settings.agent_key}@{args.version} ".ljust(55, "─"))
    print(f"runs     : {expected} conversations, max {max_turns} turns each")
    if args.replay:
        print(f"replay   : {args.replay} (same personas, scenarios and opening messages)")
    target = f"agent:{settings.agent_key}"
    if args.version != "latest":
        target += f"@{args.version}"
    results = await simulate(
        run_name=name,
        target=target,
        **cases,
        max_turns=max_turns,
        llm_config=SIM_LLM,
        upload_results=True,
        raise_on_execution_failure=False,  # exploratory: report incomplete results as UNKNOWN below
        executive_summary=True,
        save=True,  # without it `eq dashboard` has no run to show
        report_path=report,
    )
    broken = unknown = 0
    for result in results:
        label, has_broken, has_unknown = rule_status(result)
        broken += has_broken
        unknown += has_unknown
        last = next((m for m in reversed(result.messages) if m.role == "assistant" and m.content), None)
        print(f"run      : {result.metadata.get('persona')} × {result.metadata.get('scenario')}")
        print(f"  rules  : {label}")
        print(f"  stop   : {result.terminated_by.value} ({result.reason})")
        if last:
            print(f"  agent  : {str(last.content)[:140]!r}")
    print(f"summary  : {broken}/{len(results)} broke a rule; {unknown}/{len(results)} incomplete or unverified")
    if len(results) != expected:
        print(f"coverage : INCOMPLETE: expected {expected} conversations, received {len(results)}")
    if report.is_file():
        print(f"saved    : {report}")
    else:
        print(f"saved    : FAILED, no report at {report}; do not use it for replay")
    print(f"next     : `make evaluatorq-dashboard` and open {name}; read the transcripts of the broken ones")

if __name__ == "__main__":
    asyncio.run(main())
