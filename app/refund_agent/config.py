"""Every setting the app reads, in one place, all from the environment.

The repo `.env` is loaded on import and wins over the shell, so a stale `ORQ_API_KEY` exported
months ago cannot hijack a workshop run. Modules read `settings.<field>`; nothing else in `app/`
touches `os.environ`.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "app" / "data"
INSTRUCTIONS = DATA_DIR / "instructions.md"  # the agent's prompt: v1 on a fresh clone, yours after module 04

# The repo .env wins over a stale shell export.
load_dotenv(os.environ.get("ORQ_ENV_FILE", ROOT / ".env"), override=True)

SEAT_PREFIX = re.compile(r"^ws\d{2,3}$")  # ws07: one per participant, from the kickstart email


def _env(name: str, default: str = "") -> str:
    """One variable, stripped; the default (empty by default) when it is unset."""
    return os.environ.get(name, default).strip()


@dataclass(frozen=True)
class Settings:
    """Read once at import; `settings` below is the single instance the whole app shares."""

    api_key: str = field(default_factory=lambda: _env("ORQ_API_KEY"))
    base_url: str = field(
        default_factory=lambda: _env("ORQ_BASE_URL", "https://my.orq.ai").rstrip("/")
    )
    project: str = field(default_factory=lambda: _env("ORQ_PROJECT"))
    # Workspace key (the slug in Studio URLs). The API key only carries the workspace UUID, so
    # the chat UI reads this to deep-link a trace.
    workspace: str = field(default_factory=lambda: _env("ORQ_WORKSPACE"))
    # Your seat: every entity key starts with it (ws07-refund-agent), so seats never collide.
    prefix: str = field(default_factory=lambda: _env("WS_PREFIX"))
    model: str = field(default_factory=lambda: _env("MODEL", "openai/gpt-6-luna"))
    judge_model: str = field(default_factory=lambda: _env("JUDGE_MODEL", "openai/gpt-6-luna"))
    identity_id: str = field(default_factory=lambda: _env("IDENTITY_ID", "customer-user_001"))

    @property
    def router_url(self) -> str:
        """The OpenAI-compatible gateway, where `agent/<key>` models live."""
        return f"{self.base_url}/v3/router"

    def key(self, name: str) -> str:
        """Entity key with your seat prefix, e.g. ws07-refund-agent."""
        return f"{self.prefix}-{name}"

    @property
    def agent_key(self) -> str:
        return self.key("refund-agent")

    @property
    def path(self) -> str:
        """Entity storage path: `<project>/workshop`, or ORQ_PATH when the email gives one."""
        return _env("ORQ_PATH", f"{self.project}/workshop")

    def require_key(self) -> Settings:
        """Fail early with a fix, instead of a 401 three calls later."""
        if not self.api_key:
            raise SystemExit("ORQ_API_KEY is empty. Paste the block from your kickstart email into .env.")
        return self

    def require_seat(self) -> Settings:
        """Writes need an assigned seat prefix (ws07) and project, so two seats never touch the same keys."""
        self.require_key()
        if not SEAT_PREFIX.match(self.prefix):
            raise SystemExit(
                f"WS_PREFIX={self.prefix!r} is not a seat prefix. Use the one from your kickstart email, e.g. WS_PREFIX=ws07."
            )
        if not self.project and not _env("ORQ_PATH"):
            raise SystemExit("ORQ_PROJECT is empty. Paste it from your kickstart email.")
        return self


settings = Settings()
