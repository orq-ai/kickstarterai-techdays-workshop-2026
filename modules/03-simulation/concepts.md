# Simulation concepts

Simulation gives an agent many realistic conversations before real customers discover its weak spots.

## Why simulate

Hand-written transcripts are useful examples, but they go stale and cover only the cases someone thought to type. A simulator can vary personas and goals across many conversations, then preserve the evidence for review.

## Three models, one transcript

A user simulator plays a persona with a goal. The agent under test responds. A judge evaluates the completed conversation against explicit criteria. Every model call goes through the router, where it is traced and costed, and the conversation can continue up to `max_turns`.

```python {.code-frame}
from evaluatorq.simulation import simulate
from evals.target import agent_target

# modules/03-simulation/run.py
results = await simulate(
    target=agent_target(VERSION),
    personas=PERSONAS,
    scenarios=SCENARIOS,
    max_turns=3,
    llm_config=SIM_LLM,               # simulator and judge through the router
    evaluator_names=["goal_achieved", "criteria_met"],
    save=True,
)
```

![Cases feed a user simulator that exchanges a transcript with the refund agent; a judge evaluates the completed transcript and its criteria, while all model calls pass through the router.](assets/simulation-loop.png)

The simulation target is an adapter, not a second implementation of the agent. `agent_target()` points evaluatorq at the same managed `agent/<key>@<version>` that the chat UI calls. It uses an OpenAI-compatible router client, so evaluatorq can drive a managed agent while orq.ai executes its tools.

```python {.code-frame}
from evaluatorq.contracts import LLMCallConfig
from openai import AsyncOpenAI
from app.refund_agent.config import settings

# evals/target.py
model = f"agent/{settings.agent_key}@{version}"
router = AsyncOpenAI(base_url=settings.router_url, api_key=settings.api_key)
return ManagedAgentTarget(
    LLMCallConfig(model=model, client=router),
    client=router,
    require_orq=True,
)
```

This adapter pattern is reusable: keep the agent implementation in one place, then adapt its input and output to the evaluator framework.

## A case is persona × scenario × criteria

A persona describes traits such as patience, assertiveness, politeness, and technical level. A scenario supplies the customer goal. Its `must_happen` and `must_not_happen` criteria say what must be visible in the transcript. Two personas times three scenarios produce six conversations.

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

![Two personas and three scenarios form six conversations; each scenario carries observable must-happen and must-not-happen criteria for the judge.](assets/case-grid.png)

## What the judge can see

Text alone can make a confident but incorrect answer look persuasive. This workshop's `evals/target.py` keeps the managed agent's code-tool calls and their results on the transcript passed to the judge. The judge can therefore use execution evidence, not just the final wording.

```python {.code-frame}
import json

# evals/target.py, inside ManagedAgentTarget._normalise_response()
for item in response.output or []:
    raw = item if isinstance(item, dict) else item.model_dump()
    if str(raw.get("type", "")).startswith("orq:"):
        results[raw.get("call_id")] = raw.get("result", raw.get("status"))

# The matched function call keeps the managed tool result.
item = item.model_copy(update={"result": json.dumps(results[item.call_id])})
```

![A text-only judge sees a customer and agent transcript, while this workshop's judge also sees each tool call and result as evidence.](assets/judge-visibility.png)

## The control case

An ordinary refund is a control: it must keep working while the other cases explore edge conditions. Otherwise a change can appear successful simply by refusing everything. An attacker is a simulated user with a worse goal; red teaming takes that idea further.

Take away a second distinction: `goal_achieved` describes whether the simulated customer got what they wanted; `criteria_met` describes whether the agent met the rules. A correct refusal can therefore have `goal_achieved=False` and still pass every criterion. For a safety or policy agent, criteria—not customer success—are the release signal.

## Official docs

- [Agent Simulation](https://docs.orq.ai/ai-studio/optimize/agent-simulations)
- [Test an Agent with Agent Simulation](https://docs.orq.ai/ai-studio/cookbooks/evaluation-safety/agent-simulations)
- [Evaluatorq](https://docs.orq.ai/ai-studio/cookbooks/evaluation-safety/evaluator-q)
