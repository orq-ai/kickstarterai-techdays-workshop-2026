# Simulation concepts

Simulation gives an agent many realistic conversations before real customers discover its weak spots.

## Why simulate

Hand-written transcripts are useful examples, but they go stale and cover only the cases someone thought to type. A simulator can vary personas and goals across many conversations, then preserve the evidence for review.

## Three models, one transcript

A user simulator plays a persona with a goal. The agent under test responds. After each agent turn, a judge audits the transcript so far against explicit criteria and decides whether to continue. Evaluatorq coordinates this loop on your laptop, preserving the agent's answer and tool evidence in the transcript. `max_turns` caps the conversation if the judge has not already ended it. Each completed case returns one result.

The Python starter uses the model in `JUDGE_MODEL` for both the simulator and the judge, in separate calls. The refund agent uses the model configured when you seeded it from `MODEL`. Every model call goes through the orq.ai AI Gateway, where it is traced and costed. Evaluatorq saves the conversations for the local `eq dashboard` and uploads the results to an Experiment in the Studio. You do not need to create a simulator or judge agent in the Studio. The `<WS_PREFIX>-refund-policy-judge` evaluator is a different thing: you create it in Improve and Evaluate with `make seed-eval`, for the regression eval.

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

The dashed arrow in the diagram is the loop: after each agent reply, the judge either requests the next customer message or stops the conversation.

`target=f"agent:{settings.agent_key}@1.0.0"` uses evaluatorq's native managed-agent support. It reads `ORQ_API_KEY` and `ORQ_BASE_URL` from the environment and calls the same Responses API model, `agent/<key>@1.0.0`, as the chat UI. Importing the workshop settings loads `.env` first. Orq runs the agent and its tools; no custom target class is needed here.

The starter still configures `SIM_LLM` separately: that is the model/client used by the simulator and judge, rather than the managed agent under test. Use the explicit version for a reproducible baseline; `target=f"agent:{settings.agent_key}"` selects the latest agent version.

## Designing a case

| Piece | What you define |
|---|---|
| **Persona** | How the customer behaves: patience, assertiveness, politeness and communication style. Numeric traits range from 0 to 1. |
| **Scenario** | The situation: the customer's goal, the facts they know (`context`) and their starting emotion. |
| **Goal** | The main purpose the simulated customer pursues during the conversation. |
| **Criteria** | The guardrails you judge the agent's behaviour against while it responds to that goal. |

The goal and the criteria answer different questions. **Goal achieved** (`goal_achieved`): did the customer get what they were trying to get? **Criteria met** (`criteria_met`): did the agent behave within the requirements you set along the way? A customer can reach their goal while the agent breaks a criterion, or fail to reach it while the agent correctly follows every criterion.

A `Persona` controls the simulated customer's behavior across a conversation. A `Scenario` gives that customer a goal, context, and criteria. `simulate()` takes their cross product, so adding one persona changes coverage across *every* scenario. This is why a small, deliberately varied matrix teaches more than a long list of near-duplicate prompts. Two personas and three scenarios produce six independently judged conversations. Each scenario carries its criteria; criteria are not another dimension of the case matrix.

Criteria describe observable evidence. “The agent is helpful” is too vague; “the agent states the refunded amount” can be checked. They are assertions for the judge, rather than instructions to the simulated customer.

Source: [`SCENARIOS`](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/main/modules/03-simulation/run.py#L62-L79) in `run.py`.

```python {.code-frame}
from evaluatorq.simulation.contracts import Criterion, Persona, Scenario

Persona(
    name="Example customer",
    patience=0.2,
    assertiveness=0.9,
    background="Prefers brief answers and asks direct questions",
)

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

For example, in a fictional appointment conversation, the goal could be “find an available time.” A required event could be “the agent states the date and time,” and a prohibited event “the agent invents an available slot.” The judge audits after each agent reply.

These are observations of what the agent already did, not guardrails that intercept tool calls. A violation can stop the simulation, but it cannot undo an action.

## Why the conversation stopped

| `terminated_by` | What to inspect |
|---|---|
| `judge` | Read `reason`: the judge may have ended the conversation after success, a violation, or an unusable judge reply. This label alone is not a pass. |
| `max_turns` | The turn budget ran out. Inspect whether the agent was progressing or stuck; an unfinished goal can reflect the budget. Audited criteria still apply. |
| `error` or `timeout` | Execution did not finish normally. Treat missing verdicts as unknown and investigate `reason` before drawing a quality conclusion. |

The runner prints `rules: all held` only when execution finished without an error or timeout and every criterion was audited and satisfied. This does not mean the customer achieved their goal. A **coverage: INCOMPLETE** warning means fewer or more conversations returned than the requested case set.

An empty `rules_broken` list does not establish that every rule held. Check `criteria_verified` and each entry's `audited` value in `metadata["criteria_meta"]`. Per-criterion `evidence` records what the judge checked. Missing or false audit flags mean the evidence is incomplete. A failed evaluator is also an incomplete result. The starter labels these cases **UNKNOWN**, preserving any violations that were already confirmed.

The starter uses `raise_on_execution_failure=False` to preserve exploratory results when execution fails. That does not make simulation a release gate; the later regression eval supplies that gate.

## What the judge can see

Text alone can make a confident but incorrect answer look persuasive. Evaluatorq's native target keeps the managed agent's code-tool calls and their results on the transcript passed to the judge. It matches separate call and result records by `call_id`, preserving the original arguments. The judge therefore sees the requested action and its outcome, not just the final wording.

This only works when the agent returns those intermediate outputs and they are passed to the judge. If the agent returns only its final answer, the judge can evaluate only that answer; it cannot inspect tool calls or results that were not returned.

![Diagram: A text-only judge sees a customer and agent transcript, while this workshop's judge also sees each tool call and result as evidence.](assets/judge-visibility.png)

## The control case

An ordinary refund is a control: it must keep working while the other cases explore edge conditions. Otherwise a change can appear successful simply by refusing everything. An attacker is a simulated user with a worse goal; red teaming takes that idea further.

A correct refusal can have `goal_achieved=False` and still satisfy every criterion. The control checks the complementary requirement: the agent must also help when it should.

## Official docs

- [Evaluatorq simulation: per-turn criteria and saved-case replay](https://orq-ai.github.io/evaluatorq/guides/agent-simulation/)
- [Simulation output reference: termination, audits, and saved runs](https://orq-ai.github.io/evaluatorq/guides/agent-simulation-output/)
- [Agent Simulation](https://docs.orq.ai/ai-studio/optimize/agent-simulations)
- [Test an Agent with Agent Simulation](https://docs.orq.ai/ai-studio/cookbooks/evaluation-safety/agent-simulations)
- [Evaluatorq](https://docs.orq.ai/ai-studio/cookbooks/evaluation-safety/evaluator-q)
