---
hide: [navigation]
---

# Is your agent behaving like you expect?

**KickstartAI TechDays · 15 October 2026 · two hours.** One refund agent, hosted in orq.ai. You meet it, let simulated customers loose on it, find what it gets wrong, fix the prompt, and prove the fix with a regression eval that would fail a build.

[Start with onboarding](modules/00.md){ .md-button .md-button--primary }
[Cheat sheet](reference/cheat-sheet.md){ .md-button }

## Before you come

You need a laptop with Python 3.11–3.13, `git`, `make`, and [uv](https://docs.astral.sh/uv/). Install the [orq.ai CLI](https://docs.orq.ai/reference/cli) before the workshop; it is used for inspection and quick API reproduction.

```bash {.terminal}
# Clone once. `make setup` runs `uv sync --all-groups`.
git clone https://github.com/orq-ai/kickstarterai-techdays-workshop-2026
cd kickstarterai-techdays-workshop-2026
make setup
```

`make setup` installs the pinned workshop runtime from `pyproject.toml`:

| Package | Why it is here |
|---|---|
| [`orq-ai-sdk`](https://github.com/orq-ai/orq-python) | Create and version orq.ai resources; invoke managed agents from Python |
| [`openai`](https://github.com/openai/openai-python) | OpenAI-compatible client used for router and evaluatorq calls |
| [`evaluatorq`](https://github.com/orq-ai/evaluatorq) | Simulations, dataset jobs, scorers, and `eq dashboard` |
| `python-dotenv` | Loads the supplied orq.ai key and workshop configuration from `.env` |

You do **not** need to install these packages individually with `pip`; `uv` uses the repository lockfile for the tested versions. Your orq.ai key, project, workspace, and seat prefix arrive by email on the day after you scan the QR code on the first slide.

## Official resources

- [orq.ai documentation](https://docs.orq.ai/): Agents, AI Gateway, tools, evaluators, experiments, and observability
- [orq.ai Python SDK](https://github.com/orq-ai/orq-python): the `orq_ai_sdk` package used by this workshop
- [orq.ai CLI reference](https://docs.orq.ai/reference/cli): install and command reference
- [evaluatorq documentation](https://orq-ai.github.io/evaluatorq/): simulations, jobs, evaluators, and dashboards
- [evaluatorq on GitHub](https://github.com/orq-ai/evaluatorq): source, examples, and issue tracker
- [evaluatorq on PyPI](https://pypi.org/project/evaluatorq/): package releases and install metadata

## The two hours

| Clock | Block | You run | Page |
|---|---|---|---|
| 0:00 | Welcome | | |
| 0:05 | Get your key, call a model through the gateway | `make setup orq-doctor gateway-check`, curl, Python | [Onboarding](modules/00.md) |
| 0:20 | Your coding agent (optional) | orqi, or the orq.ai plugin in your own agent | [Coding agents](modules/01.md) |
| 0:30 | Create and meet the refund agent | `make seed-workspace agent-chat-ui invoke-agent` | [Refund agent](modules/02.md) |
| 0:45 | Simulate customers | `make simulate-agent`, `make evaluatorq-dashboard` | [Simulation](modules/03.md) |
| 1:15 | Fix it and prove it | `make publish-agent-version`, `make regression-eval` | [Fix and eval](modules/04.md) |
| 1:50 | Take home, questions | | |

Each block is a short concept on screen, then your hands on the keyboard; the hosts walk the room.

## Go further

This workshop is a two-hour cut of the full [orq.ai workshop](https://github.com/orq-ai/orq-workshop): the AI Gateway, guardrails, tracing, knowledge bases, MCP, trace insights and red teaming, on the same refund agent.
