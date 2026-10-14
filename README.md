<p align="center">
  <img src="docs/assets/og-image.png" alt="orq.ai workshop" width="820">
</p>

# Is your agent behaving like you expect?

The hands-on part of the KickstartAI TechDays session on 15 October 2026: two hours with a refund agent hosted in [orq.ai](https://orq.ai). You simulate customers against version 1, find what it gets wrong, fix the prompt, publish version 2, and prove the fix with a regression eval on an orq.ai dataset.

Docs site: **https://orq-ai.github.io/kickstarterai-techdays-workshop-2026**

## Quickstart

You need [uv](https://docs.astral.sh/uv/), `git`, `make` and the [orq.ai CLI](https://docs.orq.ai/reference/cli). Your key, project and seat prefix come by email on the day.

```bash
git clone https://github.com/orq-ai/kickstarterai-techdays-workshop-2026
cd kickstarterai-techdays-workshop-2026
make setup                          # uv sync, .env from the example
# paste the block from your kickstart email into .env
make orq-doctor smoke-test
```

Then follow the docs site, or `make help` for every target in order.

## The flow

| Page | Folder | You run |
|---|---|---|
| Onboarding | `modules/00-onboarding` | `make setup orq-doctor smoke-test`; the gateway from curl, CLI and Python |
| Coding agents | `modules/01-coding-agents` | orqi, or the orq.ai plugin in your own agent |
| Refund agent | `modules/02-refund-agent` | `make seed-workspace`, `make agent-chat-ui`, `make invoke-agent` |
| Simulation | `modules/03-simulation` | `make simulate-agent`, `make evaluatorq-dashboard` |
| Fix and eval | `modules/04-fix-and-eval` | `make publish-agent-version`, `make compare-versions`, `make regression-eval` |

`main` holds the exercises with TODOs. The public `solution` branch has the same files completed; look at one file without switching branches: `git show origin/solution:modules/03-simulation/run.py`.

## Go further

This is a two-hour cut of the full [orq.ai workshop](https://github.com/orq-ai/orq-workshop): the AI Gateway, guardrails, tracing, knowledge bases, MCP, trace insights and red teaming, on the same refund agent.

## License

MIT, see `LICENSE`.
