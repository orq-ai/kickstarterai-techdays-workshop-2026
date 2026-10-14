"""make smoke-test: one model request through the orq AI Gateway, from Python. The last setup check.

What: the plain OpenAI SDK with its base URL pointed at orq's router, one Responses API call to
MODEL from .env. Nothing orq-specific in the call: any OpenAI-compatible client works this way.
Why: if this passes, the key, the gateway and the model all work. The `x-orq-trace-id` header is
the proof the call went through orq.
How: `make smoke-test` (or `uv run python -m app.smoke [provider/model]`). Exits non-zero on failure.
"""

import sys

from openai import OpenAI

from app.refund_agent.config import settings

QUESTION = "In one sentence: what does an AI gateway do?"


def main() -> None:
    settings.require_key()
    model = sys.argv[1] if len(sys.argv) > 1 else settings.model
    client = OpenAI(api_key=settings.api_key, base_url=settings.router_url)  # the only orq-specific line
    raw = client.responses.with_raw_response.create(model=model, input=QUESTION)
    response = raw.parse()
    trace_id = raw.headers.get("x-orq-trace-id")

    print("── Smoke test · one request through the gateway ───────")
    print(f"endpoint : {settings.router_url}/responses")
    print(f"model    : {model}")
    print(f"answer   : {response.output_text.strip()[:140]}")
    print(f"tokens   : {response.usage.input_tokens} in, {response.usage.output_tokens} out")
    print(f"trace    : {trace_id}")

    assert trace_id, "no x-orq-trace-id header: the call did not go through orq"
    print("verdict  : OK, your key and the gateway work")
    print("next     : open Traces in the Studio and search the trace id")


if __name__ == "__main__":
    main()
