# Onboarding

!!! abstract "12-Factor Agents · Factor 2: own your prompts"
    Your agent's prompt is a file in this repo, `app/data/instructions.md`. `make seed-workspace` turns it into version 1.0.0 of an agent in orq. Everything after this module is about changing that file on purpose and measuring what changed.

| | |
|---|---|
| **Time** | 15 min |
| **Prerequisites** | a laptop with [uv](https://docs.astral.sh/uv/), `git`, `make`, and the [orq CLI](https://docs.orq.ai/docs/cli) |
| **You will have** | your own seat in the workshop workspace: a key, a seat prefix, your refund agent at v1.0.0 with three code tools, and one trace that proves it works |

## Why

Thirty people share one orq workspace today. Each seat gets its own key and its own prefix (`ws07`), and every entity you create starts with it: `ws07-refund-agent`, `ws07-lookup_order`. Nobody overwrites anybody, and `make reset-workspace` only ever touches your own keys.

## Steps

### Step 1 · Get your key

1. Scan the QR code on the slide, or open the kickstart page the hosts show.
2. Enter your email and the passcode on the slide.
3. Open the email. It holds a ready-to-paste block: `ORQ_API_KEY`, `ORQ_PROJECT`, `WS_PREFIX` and `ORQ_WORKSPACE`.

### Step 2 · Clone and configure

```bash
git clone https://github.com/orq-ai/kickstarterai-techdays-workshop-2026
cd kickstarterai-techdays-workshop-2026
make setup                      # uv sync, and .env from .env.example
```

Paste the block from the email over the empty lines at the top of `.env`. The model lines below them are already filled in; leave them.

!!! warning "Use the prefix from your email"
    `make seed-workspace` refuses to run with an empty `WS_PREFIX` or a made-up one: the prefix is what keeps your entities apart from your neighbour's.

### Step 3 · Check, seed, smoke

```bash
make orq-doctor                 # the CLI with your key: who you are, endpoints, skills
make seed-workspace             # your agent v1.0.0, its tools, the eval dataset and the judge
make smoke-test                 # one turn to your agent
```

Expected output of the last two:

```text
── Seed · create this seat's entities ─────────────────
seat     : ws07 → <your project>/workshop
tools    : ws07-lookup_order, ws07-issue_refund, ws07-get_policy (code tools, run by orq)
agent    : ws07-refund-agent v1.0.0
dataset  : ws07-refund-eval (01M4…)
judge    : ws07-refund-policy-judge (01M4…)
── Smoke test · one turn to your agent ────────────────
agent    : ws07-refund-agent
question : Hi, I want a refund for order ord_a1, I changed my mind.
answer   : Your refund for order ord_a1 has been issued: €24.99.
tools    : lookup_order → issue_refund
trace    : dec8b671d962af0fbf70537773a7bc06
verdict  : OK, orq ran your agent and its tools
```

`make seed-workspace` is safe to run again: it only creates what is missing. It never changes an existing agent; new versions come from `make publish-agent-version` in the fix-and-eval module.

### Step 4 · Find it in the Studio

Open [my.orq.ai](https://my.orq.ai), switch to the workshop workspace, and open **Agents** > `ws07-refund-agent`. Then **Traces**: search the trace id from the smoke test.

## Gotchas

- **`orq-doctor` shows another workspace.** `orq doctor` also reports your own `orq auth login` session. The line that counts is `source: ORQ_API_KEY` from `orq whoami`: that is the key in `.env`.
- **401 on seed.** The key in `.env` has a typo or a trailing space. Paste the block again.
- **`WS_PREFIX='ws'` is not a seat prefix.** You kept the default. Use the one from your email.

## Done when

`make smoke-test` prints a trace id and `verdict : OK`.
