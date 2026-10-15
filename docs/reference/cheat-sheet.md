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
uv run eq sim runs  # saved reports: .evaluatorq/sim-runs/ (or $EVALUATORQ_DIR/sim-runs/)
# Reuse a specific v1 report's cases and opening messages against v2:
make simulate-agent VERSION=2.0.0 REPLAY=".evaluatorq/sim-runs/<your-v1-baseline>.json"
make publish-agent-version [FILE=...]
make compare-versions [VERSION=latest]

# Regression gate and cleanup
make seed-eval  # once: creates your dataset and judge
make regression-eval [VERSION=2.0.0]
make reset-workspace
```

## The gateway

`$ORQ_API_KEY` and `$MODEL` come from your `.env`; export them once per terminal as in Onboarding.

```bash {.terminal}
curl -s https://my.orq.ai/v3/router/responses \
  -H "Authorization: Bearer $ORQ_API_KEY" \
  -H "Content-Type: application/json" \
  --data "{
    \"model\": \"$MODEL\",
    \"input\": \"hi\"
  }"

# The Model Garden
orq models list -o json

orq responses create \
  --model "$MODEL" \
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
    model=MODEL,
    input="hi",
).output_text
```

## Your agent

Studio shortcuts: [Agents](https://my.orq.ai/kickstartai-workshop-2026/agents) · [Tools](https://my.orq.ai/kickstartai-workshop-2026/tools) · [Traces](https://my.orq.ai/kickstartai-workshop-2026/traces) · [Datasets](https://my.orq.ai/kickstartai-workshop-2026/datasets) · [Evaluators](https://my.orq.ai/kickstartai-workshop-2026/resources/evaluators) · [Experiments](https://my.orq.ai/kickstartai-workshop-2026/experiments) · [Models](https://my.orq.ai/kickstartai-workshop-2026/router/models).

Select the project from your email's `ORQ_PROJECT`, then search for your seat prefix.

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
orq traces conversation <trace_id>
```

## Docs

| Topic | Page |
|---|---|
| Agents | [Build agents](https://docs.orq.ai/docs/ai-studio/ai-engineering/build-agents) · [Run agents](https://docs.orq.ai/docs/ai-studio/ai-engineering/run-agents) · [Responses API](https://docs.orq.ai/docs/ai-gateway/features/responses-api) |
| Quality | [Agent simulations](https://docs.orq.ai/docs/ai-studio/optimize/agent-simulations) · [Evaluators](https://docs.orq.ai/docs/ai-studio/optimize/evaluators) · [Datasets](https://docs.orq.ai/docs/ai-studio/optimize/datasets) · [Experiments](https://docs.orq.ai/docs/ai-studio/optimize/experiments) |
| Coding agents | [orq.ai MCP server](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/orq-mcp) · [orq.ai Skills](https://docs.orq.ai/docs/ai-studio/integrations/code-assistants/orq-skills) · [orq.ai CLI](https://docs.orq.ai/reference/cli) |
