---
hide: [navigation]
---

# Is your agent behaving like you expect?

**KickstartAI TechDays · 15 October 2026 · two hours.** One refund agent, hosted in orq. You meet it, let simulated customers loose on it, find what it gets wrong, fix the prompt, and prove the fix with a regression eval that would fail a build.

[Start with onboarding](modules/00.md){ .md-button .md-button--primary }
[Cheat sheet](reference/cheat-sheet.md){ .md-button }

## Before you come

- A laptop that allows `curl | sh`, with `git`, `make` and [uv](https://docs.astral.sh/uv/).
- The [orq CLI](https://docs.orq.ai/docs/cli).
- Clone the repo and install: `git clone https://github.com/orq-ai/kickstarterai-techdays-workshop-2026 && cd kickstarterai-techdays-workshop-2026 && make setup`.

Your key comes on the day, by email, after you scan the QR code on the first slide.

## The two hours

| Clock | Block | You run | Page |
|---|---|---|---|
| 0:00 | Welcome | | |
| 0:05 | Get your key and set up | `make setup orq-doctor seed-workspace smoke-test` | [Onboarding](modules/00.md) |
| 0:20 | Your coding agent (optional) | orqi, or the orq plugin in your own agent | [Coding agents](modules/01.md) |
| 0:30 | Meet the refund agent | `make agent-chat-ui`, `make invoke-agent` | [Refund agent](modules/02.md) |
| 0:45 | Simulate customers | `make simulate-agent`, `make evaluatorq-dashboard` | [Simulation](modules/03.md) |
| 1:15 | Fix it and prove it | `make publish-agent-version`, `make regression-eval` | [Fix and eval](modules/04.md) |
| 1:50 | Take home, questions | | |

Each block is a short concept on screen, then your hands on the keyboard; the hosts walk the room.

## Go further

This workshop is a two-hour cut of the full [orq.ai workshop](https://github.com/orq-ai/orq-workshop): the AI Gateway, guardrails, tracing, knowledge bases, MCP, trace insights and red teaming, on the same refund agent.
