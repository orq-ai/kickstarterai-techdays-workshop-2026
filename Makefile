# KickstartAI TechDays workshop. Targets are listed in the order you run them: `make help`.
.DEFAULT_GOAL := help
SHELL := /bin/bash
UV ?= uv
RUN := $(UV) run
VERSION ?=
FILE ?= app/data/instructions.md
MARP ?= $(shell command -v marp 2>/dev/null || echo npx -y @marp-team/marp-cli)

help: ## List targets in workshop order
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-22s\033[0m %s\n",$$1,$$2}'

# ── Onboarding ──
setup: ## Install Python deps (uv) and create .env from the example if missing
	$(UV) sync --all-groups
	@test -f .env || { cp .env.example .env; echo "Created .env. Paste the block from your kickstart email into it."; }

orq-doctor: ## orq CLI check with the key from .env: who you are, endpoints, skills
	@set -a; source .env; set +a; unset ORQ_WORKSPACE; orq whoami && orq doctor

gateway-check: ## One model request through the orq.ai AI Gateway: answer, tokens, trace id
	$(RUN) python -m app.gateway_check

# ── Refund agent ──
seed-workspace: ## Create your agent v1.0.0 and its code tools (idempotent)
	$(RUN) python -m app.refund_agent.entities seed

seed-eval: ## Create the regression dataset and policy judge (idempotent)
	$(RUN) python -m app.refund_agent.entities seed-eval

invoke-agent: ## Inspect your agent and call it from Python (modules/02-refund-agent/run.py)
	$(RUN) python modules/02-refund-agent/run.py

agent-chat-ui: ## Chat with your agent in the browser on http://127.0.0.1:8002 (pick a version)
	$(RUN) python -m app.web

# ── Simulation ──
simulate-agent: ## Simulate VERSION=1.0.0, or replay saved cases with REPLAY=path/to/run.json
	$(RUN) python modules/03-simulation/run.py $(or $(VERSION),1.0.0) $(if $(REPLAY),--replay "$(REPLAY)")

evaluatorq-dashboard: ## Simulation and eval results in the browser (eq dashboard), with the key from .env
	@set -a; source .env; set +a; $(RUN) eq dashboard

# ── Fix and eval ──
publish-agent-version: ## Publish FILE (default app/data/instructions.md) as your agent's next version; no-op if unchanged
	$(RUN) python -m app.refund_agent.entities publish --file $(FILE)

compare-versions: ## Replay your problem prompts on @1.0.0 and VERSION (default latest) (modules/04-fix-and-eval/run.py)
	$(RUN) python modules/04-fix-and-eval/run.py $(or $(VERSION),latest)

regression-eval: ## Run the orq dataset against VERSION (default 2.0.0); exit 1 on regression
	$(RUN) python -m evals.regression --version $(or $(VERSION),2.0.0)

# ── Housekeeping ──
reset-workspace: ## Delete your seat's agent, tools, dataset and judge (only keys starting with WS_PREFIX-)
	$(RUN) python -m app.refund_agent.entities reset

test: ## Unit tests, no network
	$(RUN) pytest -q

docs-serve: ## Live docs at http://127.0.0.1:8000
	$(RUN) mkdocs serve

docs-build: ## Strict docs build (fails on broken links)
	$(RUN) mkdocs build --strict

diagrams: ## Export diagram SVG sources to committed PNGs
	$(UV) run --with playwright python scripts/export_diagrams.py

slides: ## Render slides/workshop.md to HTML with Marp
	$(MARP) slides/workshop.md --theme slides/orq-theme.css -o slides/workshop.html

deck: ## Serve the reveal.js deck in slides/kickstart on :8000 (add ?code=XXXX to show the login code)
	python3 -m http.server 8000 -d slides/kickstart

.PHONY: help setup orq-doctor seed-workspace seed-eval gateway-check invoke-agent agent-chat-ui simulate-agent evaluatorq-dashboard publish-agent-version compare-versions regression-eval reset-workspace test docs-serve docs-build diagrams slides deck
