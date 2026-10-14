# Onboarding

| | |
|---|---|
| **Prerequisites** | a laptop with [uv](https://docs.astral.sh/uv/), `git`, `make`, and the [orq.ai CLI](https://docs.orq.ai/reference/cli) |
| **You will have** | a working gateway request using the workshop key, plus its trace in Studio |

## Why

Every model call today, yours and the agent's, goes through the **orq.ai AI Gateway**: one OpenAI-compatible endpoint in front of every model the workspace has enabled. One key, one base URL, and each call becomes a trace with its cost, tokens and latency. Before anything else, check that this works with your key.

## Steps

### Step 1 · Get your key

1. Scan the QR code on the slide, or open the kickstart page the hosts show.
2. Enter your email and the passcode on the slide.
3. Open the email. It holds a ready-to-paste block: `ORQ_API_KEY`, `ORQ_PROJECT`, `WS_PREFIX` and `ORQ_WORKSPACE`.

### Step 2 · Clone and configure

```bash {.terminal}
git clone https://github.com/orq-ai/kickstarterai-techdays-workshop-2026
cd kickstarterai-techdays-workshop-2026

# Install the locked workshop and docs dependencies.
uv sync --all-groups

# Create a local configuration file only on a fresh clone.
test -f .env || cp .env.example .env
```

`make setup` is the shortcut for these two setup operations.

Paste the block from the email over the empty lines at the top of `.env`. The model lines below them are already filled in; leave them.

**Once per new terminal**, load the workshop configuration so direct CLI and curl commands can read it:

```bash {.terminal}
set -a              # auto-export assignments to child commands
source .env        # load ORQ_API_KEY, WS_PREFIX, MODEL, and other settings
set +a              # stop auto-exporting future shell assignments
```

Workshop Python scripts load `.env` themselves. This export is for direct shell commands such as `orq` and `curl`.

Check that the CLI uses your workshop key:

```bash {.terminal}
orq whoami
```

Look for `source: ORQ_API_KEY`. If authentication fails, `orq doctor` diagnoses the configured endpoints and tooling. `make orq-doctor` runs both commands with `.env` exported.

A saved `orq auth login` session can point to another workspace. For this exercise, check that `orq whoami` reports `source: ORQ_API_KEY`.

### Step 3 · Make one gateway request

A model ID has the form `provider/model`. `app/gateway_check.py` uses `MODEL` from your `.env` to make one OpenAI-compatible Responses API call and print its trace ID.

```bash {.terminal}
uv run python -m app.gateway_check
```

`make gateway-check` is an optional shortcut for the same command. Look for `verdict : OK` and save the trace ID:

```text
── Gateway check · one request through the gateway ───────
endpoint : https://my.orq.ai/v3/router/responses
model    : openai/gpt-6-luna
answer   : An AI gateway sits between applications and AI models
           to manage and secure requests, ...
tokens   : 17 in, 48 out
trace    : 74c18139baffe8399c6029823b037995
verdict  : OK, your key and the gateway work
```

### Step 4 · Find that trace

Open [my.orq.ai](https://my.orq.ai), select the workshop workspace, then open **Observability** > **Traces** and find the ID from Step 3. Check the model, response, tokens, cost, and latency. That is the same evidence you will later use to inspect an agent turn.

![The Traces page with the gateway check selected: one responses.openai trace with a gpt-6-luna span, its model, input, output and reasoning tokens, and estimated cost.](assets/gateway-trace.png)

### Optional · Browse models and try other interfaces

In **AI Gateway** > **Models**, the Model Garden lists the models available to this workspace. The model ID in `.env` is your starting point; the provider, capabilities, and price help you choose another. Comparing models is useful, but not required before creating the agent.

![The Model Garden filtered to enabled models: GPT-6 Luna, DeepSeek, GLM, Kimi and Nemotron models, each with its provider/model id, price per token and capabilities.](assets/model-garden.png)

The same list from the terminal (requires `jq`):

```bash {.terminal}
orq models list -o json |
  jq -r '
    .[]
    | select(.enabled)
    | "\(.provider)/\(.model_id)  \(.model_type)"
  '
```

The following tabs show the same request without the workshop script. They are alternative interfaces, not three additional required calls. The gateway speaks the OpenAI API at `https://my.orq.ai/v3/router`.

=== "curl"

    ```bash {.terminal}
    curl -s https://my.orq.ai/v3/router/responses \
      -H "Authorization: Bearer $ORQ_API_KEY" \
      -H "Content-Type: application/json" \
      --data "{
        \"model\": \"$MODEL\",
        \"input\": \"In one sentence: what does an AI gateway do?\"
      }" \
      -D - |
      grep -i x-orq-trace-id
    ```

=== "orq.ai CLI"

    ```bash {.terminal}
    orq responses create \
      --model "$MODEL" \
      --input '"In one sentence: what does an AI gateway do?"' \
      -o json
    ```

=== "Python"

    ```python {.code-frame}
    from openai import OpenAI

    from app.refund_agent.config import settings  # loads .env

    client = OpenAI(api_key=settings.api_key, base_url=settings.router_url)
    raw = client.responses.with_raw_response.create(
        model=settings.model,
        input="In one sentence: what does an AI gateway do?",
    )
    print(raw.parse().output_text)
    print(raw.headers.get("x-orq-trace-id"))
    ```

These examples use the same gateway contract. `app/gateway_check.py` is the tested Python version from Step 3; the trace header confirms the request passed through orq.ai.

### Optional · Compare another model

Pick another chat model from the Model Garden and send the same request; only the model id changes:

```bash {.terminal}
uv run python -m app.gateway_check deepseek/deepseek-flash
```

Compare the two trace IDs in **Observability** > **Traces**. The model, tokens, cost, and latency will differ.

## Gotchas

- **401 API key is not valid.** The key in `.env` has a typo or a trailing space, or your shell exports an older `ORQ_API_KEY`. Paste the block again, then rerun the environment command from Step 2 before using curl or the CLI.
- **400 invalid model.** The model id has no provider, or is not enabled in the workspace. Copy it from the Model Garden as `provider/model`.

## Official docs

- [AI Gateway](https://docs.orq.ai/ai-gateway/get-started/introduction): one endpoint in front of every model
- [Models (Model Garden)](https://docs.orq.ai/ai-gateway/using-the-router): browse and enable models, `provider/model` ids
- [OpenAI-compatible API](https://docs.orq.ai/ai-gateway/features/openai-compatible-api): the OpenAI SDK with orq.ai's base URL
- [Responses API](https://docs.orq.ai/ai-gateway/features/responses-api): the endpoint every call today uses
- [API keys](https://docs.orq.ai/ai-studio/organization/api-keys): project-scoped keys, like the one in your email
- [Traces](https://docs.orq.ai/ai-studio/observability/traces): what each call records
- [orq.ai CLI](https://docs.orq.ai/reference/cli): `orq whoami`, `orq models`, `orq responses`

## Done when

`uv run python -m app.gateway_check` prints a trace id and `verdict : OK`, and you have found that trace in the Studio.
