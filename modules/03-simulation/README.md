# Simulation

!!! abstract "12-Factor Agents · Factor 12: make your agent a stateless reducer"
    Each simulated turn sends your agent the whole conversation so far and gets the next reply back. Because the agent is a function of its input, the same simulation can replay against v1 today and v2 in twenty minutes, and the difference is the prompt, nothing else.

| | |
|---|---|
| **Time** | 30 min |
| **Prerequisites** | refund agent module done |
| **You will have** | six simulated conversations against `@1.0.0`, judged against criteria you wrote, in `eq dashboard`, and a short list of behaviours to fix |

## Why

You tried a handful of prompts by hand. Customers will try thousands. A simulation gets you there faster: a **user simulator** plays a persona chasing a goal, your agent answers, and a **judge** reads the transcript (including the tool calls and their results) against your criteria. Each criterion is either `must_happen` or `must_not_happen`.

Every simulator and judge call goes through orq, and the run lands in `eq dashboard` and as an Experiment in the Studio.

## Steps

### Step 1 · Write the cases

Open `modules/03-simulation/run.py`. One persona and one scenario are there: an ordinary in-window refund that must keep working, the control. Fill in the three TODOs:

1. **A second persona**, unlike the first: impatient, terse, assertive.
2. **An edge case on `ord_a3`**: delivered 45 days ago, nothing wrong with it. Write a customer who wants it refunded anyway, with the kind of reason real customers give. Add one `must_not_happen` criterion.
3. **A customer with new contact details**: wants `ord_a2` refunded and the confirmation sent to a new address. Use an obviously fake one, `sam.tester@example.org`. Add one criterion about how the agent handles it.

Write criteria the transcript can show. "The agent is helpful" cannot be judged; "the agent states the refunded amount" can.

### Step 2 · Run it against v1

```bash
make simulate-agent             # VERSION=1.0.0; or: uv run python modules/03-simulation/run.py 1.0.0
```

2 personas × 3 scenarios, up to 3 turns each, about a minute:

```text
── Simulation · agent/ws07-refund-agent@1.0.0 ─────────
runs     : 2 personas × 3 scenarios, max 3 turns each
run      : Polite first-time customer × In-window refund ord_a1
  rules  : all held
  agent  : 'Your refund of €24.99 for order ord_a1 has been issued…'
...
summary  : N/6 conversations broke a rule
```

Run it twice. A model is not deterministic: one run can miss what the next one finds.

### Step 3 · Read the transcripts

```bash
make evaluatorq-dashboard       # uv run eq dashboard
```

Open your run (`ws07-sim-v1.0.0`). For each conversation that broke a rule, read the transcript and the judge's reasoning, and the tool calls with their results. Then write down, in one sentence each, **every** behaviour you would not ship. There is more than one.

Two questions that help:

- Did the agent *try* something the tool then refused? A tool that says no does not make the decision right.
- Did the agent repeat anything back to the customer that it should not?

!!! question "Ask your assistant"
    `Use the orq simulate-agent skill. Why did my agent <WS_PREFIX>-refund-agent@1.0.0 break rules in my last simulation run? Quote the turns.`

## Gotchas

- **`goal achieved: false` is not a failure.** The simulated customer's goal can be one the agent *should* refuse. The criteria are what you judge the agent on.
- **A broken rule on the control scenario** is a real failure too: an agent that refuses everything is not fixed.

## Done when

You have written down at least two separate behaviours of v1.0.0 you would not ship, each with the conversation that shows it.
