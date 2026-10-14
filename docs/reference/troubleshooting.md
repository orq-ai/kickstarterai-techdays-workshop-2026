# Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `WS_PREFIX='…' is not a seat prefix` | `.env` still has the default or an empty prefix | paste `WS_PREFIX=ws<NN>` from your kickstart email |
| `401 API key is not valid for this workspace` | a typo in the key, or a stale `ORQ_API_KEY` in your shell picked up by another tool | the repo reads `.env` and wins over the shell; for the CLI and orqi run `set -a; source .env; set +a` first |
| `400` invalid model on a gateway call | the model id has no provider, or the model is not enabled in the workspace | copy it from the Model Garden as `provider/model` |
| `make orq-doctor` shows another workspace under `auth` | your own `orq auth login` session | `orq whoami` above it says `source: ORQ_API_KEY`: that is the key that counts |
| orqi: `401 Token verification failed` although `make smoke-test` works | orqi reuses an older stored login for model calls | `mv ~/.orqi/agent/auth.json ~/.orqi/agent/auth.json.bak`, then run orqi again with `.env` exported |
| `eq dashboard` says `ORQ_API_KEY was rejected` | it read an older key exported in your shell | use `make evaluatorq-dashboard`, which exports `.env` first |
| coding agent cannot find your agent | its MCP connection signed in over OAuth to your own workspace | connect with the bearer header, see the coding agents module |
| the chat UI says the agent does not exist | not seeded yet | `make seed-workspace` |
| the version picker has no `@2.0.0` | nothing published yet, or unchanged instructions | edit `app/data/instructions.md`, `make publish-agent-version`, reload the page |
| a refund in the chat does not show as refunded in the Orders table | each code-tool call starts from the same orders | expected; the tool result and the trace are the evidence |
| `make simulate-agent` says `missing: TODO …` | the starter still has TODOs | fill them in; it runs with what is there meanwhile |
| a simulation or eval result differs between two runs | the model is not deterministic | run twice; the thresholds carry a margin for this |
| `mkdocs build --strict` fails | broken link or missing snippet | links inside module READMEs must be absolute URLs, not relative paths |
