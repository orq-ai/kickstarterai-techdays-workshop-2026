# Working in this repo with a coding agent

An orq.ai workshop repository. Participants run it by hand or with a coding agent (orqi, or any agent with the orq skills and the orq MCP server).

## Layout

- `app/refund_agent/` is the shared plumbing. `entities.py` seeds, versions and resets the orq entities; `client.py` is the one call to the agent (`ask_agent`); `tools.py` holds the tool rules that `make seed-workspace` turns into orq code tools; `config.py` reads `.env`. Compose it, do not edit it, unless a module says so.
- `app/data/instructions.md` is the agent's prompt. Participants edit it in the fix-and-eval module and publish it with `make publish-agent-version`.
- `app/web.py` + `web/index.html` is the chat UI (`make agent-chat-ui`).
- `evals/` is the regression eval (`regression.py`, `scorers.py`) and the evaluatorq simulation target (`target.py`).
- `modules/NN-name/` is one exercise each: `README.md` (the lesson), `run.py` (starter with TODOs, where the module has code), `agent_prompt.md`, `assets/`. The completed `run.py` files live at the same paths on the `solution` branch, with the reference prompt at `modules/04-fix-and-eval/solution/instructions.md`. Never put solution code on `main`.
- Diagrams are SVG sources next to their PNGs (`modules/NN-name/assets/*.svg`, `docs/assets/diagrams/*.svg`), styled by `scripts/diagram.css`. Edit the SVG, run `make diagrams`, commit both; docs embed the PNG.
- `docs/` is the MkDocs site. Module pages include `modules/NN-name/README.md` via snippets, so edit the README, not the page, and use absolute URLs in READMEs (relative links break the build).

## Conventions

- Every orq entity this repo creates is keyed `<WS_PREFIX>-…`, where `WS_PREFIX` is the participant's seat (`ws07`). `seed-workspace` and `reset-workspace` refuse anything else.
- The agent is fully managed: orq runs the model and the code tools. Call it with `model="agent/<key>[@<version>]"` on the Responses API. New versions come from `entities.publish_version` (major bumps only).
- Models come from `.env`; never hard-code one in a module.
- Credentials live in `.env` only. Never print `ORQ_API_KEY`.
- Module titles carry no numbers; numbers stay in folder names and URLs.
- Lesson pages before the simulation must not name the behaviours the simulation is meant to find.
- Use `uv run` for every Python invocation. `make test` runs without network.

## Useful orq skills here

`simulate-agent`, `build-evaluator`, `run-experiment`, `analyze-trace-failures`, `invoke-deployment`.
