# Glossary

**Managed agent.** An agent hosted by orq.ai: instructions, model, tools, limits and versions in one entity. Invoked through the Responses API as `model="agent/<key>"`, pinned with `@<version>`. [Docs](https://docs.orq.ai/docs/ai-studio/ai-engineering/build-agents)

**Code tool.** A Python tool that orq.ai runs next to the agent. It receives the call's arguments in `params` and returns what it leaves in `result`. In this repo they are generated from `app/refund_agent/tools.py`.

**Agent version.** Every update with `version_increment` creates a new version (`1.0.0`, `2.0.0`); old versions stay callable as `agent/<key>@<version>`.

**Seat prefix.** `WS_PREFIX`, e.g. `ws07`. Every entity you create starts with it, so thirty participants share one workspace without collisions.

**Simulation.** A user simulator plays a persona chasing a goal against your agent, for a few turns; a judge scores the transcript against `must_happen` / `must_not_happen` criteria. From [evaluatorq](https://docs.orq.ai/docs/ai-studio/optimize/agent-simulations).

**Persona, scenario, criterion.** Who the simulated customer is; what they want and the facts of their case; what the agent must or must not do in that conversation.

**Dataset.** Rows of inputs and expected outputs stored in orq.ai. The regression eval reads `ws07-refund-eval` with `DatasetIdInput`. [Docs](https://docs.orq.ai/docs/ai-studio/optimize/datasets)

**Evaluator / LLM judge.** A scorer stored in orq.ai. `ws07-refund-policy-judge` is an LLM judge that answers true or false. [Docs](https://docs.orq.ai/docs/ai-studio/optimize/evaluators)

**Experiment.** One evaluatorq run uploaded to the Studio with per-row verdicts, next to earlier runs. [Docs](https://docs.orq.ai/docs/ai-studio/optimize/experiments)

**Regression eval.** The same dataset and scorers on every version; a mean below its threshold exits 1, so it can gate a pull request.

**evaluatorq.** orq.ai's Python and TypeScript evaluation framework: jobs over datasets, simulations, `eq dashboard`. [Docs](https://docs.orq.ai/docs/ai-studio/cookbooks/evaluation-safety/evaluator-q)

**orq.ai MCP server / orq.ai Skills.** `https://my.orq.ai/v2/mcp` gives a coding agent tools on your workspace; the skills are workflows (`simulate-agent`, `build-evaluator`, ...) it can follow. [MCP](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/orq-mcp) · [Skills](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/orq-skills)

**orqi.** The orq.ai helper agent for the terminal, with the orq.ai MCP tools and skills built in. Alpha. [GitHub](https://github.com/orq-ai/orqi)
