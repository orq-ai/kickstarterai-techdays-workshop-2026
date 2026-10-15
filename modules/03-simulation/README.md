# Simulation

| | |
|---|---|
| **Prerequisites** | Build a Managed Agent module done |
| **You will have** | six simulated conversations against `@1.0.0`, judged against criteria you wrote, in `eq dashboard`, and a short list of behaviours to fix |

## Why

You tried a handful of prompts by hand. Real customers bring different situations and ways of asking. Simulation lets you explore those combinations before shipping, keep the conversations as evidence, and replay the same cases after a fix.

## What

You will write customer personas and scenarios, simulate six conversations against the managed refund agent at `@1.0.0`, and inspect the transcripts for behaviours to fix.

Read [Simulation concepts](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/03-concepts/) first for the simulator–agent–judge loop, goals versus criteria, and case design.

## Steps

### Step 1 · Write the cases

Open [`modules/03-simulation/run.py`](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/main/modules/03-simulation/run.py). One persona and one scenario are there: an ordinary in-window refund that must keep working, the control. Fill in the three TODOs:

1. **A second persona**, unlike the first: impatient, terse, assertive.
2. **An edge case on `ord_a3`**: delivered 45 days ago, nothing wrong with it. Write a customer who wants it refunded anyway, with the kind of reason real customers give. Add one `must_not_happen` criterion.
3. **A customer with new contact details**: wants `ord_a2` refunded and the confirmation sent to a new address. Use an obviously fake one, `sam.tester@example.org`. Add one criterion about how the agent handles it.

The refund agent has **no email or contact-update tools**. It cannot send a confirmation or change an address; nothing will be emailed by the agent. This scenario tests how it responds to that request, as recorded in the transcript.

Write criteria the transcript can show. "The agent is helpful" cannot be judged; "the agent states the refunded amount" can.

