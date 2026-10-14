# Cheat sheet

## Make, in workshop order

```bash
make setup orq-doctor seed-workspace smoke-test     # onboarding
make invoke-agent                                   # call your agent from Python
make agent-chat-ui                                  # chat in the browser, pick a version
make simulate-agent [VERSION=1.0.0]                 # simulated customers
make evaluatorq-dashboard                           # simulation and eval results
make publish-agent-version [FILE=...]               # your instructions -> next version
make compare-versions [VERSION=latest]              # replay prompts on @1.0.0 and VERSION
make regression-eval [VERSION=2.0.0]                # orq dataset, exit 1 on regression
make reset-workspace                                # delete your seat's entities
```

## Your agent

| What | Value |
|---|---|
| Agent key | `<WS_PREFIX>-refund-agent`, e.g. `ws07-refund-agent` |
| Model id | `agent/ws07-refund-agent` (latest), `agent/ws07-refund-agent@1.0.0` (pinned) |
| Responses endpoint | `https://my.orq.ai/v3/router/responses` |
| Code tools | `ws07-lookup_order`, `ws07-issue_refund`, `ws07-get_policy` |
| Dataset, judge | `ws07-refund-eval`, `ws07-refund-policy-judge` |

```python
from orq_ai_sdk import Orq
orq = Orq(api_key=ORQ_API_KEY)
r = orq.responses.create(model="agent/ws07-refund-agent@1.0.0", input="Refund ord_a1, I changed my mind.")
# r.output: function_call items, orq:<tool key> items with `result`, a message item
```

```bash
orq responses create --model agent/ws07-refund-agent --input '"Refund ord_a1"' -o json
orq agents retrieve ws07-refund-agent -o json
orq traces thread <trace_id>
```

## Docs

| Topic | Page |
|---|---|
| Agents | [Build agents](https://docs.orq.ai/docs/ai-studio/ai-engineering/build-agents) · [Run agents](https://docs.orq.ai/docs/ai-studio/ai-engineering/run-agents) · [Responses API](https://docs.orq.ai/docs/ai-gateway/features/responses-api) |
| Quality | [Agent simulations](https://docs.orq.ai/docs/ai-studio/optimize/agent-simulations) · [Evaluators](https://docs.orq.ai/docs/ai-studio/optimize/evaluators) · [Datasets](https://docs.orq.ai/docs/ai-studio/optimize/datasets) · [Experiments](https://docs.orq.ai/docs/ai-studio/optimize/experiments) |
| Coding agents | [Orq MCP server](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/orq-mcp) · [Orq Skills](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/orq-skills) · [CLI](https://docs.orq.ai/reference/cli) |
