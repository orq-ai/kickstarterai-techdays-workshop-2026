# Cheat sheet

## Make, in workshop order

```bash {.terminal}
# Onboarding: key + gateway
make setup orq-doctor gateway-check

# Agent: create, inspect, and chat
make seed-workspace
make invoke-agent
make agent-chat-ui

# Simulation and prompt versions
make simulate-agent [VERSION=1.0.0]
make evaluatorq-dashboard
make publish-agent-version [FILE=...]
make compare-versions [VERSION=latest]

# Regression gate and cleanup
make regression-eval [VERSION=2.0.0]
make reset-workspace
```

## The gateway

```bash {.terminal}
curl -s https://my.orq.ai/v3/router/responses \
  -H "Authorization: Bearer $ORQ_API_KEY" \
  -H "Content-Type: application/json" \
  --data '{
    "model": "openai/gpt-6-luna",
    "input": "hi"
  }'

# The Model Garden
orq models list -o json

orq responses create \
  --model openai/gpt-6-luna \
  --input '"hi"' \
  -o json
```

```python {.code-frame}
from openai import OpenAI
client = OpenAI(
    api_key=ORQ_API_KEY,
    base_url="https://my.orq.ai/v3/router",
)
client.responses.create(
    model="openai/gpt-6-luna",
    input="hi",
).output_text
```

## Your agent

| What | Value |
|---|---|
| Agent key | `<WS_PREFIX>-refund-agent`, e.g. `ws07-refund-agent` |
| Model id | `agent/ws07-refund-agent` (latest), `agent/ws07-refund-agent@1.0.0` (pinned) |
| Responses endpoint | `https://my.orq.ai/v3/router/responses` |
| Code tools | `ws07-lookup_order`, `ws07-issue_refund`, `ws07-get_policy` |
| Dataset, judge | `ws07-refund-eval`, `ws07-refund-policy-judge` |

```python {.code-frame}
from orq_ai_sdk import Orq
orq = Orq(api_key=ORQ_API_KEY)
r = orq.responses.create(
    model="agent/ws07-refund-agent@1.0.0",
    input="Refund ord_a1, I changed my mind.",
)
# r.output: function_call items, orq:<tool key> items with result,
# then a message item
```

```bash {.terminal}
orq responses create \
  --model agent/ws07-refund-agent \
  --input '"Refund ord_a1"' \
  -o json

orq agents retrieve ws07-refund-agent -o json
orq traces thread <trace_id>
```

## Docs

| Topic | Page |
|---|---|
| Agents | [Build agents](https://docs.orq.ai/docs/ai-studio/ai-engineering/build-agents) · [Run agents](https://docs.orq.ai/docs/ai-studio/ai-engineering/run-agents) · [Responses API](https://docs.orq.ai/docs/ai-gateway/features/responses-api) |
| Quality | [Agent simulations](https://docs.orq.ai/docs/ai-studio/optimize/agent-simulations) · [Evaluators](https://docs.orq.ai/docs/ai-studio/optimize/evaluators) · [Datasets](https://docs.orq.ai/docs/ai-studio/optimize/datasets) · [Experiments](https://docs.orq.ai/docs/ai-studio/optimize/experiments) |
| Coding agents | [orq.ai MCP server](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/orq-mcp) · [orq.ai Skills](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/orq-skills) · [orq.ai CLI](https://docs.orq.ai/reference/cli) |
