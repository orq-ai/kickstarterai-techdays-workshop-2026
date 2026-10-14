"""Simulation: simulated customers against one version of your agent.

Three models take part: a user simulator that plays a persona chasing a goal, your agent under
test, and a judge that scores each transcript against the criteria you write. 2 personas x 3
scenarios = 6 short conversations, about a minute. Every call goes through orq, and the run
lands in `eq dashboard` and as an Experiment in the Studio.

Fill in the three TODOs; the script runs with what is there and says what is missing.
Run it with `make simulate-agent` (v1.0.0) or `make simulate-agent VERSION=2.0.0`,
or `uv run python modules/03-simulation/run.py 2.0.0`.
"""

# isort: skip_file
# app.refund_agent.config must load .env before evaluatorq is imported (it reads ORQ_API_KEY then)
import asyncio
import os
import sys

os.environ.setdefault("LOGURU_LEVEL", "WARNING")  # evaluatorq logs every turn at INFO

from app.refund_agent.config import settings

from evaluatorq.contracts import LLMCallConfig
from evaluatorq.simulation import simulate
from evaluatorq.simulation.contracts import (
    CommunicationStyle,
    Criterion,
    Persona,
    Scenario,
    StartingEmotion,
)
from openai import AsyncOpenAI

from evals.target import agent_target

VERSION = (sys.argv[1:] or [os.environ.get("VERSION") or "1.0.0"])[0]
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

# The judge reads the transcript, including the tool calls and their results (evals/target.py
# keeps them). Write each criterion so the transcript can show it.
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


async def main() -> None:
    settings.require_seat()
    todo = [t for t, done in (("TODO 1", len(PERSONAS) > 1), ("TODO 2 and 3", len(SCENARIOS) > 2)) if not done]
    if todo:
        print(f"missing  : {', '.join(todo)} (running with what is there)")
    name = settings.key(f"sim-v{VERSION}")
    print(f"── Simulation · agent/{settings.agent_key}@{VERSION} ".ljust(55, "─"))
    print(f"runs     : {len(PERSONAS)} personas × {len(SCENARIOS)} scenarios, max 3 turns each")
    results = await simulate(
        evaluation_name=name,
        target=agent_target(VERSION),
        personas=PERSONAS,
        scenarios=SCENARIOS,
        max_turns=3,
        llm_config=SIM_LLM,
        evaluator_names=["goal_achieved", "criteria_met"],
        upload_results=True,
        exit_on_failure=False,
        executive_summary=False,
        save=True,  # without it `eq dashboard` has no run to show
    )
    broken = 0
    for result in results:
        rules = [
            SCENARIOS_BY_NAME[result.metadata.get("scenario")].criteria[int(r.split("_")[-1])].description[:70]
            if r.startswith("criteria_") else r
            for r in result.rules_broken or []
        ]
        broken += bool(rules)
        last = next((m for m in reversed(result.messages) if m.role == "assistant" and m.content), None)
        print(f"run      : {result.metadata.get('persona')} × {result.metadata.get('scenario')}")
        print(f"  rules  : {'BROKEN: ' + '; '.join(rules) if rules else 'all held'}")
        if last:
            print(f"  agent  : {str(last.content)[:140]!r}")
    print(f"summary  : {broken}/{len(results)} conversations broke a rule")
    print(f"next     : `make evaluatorq-dashboard` and open {name}; read the transcripts of the broken ones")


SCENARIOS_BY_NAME = {scenario.name: scenario for scenario in SCENARIOS}

if __name__ == "__main__":
    asyncio.run(main())
