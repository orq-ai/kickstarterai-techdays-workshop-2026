# Coding agents

| | |
|---|---|
| **Prerequisites** | onboarding done; one coding agent of your choice, or none (orqi below needs nothing else) |
| **You will have** | a coding agent that answers questions about your orq.ai workspace |

## Why

The skills are workflows written for an agent (simulate an agent, build an evaluator, analyze traces); the MCP server gives it the tools to act on your workspace. Pick **one** path below. You can skip this module entirely and follow along by hand.

## Steps

### Step 1 · Pick your agent

Run the once-per-terminal setup from [Onboarding](https://orq-ai.github.io/kickstarterai-techdays-workshop-2026/modules/00/) first; the agents read your key from the shell.

=== "orqi"

    [orqi](https://github.com/orq-ai/orqi) is the orq.ai helper agent for the terminal, with the orq.ai tools and skills already wired in.

    ```bash {.terminal}
    curl -fsSL \
      https://raw.githubusercontent.com/orq-ai/orqi/main/install.sh |
      sh

    orqi \
      "List the chat models available through the connected \
      orq.ai MCP server."
    ```

    orqi does not read `.env` by itself, so its header line must say `ORQ_API_KEY`.

    Example output, abbreviated. The exact list reflects the connected MCP session and your permissions:

    <!-- termynal -->

    ```console
    $ orqi "List the chat models available through the connected orq.ai MCP server."

    Chat models available to this MCP session:
    openai/gpt-6-luna
    baseten/deepseek-v4.1-flash
    deepseek/deepseek-flash
    nvidia/moonshotai/kimi-k3
    ...

    12 chat models available.
    ```

    !!! warning "orqi answers 401 Token verification failed"
        You used orqi before with another account, and it reuses that stored login for model calls even with `ORQ_API_KEY` exported. Move it aside and retry: `mv ~/.orqi/agent/auth.json ~/.orqi/agent/auth.json.bak`.

=== "Claude Code"

    ```bash {.terminal}
    claude plugin marketplace add orq-ai/assistant-plugins
    claude plugin install orq-skills@orq-claude-plugin
    ```

    The plugin brings the skills, the MCP server and slash commands such as `/orq:traces`.

=== "Other agents"

    ```bash {.terminal}
    npx skills add orq-ai/assistant-plugins
    ```

    Then add the MCP server `https://my.orq.ai/v2/mcp` (HTTP transport) in your agent's MCP settings. It signs you in with OAuth on first use.

    ??? info "Only accepts stdio MCP servers?"
        Use [`mcp-remote`](https://github.com/punkpeye/mcp-remote) as a local proxy. Add this to the agent's MCP configuration, then restart or reload its MCP servers:

        ```json
        {
          "mcpServers": {
            "orq": {
              "command": "npx",
              "args": ["-y", "mcp-remote", "https://my.orq.ai/v2/mcp"]
            }
          }
        }
        ```

        The first connection opens the orq.ai OAuth flow in the browser; `npx` downloads the proxy on demand.

!!! warning "One MCP path only"
    Install the MCP server through the plugin **or** by hand, not both, or it registers twice and every tool shows up double.

### Step 2 · Check which models it can access

Ask your agent:

<blockquote class="agent-prompt-frame">
  <p>List the chat models available to me through the connected orq.ai MCP server. Return their provider/model IDs.</p>
</blockquote>

Compare its list with [**AI Gateway** > **Models**](https://my.orq.ai/kickstartai-workshop-2026/router/models) in the Studio. They should match.

??? tip "Workshop models missing?"
    Add the MCP URL with your key instead of OAuth: header `Authorization: Bearer ${ORQ_API_KEY}`. In Claude Code:

    ```bash {.terminal}
    claude mcp add \
      --transport http \
      orq \
      https://my.orq.ai/v2/mcp \
      --header "Authorization: Bearer ${ORQ_API_KEY}"
    ```

    For other agents, set the same header in their MCP settings.

## Official docs

- [orq.ai MCP server](https://docs.orq.ai/ai-studio/integrations/code-assistants/orq-mcp): tools on your workspace for any MCP client, OAuth or bearer key
- [orq.ai Skills](https://docs.orq.ai/ai-studio/integrations/code-assistants/orq-skills): the workflows, and the Claude Code plugin
- [Automate evals and observability in Claude Code](https://docs.orq.ai/ai-studio/cookbooks/evaluation-safety/automate-evals-and-observability-with-claude-code): a worked example
- [orq.ai CLI](https://docs.orq.ai/reference/cli)

## Done when

Your coding agent (or orqi) lists chat-model provider/model IDs available through its connected orq.ai MCP session.
