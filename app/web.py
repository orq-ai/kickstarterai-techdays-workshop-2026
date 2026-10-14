"""make agent-chat-ui: talk to your managed agent in a browser, one trace link per answer.

What: four routes.
    GET  /              web/index.html
    GET  /api/agent     your agent's key and the versions the picker offers
    GET  /api/backend   the mock backend, read-only: your orders and the policy documents
    POST /api/chat      one turn: {message, history, version} -> {answer, tool_calls, trace_url, history}
The agent lives in orq; one chat turn is one Responses call to `agent/<seat>-refund-agent@<version>`
(see `ask_agent` in app/refund_agent/client.py). orq runs the model and the code tools.

Stateless: the browser sends back the conversation it has (user and assistant text only), so
switching versions in the picker starts a new conversation and a replay on v1 and v2 begins from
the same first message. /api/backend is a static projection of app/data/orders.json and
app/data/kb/: what the code tools were built from, not what they return live. A refund never
changes it (each code-tool call starts from the same orders).

How: `make agent-chat-ui`, then open http://127.0.0.1:8002.
"""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import quote

import uvicorn
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route

from app.refund_agent import tools
from app.refund_agent.client import ask_agent, make_orq
from app.refund_agent.config import ROOT, settings
from app.refund_agent.entities import current_agent, versions

INDEX_HTML = ROOT / "web" / "index.html"
PORT = 8002
VERSION_SAFE = set("0123456789.")  # what a version pin may contain, besides "latest"
ORDER_FIELDS = ("id", "item", "amount", "delivered_days_ago", "refunded")  # never owner_id or notes


def trace_url(trace_id: str | None) -> str | None:
    """Studio deep link to one trace; the Traces page when ORQ_WORKSPACE is not set."""
    if not trace_id:
        return None
    if not settings.workspace:
        return f"{settings.base_url}/traces"
    return f"{settings.base_url}/{quote(settings.workspace, safe='')}/traces/(trace:{quote(trace_id, safe='')})"


def backend_view() -> dict[str, Any]:
    """The allowlisted, read-only projection the sidebar shows: the session user's orders without
    owner ids or notes (which hold another customer's contact details), and the four policy files."""
    owned = [o for o in tools._FIXTURE["orders"] if o["owner_id"] == tools._FIXTURE["session_user_id"]]
    return {
        "orders": [{field: order[field] for field in ORDER_FIELDS} for order in owned],
        "policies": [
            {"topic": topic, "text": (tools.KB_DIR / f"{topic}.md").read_text()} for topic in tools.POLICY_TOPICS
        ],
    }


def _error(status: int, detail: str) -> JSONResponse:
    return JSONResponse({"detail": detail}, status_code=status)


def index(request: Request) -> FileResponse:
    return FileResponse(INDEX_HTML)


async def get_agent(request: Request) -> JSONResponse:
    if not settings.api_key:
        return _error(503, "ORQ_API_KEY is empty. Add the block from your kickstart email to .env, then restart the chat.")
    try:
        agent = await run_in_threadpool(lambda: current_agent(make_orq()))
    except Exception:  # noqa: BLE001  the UI exposes setup guidance, not provider diagnostics
        return _error(502, "Could not reach orq to load agent setup. Check ORQ_API_KEY and your connection, then try again.")
    if agent is None:
        return _error(404, f"{settings.agent_key} does not exist yet: run `make seed-workspace`")
    return JSONResponse({"key": settings.agent_key, "versions": ["latest", *versions(agent)]})


async def get_backend(request: Request) -> JSONResponse:
    return JSONResponse(backend_view())


def _clean_history(history: Any) -> list[dict[str, str]] | None:
    """User and assistant text turns only; None when the shape is wrong."""
    if not isinstance(history, list):
        return None
    clean = []
    for message in history:
        if not isinstance(message, dict) or message.get("role") not in ("user", "assistant"):
            return None
        if not isinstance(message.get("content"), str):
            return None
        clean.append({"role": message["role"], "content": message["content"]})
    return clean


async def post_chat(request: Request) -> JSONResponse:
    if not settings.api_key:
        return _error(500, "ORQ_API_KEY is empty. Paste the block from your kickstart email into .env.")
    try:
        body = await request.json()
    except ValueError:
        return _error(400, "body must be JSON")
    body = body if isinstance(body, dict) else {}
    message = body.get("message")
    history = _clean_history(body.get("history") or [])
    version = body.get("version") or "latest"
    if not isinstance(message, str) or not message.strip() or history is None:
        return _error(422, "expected {message: non-empty string, history: [{role, content}], version: string}")
    if not isinstance(version, str) or (version != "latest" and not set(version) <= VERSION_SAFE):
        return _error(422, "version must be latest or like 2.0.0")

    started = time.perf_counter()
    conversation = [*history, {"role": "user", "content": message}]
    try:
        turn = await run_in_threadpool(ask_agent, conversation, version)
    except Exception as exc:  # noqa: BLE001  shown in the chat, not a stack trace
        return _error(502, f"orq error: {str(exc)[:300]}")
    return JSONResponse(
        {
            "answer": turn.answer,
            "tool_calls": [
                {
                    "name": c.name,
                    "ok": isinstance(c.result, dict) and bool(c.result.get("ok")),
                    "error": c.result.get("error") if isinstance(c.result, dict) else None,
                }
                for c in turn.tool_calls
            ],
            "trace_id": turn.trace_id,
            "trace_url": trace_url(turn.trace_id),
            "history": [*conversation, {"role": "assistant", "content": turn.answer}],
            "version": version,
            "seconds": round(time.perf_counter() - started, 1),
        }
    )


app = Starlette(
    routes=[
        Route("/fonts/kurrent.woff2", lambda request: FileResponse(ROOT / "slides/kickstart/assets/ESKlarheitKurrent-Rg.woff2")),
        Route("/fonts/kurrent-medium.woff2", lambda request: FileResponse(ROOT / "slides/kickstart/assets/ESKlarheitKurrent-Md.woff2")),
        Route("/fonts/kurrent-semibold.woff2", lambda request: FileResponse(ROOT / "slides/kickstart/assets/ESKlarheitKurrent-Smbd.woff2")),
        Route("/fonts/kurrent-mono.ttf", lambda request: FileResponse(ROOT / "slides/kickstart/assets/ESKlarheitKurrentMono-Md.ttf")),
        Route("/", index),
        Route("/api/agent", get_agent),
        Route("/api/backend", get_backend),
        Route("/api/chat", post_chat, methods=["POST"]),
    ]
)

if __name__ == "__main__":
    # web/index.html is read per request: edit it and refresh, no restart.
    uvicorn.run("app.web:app", host="127.0.0.1", port=PORT, reload=True, reload_dirs=[str(ROOT / "app")])
