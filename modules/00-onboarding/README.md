# Onboarding

| | |
|---|---|
| **Time** | 15 min |
| **Prerequisites** | a laptop with [uv](https://docs.astral.sh/uv/), `git`, `make`, and the [orq CLI](https://docs.orq.ai/reference/cli) |
| **You will have** | your own key and seat in the workshop workspace, the models it offers, and one model request sent through the orq AI Gateway from curl, the CLI and Python, with its trace |

## Why

Every model call today, yours and the agent's, goes through the **orq AI Gateway**: one OpenAI-compatible endpoint in front of every model the workspace has enabled. One key, one base URL, and each call becomes a trace with its cost, tokens and latency. Before anything else, check that this works with your key.

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

Then check the CLI sees your key:

```bash
make orq-doctor                 # orq whoami + orq doctor with the key from .env
```

`orq whoami` must say `source: ORQ_API_KEY`. `orq doctor` may also mention your own `orq auth login` session; the key is what counts.

### Step 3 · The Model Garden

Open [my.orq.ai](https://my.orq.ai) and switch to the workshop workspace.

!!! tip "Which project?"
    The Studio shows one project at a time. Your key writes to the project it belongs to: pick it in the project picker at the top left (for this workshop, **Default Project**). Everything you create later starts with your seat prefix, so search for `ws07` to find yours among thirty seats.

Open **AI Gateway** > **Models**, the Model Garden. These are the models the gateway serves to this workspace, each with its provider, type and price per token. A model id is always `provider/model`: `openai/gpt-6-luna` is the one in your `.env` as `MODEL`.

![The Model Garden filtered to enabled models: GPT-6 Luna, DeepSeek, GLM, Kimi and Nemotron models, each with its provider/model id, price per token and capabilities.](assets/model-garden.png)

The same list from the terminal:

```bash
set -a; source .env; set +a     # export the key into this shell (the CLI and curl need it)
orq models list -o json | jq -r '.[] | select(.enabled) | "\(.provider)/\(.model_id)  \(.model_type)"'
```

### Step 4 · One request: curl, CLI, Python

The gateway speaks the OpenAI API at `https://my.orq.ai/v3/router`. The same request three ways:

=== "curl"

    ```bash
    curl -s https://my.orq.ai/v3/router/responses \
      -H "Authorization: Bearer $ORQ_API_KEY" -H "Content-Type: application/json" \
      -d "{\"model\": \"$MODEL\", \"input\": \"Say hello in five words.\"}" -D - | grep -i x-orq-trace-id
    ```

=== "orq CLI"

    ```bash
    orq responses create --model "$MODEL" --input '"Say hello in five words."' -o json
    ```

=== "Python"

    ```python
    from openai import OpenAI

    client = OpenAI(api_key=ORQ_API_KEY, base_url="https://my.orq.ai/v3/router")
    response = client.responses.create(model="openai/gpt-6-luna", input="Say hello in five words.")
    print(response.output_text)
    ```

The Python version is `app/smoke.py`, the last setup check:

```bash
make smoke-test
```

```text
── Smoke test · one request through the gateway ───────
endpoint : https://my.orq.ai/v3/router/responses
model    : openai/gpt-6-luna
answer   : An AI gateway sits between applications and AI models to manage and secure requests, ...
tokens   : 17 in, 48 out
trace    : 74c18139baffe8399c6029823b037995
verdict  : OK, your key and the gateway work
```

Every response carries an `x-orq-trace-id` header: the proof the call went through orq.

### Step 5 · Swap the model, find the traces

Pick another chat model from the Model Garden and send the same request; only the model id changes:

```bash
uv run python -m app.smoke deepseek/deepseek-flash
```

Then open **Traces** in the Studio and search the two trace ids. Compare the model, tokens, cost and latency of the two calls.

![The Traces page with the smoke test selected: one responses.openai trace with a gpt-6-luna span, its model, input, output and reasoning tokens, and estimated cost.](assets/gateway-trace.png)

## Gotchas

- **401 API key is not valid.** The key in `.env` has a typo or a trailing space, or your shell exports an older `ORQ_API_KEY`. Paste the block again; for curl and the CLI run `set -a; source .env; set +a` first.
- **400 invalid model.** The model id has no provider, or is not enabled in the workspace. Copy it from the Model Garden as `provider/model`.

## Official docs

- [AI Gateway](https://docs.orq.ai/ai-gateway/get-started/introduction): one endpoint in front of every model
- [Models (Model Garden)](https://docs.orq.ai/ai-gateway/using-the-router): browse and enable models, `provider/model` ids
- [OpenAI-compatible API](https://docs.orq.ai/ai-gateway/features/openai-compatible-api): the OpenAI SDK with orq's base URL
- [Responses API](https://docs.orq.ai/ai-gateway/features/responses-api): the endpoint every call today uses
- [API keys](https://docs.orq.ai/ai-studio/organization/api-keys): project-scoped keys, like the one in your email
- [Traces](https://docs.orq.ai/ai-studio/observability/traces): what each call records
- [orq CLI](https://docs.orq.ai/reference/cli): `orq whoami`, `orq models`, `orq responses`

## Done when

`make smoke-test` prints a trace id and `verdict : OK`, and you have found that trace in the Studio.