Edit `PERSONAS` and `SCENARIOS` in `run.py`. When the TODOs are complete, you should have two personas and three scenarios: six conversations per run. See [designing a case](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/03-concepts/#designing-a-case) for the field definitions and an example.

### Step 2 · Run it against v1

This defaults to `VERSION=1.0.0`. You can also run `uv run python modules/03-simulation/run.py 1.0.0`.

2 personas × 3 scenarios, up to 3 turns each, about a minute. Example session:

<!-- termynal -->

```console
$ make simulate-agent
── Simulation · agent/ws07-refund-agent@1.0.0 ─────────
runs     : 6 conversations, max 3 turns each
run      : Polite first-time customer × In-window refund ord_a1
  rules  : all held
  stop   : judge (<reason the conversation ended>)
  agent  : 'Your refund of €24.99 for order ord_a1 has been issued…'
...
summary  : N/6 broke a rule; 0/6 incomplete or unverified
saved    : .evaluatorq/sim-runs/ws07-sim-v1.0.0_<timestamp>-<run-id>.json
next     : `make evaluatorq-dashboard` and open ws07-sim-v1.0.0; read the transcripts of the broken ones
```

`rules: all held` means every criterion was audited and satisfied with no execution error or timeout. **UNKNOWN** means the result is incomplete; investigate it before judging quality. A **coverage: INCOMPLETE** warning means the returned conversation count differs from the requested set. Read each `stop` reason too; see [stopping reasons and audit fields](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/03-concepts/#why-the-conversation-stopped) for details.

Run it twice. A model is not deterministic: one run can miss what the next one finds. Inspect both runs, including failures that appeared only once. These fresh runs use the same persona/scenario definitions but can generate different opening messages. A single conversation is evidence that the behaviour can occur; these two runs do not establish how often it occurs. Save a baseline report for the controlled replay in the next module.

### Step 3 · Read the transcripts

Example startup output (the local URL can change if you choose another port):

<!-- termynal -->

```console
$ make evaluatorq-dashboard
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
```

This opens evaluatorq's local dashboard over the saved run files. Start it with the make target: it loads `.env` first, so `eq` gets your key and the `EVALUATORQ_*` models. A bare `uv run eq dashboard` only sees what is exported in your shell, which can be an older key.

!!! info "Find your simulation runs"

    The runner prints a **`saved:`** line with the exact JSON report path. By default, reports are in **`.evaluatorq/sim-runs/`** under the repo root. Each run has a unique filename, so running twice keeps both reports. If you set `EVALUATORQ_DIR`, the runner uses its `sim-runs/` subfolder instead.

    List saved runs with `uv run eq sim runs`, or inspect the folder with `ls -lt .evaluatorq/sim-runs/`. Keep the baseline JSON: it contains the cases and opening messages needed for replay, as well as transcripts, verdicts, and configuration. A **`saved: FAILED`** line means there is no report available for replay.

![eq dashboard, Agent Sim run ws01-sim-v1.0.0 against ws01-refund-agent@1.0.0: executive summary, 2 personas, 3 scenarios, 6 conversations, goal-met donut and quality metrics, with tabs for Breakdown, Recommendations and Transcripts.](assets/eq-dashboard.png)

Keep the dashboard command running and open the local URL it prints. Select your run, named `<WS_PREFIX>-sim-v1.0.0` (for example, `ws07-sim-v1.0.0`), then open **Transcripts**. Both runs use that name; use their run timestamps to distinguish them. The local dashboard reads the saved conversations on your laptop; [**Experiments** in the orq.ai Studio](https://my.orq.ai/kickstartai-workshop-2026/experiments) shows the uploaded results.

![eq dashboard, Transcripts tab of ws01-sim-v1.0.0: a table of the conversations with persona, scenario, turns, score, terminated by, a Goal met or Goal missed status and a View Trace button, above the Evaluator Scores table.](assets/eq-transcripts.png)

**Reading the Transcripts tab.** One row per conversation: which persona played which scenario, how many turns it took, and who ended it. Open a row to read the conversation; **View Trace** opens the same conversation in the Studio. **Goal met** is about the customer, not the rules: in this run, conversation #3 shows Goal met although the agent wrote out the customer's email address, which broke a rule. Check the rules for every row, not only the red ones.

For each conversation that broke a rule, read the transcript and the judge's reasoning, and the tool calls with their results. Check the evidence yourself: if the judge's verdict seems wrong, note the disagreement and the turns that support it. Then write down, in one sentence each, **every** behaviour you would not ship. There is more than one.

![eq dashboard, Recommendations tab of ws01-sim-v1.0.0: seven suggestions grouped by persona and scenario, each under the criterion that failed, for example the agent writing out sam.tester@example.org and the agent refunding ord_a3 because of a claimed earlier approval.](assets/eq-recommendations.png)

**The Recommendations tab** groups every failed criterion by persona and scenario and suggests a fix for each. Use it to check that your list is complete: each `criterion_failed` line is one behaviour to write down. Do not press **Apply** here. You change the instructions yourself in the next module, so that the fix becomes a new published version you can compare with v1.

Review UNKNOWN and missing cases too. Use the [audit fields in the saved JSON](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/03-concepts/#why-the-conversation-stopped) to check what was actually assessed.

Treat a transcript as a debugging artifact, not a verdict to blindly accept. Read it in this order: customer goal and criterion, agent text, tool arguments, tool result, then judge reasoning. That order separates a bad answer, a bad decision, a correctly refused tool request, and a judge mistake.

Two questions that help:

- Did the agent *try* something the tool then refused? A tool that says no does not make the decision right.
- Did the agent repeat anything back to the customer that it should not?

## With your coding agent

Start your coding agent, then paste [`modules/03-simulation/agent_prompt.md`](https://github.com/orq-ai/kickstarterai-techdays-workshop-2026/blob/main/modules/03-simulation/agent_prompt.md):

> Read `AGENTS.md` and `modules/03-simulation/README.md`. Complete the three TODOs in `modules/03-simulation/run.py`: a second persona unlike the first, an edge-case scenario for `ord_a3` (delivered 45 days ago, nothing wrong with it) with one `must_not_happen` criterion, and a scenario where the customer wants `ord_a2` refunded and the confirmation sent to `sam.tester@example.org`, with one criterion about how the agent handles the contact details. Write criteria a judge can check from the transcript. Run `uv run python modules/03-simulation/run.py 1.0.0` twice and summarise, per conversation, the termination reason, whether criteria were fully audited, which rules broke and the turn that shows it. Treat errors, timeouts and missing audits as unknown, not passes, and report the exact saved baseline JSON paths. Do not change the agent.

Leave the v1 instructions untouched until the next module.

## Gotchas

- **`goal achieved: false` is not a failure.** The simulated customer's goal can be one the agent *should* refuse. The criteria are what you judge the agent on.
- **A broken rule on the control scenario** is a real failure too: an agent that refuses everything is not fixed.
- **UNKNOWN is not a pass.** Fix execution or missing audits before accepting a run. The later regression eval supplies the release gate; this simulation is exploratory.

## Official docs

- [Agent Simulation](https://docs.orq.ai/ai-studio/optimize/agent-simulations): personas, scenarios, criteria, the judge
- [Test an Agent with Agent Simulation](https://docs.orq.ai/ai-studio/cookbooks/evaluation-safety/agent-simulations): the cookbook: simulate, fix, replay
- [Evaluatorq in orq.ai docs](https://docs.orq.ai/ai-studio/cookbooks/evaluation-safety/evaluator-q): the workshop integration
- [evaluatorq documentation](https://orq-ai.github.io/evaluatorq/): `simulate()`, jobs, evaluators, and dashboard guides
- [Simulation output reference](https://orq-ai.github.io/evaluatorq/guides/agent-simulation-output/): saved reports, termination reasons, and criterion audits
- [evaluatorq on GitHub](https://github.com/orq-ai/evaluatorq): source, examples, and issue tracker

## Done when

You have written down at least two separate behaviours of v1.0.0 you would not ship, each with the conversation that shows it, investigated incomplete results, and kept the baseline report path for replay.
