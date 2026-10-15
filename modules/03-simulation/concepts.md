# Simulation concepts

Simulation gives an agent many realistic conversations before real customers discover its weak spots.

## Why simulate

Hand-written transcripts are useful examples, but they go stale and cover only the cases someone thought to type. A simulator can vary personas and goals across many conversations, then preserve the evidence for review.

## Three models, one transcript

A user simulator plays a persona with a goal. The agent under test responds. After each agent turn, a judge audits the transcript so far against explicit criteria and decides whether to continue. Every model call goes through the router, where it is traced and costed. `max_turns` caps the conversation if the judge has not already ended it.

Source: the [`simulate() call`](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/main/modules/03-simulation/run.py) in `run.py`.

```python {.code-frame}
from app.refund_agent.config import settings
from evaluatorq.simulation import simulate

# modules/03-simulation/run.py
results = await simulate(
    target=f"agent:{settings.agent_key}@1.0.0",
    personas=PERSONAS,
    scenarios=SCENARIOS,
    max_turns=3,
    llm_config=SIM_LLM,               # simulator and judge through the router
    save=True,
)
```

![Diagram: Cases feed a user simulator and the refund agent. The judge audits each turn and decides whether the conversation continues, while all model calls pass through the router.](assets/simulation-loop.png)

`target=f"agent:{settings.agent_key}@1.0.0"` uses evaluatorq's native managed-agent support. It reads `ORQ_API_KEY` and `ORQ_BASE_URL` from the environment and calls the same Responses API model, `agent/<key>@1.0.0`, as the chat UI. Importing the workshop settings loads `.env` first. Orq runs the agent and its tools; no custom target class is needed here.

The starter still configures `SIM_LLM` separately: that is the model/client used by the simulator and judge, rather than the managed agent under test. Use the explicit version for a reproducible baseline; `target=f"agent:{settings.agent_key}"` selects the latest agent version.

## A case is persona × scenario × criteria

A persona describes traits such as patience, assertiveness, politeness, and technical level. A scenario supplies the customer goal. Its `must_happen` and `must_not_happen` criteria say what must be visible in the transcript. Two personas times three scenarios produce six conversations.

Source: [`SCENARIOS`](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/main/modules/03-simulation/run.py#L62-L79) in `run.py`.

```python {.code-frame}
from evaluatorq.simulation.contracts import Criterion, Scenario

# A control case: the criterion names visible evidence, not a vague quality.
Scenario(
    name="In-window refund ord_a1",
    goal="Get order ord_a1 refunded because it is the wrong colour",
    criteria=[
        Criterion(
            description="The agent issues the refund and states EUR 24.99",
            type="must_happen",
        ),
    ],
)
```

![Diagram: Two personas and three scenarios form six conversations; each scenario carries observable must-happen and must-not-happen criteria for the judge.](assets/case-grid.png)

## Criteria accumulate across turns

The judge checks what occurred; evaluatorq derives pass or fail from the criterion's type:

- **`must_happen`** is satisfied once the required behaviour occurs on any turn. If the conversation finishes normally without it occurring, it fails.
- **`must_not_happen`** is violated if the prohibited behaviour occurs on any turn. A later apology or correction does not erase that violation.

These are observations of what the agent already did, not guardrails that intercept tool calls. A violation can stop the simulation, but it cannot undo an action.

## Why the conversation stopped

| `terminated_by` | What to inspect |
|---|---|
| `judge` | Read `reason`: the judge may have ended the conversation after success, a violation, or an unusable judge reply. This label alone is not a pass. |
| `max_turns` | The turn budget ran out. Inspect whether the agent was progressing or stuck; an unfinished goal can reflect the budget. Audited criteria still apply. |
| `error` or `timeout` | Execution did not finish normally. Treat missing verdicts as unknown and investigate `reason` before drawing a quality conclusion. |

An empty `rules_broken` list does not establish that every rule held. Check `criteria_verified` and each entry's `audited` value in `metadata["criteria_meta"]`. Missing or false audit flags mean the evidence is incomplete. A failed evaluator is also an incomplete result. The starter labels these cases **UNKNOWN**, preserving any violations that were already confirmed.

## What the judge can see

Text alone can make a confident but incorrect answer look persuasive. Evaluatorq's native target keeps the managed agent's code-tool calls and their results on the transcript passed to the judge. It matches separate call and result records by `call_id`, preserving the original arguments. The judge therefore sees the requested action and its outcome, not just the final wording.

This only works when the agent returns those intermediate outputs and they are passed to the judge. If the agent returns only its final answer, the judge can evaluate only that answer; it cannot inspect tool calls or results that were not returned.

![Diagram: A text-only judge sees a customer and agent transcript, while this workshop's judge also sees each tool call and result as evidence.](assets/judge-visibility.png)

## The control case

An ordinary refund is a control: it must keep working while the other cases explore edge conditions. Otherwise a change can appear successful simply by refusing everything. An attacker is a simulated user with a worse goal; red teaming takes that idea further.

Take away a second distinction: `goal_achieved` describes whether the simulated customer got what they wanted; `criteria_met` describes whether the agent met the rules. A correct refusal can therefore have `goal_achieved=False` and still pass every criterion. For a safety or policy agent, criteria, not customer success, are the release signal.

## Official docs

- [Evaluatorq simulation: per-turn criteria and saved-case replay](https://orq-ai.github.io/evaluatorq/guides/agent-simulation/)
- [Simulation output reference: termination, audits, and saved runs](https://orq-ai.github.io/evaluatorq/guides/agent-simulation-output/)
- [Agent Simulation](https://docs.orq.ai/ai-studio/optimize/agent-simulations)
- [Test an Agent with Agent Simulation](https://docs.orq.ai/ai-studio/cookbooks/evaluation-safety/agent-simulations)
- [Evaluatorq](https://docs.orq.ai/ai-studio/cookbooks/evaluation-safety/evaluator-q)
