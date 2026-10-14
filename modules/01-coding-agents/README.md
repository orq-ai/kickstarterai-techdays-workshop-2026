# Coding agents

| | |
|---|---|
| **Time** | 10 min |
| **Prerequisites** | onboarding done; one coding agent of your choice, or none (orqi below needs nothing else) |
| **You will have** | a coding agent that answers questions about your orq.ai workspace |

## Why

The skills are workflows written for an agent (simulate an agent, build an evaluator, analyze traces); the MCP server gives it the tools to act on your workspace. Pick **one** path below. You can skip this module entirely and follow along by hand.

## Steps

### Step 1 · Pick your agent

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

    orqi does not read `.env` by itself. Complete the once-per-terminal environment setup in Onboarding before running it; its header line must say `ORQ_API_KEY`.

    Example output, abbreviated. The exact list reflects the connected MCP session and your permissions:

    ```text {.terminal}
    $ orqi "List the chat models available through the connected orq.ai MCP server."

    Chat models available to this MCP session:
    openai/gpt-6-luna
    baseten/deepseek-v4.1-flash
    deepseek/deepseek-flash
    nvidia/moonshotai/kimi-k3
    ...

    12 chat models available.
    ```

=== "Claude Code"

    ```bash {.terminal}
    claude plugin marketplace add orq-ai/assistant-plugins
    claude plugin install orq-skills@orq-claude-plugin
    ```

    The plugin brings the skills, the MCP server and slash commands such as `/orq:traces`.

    If OAuth does not expose the workshop models, complete the once-per-terminal environment setup in Onboarding, then add the workshop bearer-key connection:

    ```bash {.terminal}
    claude mcp add \
      --transport http \
      orq \
      https://my.orq.ai/v2/mcp \
      --header "Authorization: Bearer ${ORQ_API_KEY}"
    ```

=== "Other agents"

    ```bash {.terminal}
    npx skills add orq-ai/assistant-plugins
    ```

    Then add the MCP server `https://my.orq.ai/v2/mcp` (HTTP transport) in your agent's MCP settings. It signs you in with OAuth on first use. If OAuth does not expose the workshop models, configure the same URL with the header `Authorization: Bearer ${ORQ_API_KEY}` after completing the once-per-terminal environment setup in Onboarding.

    **Manual MCP with `npx`.** If your coding agent accepts only local stdio MCP servers, use [`mcp-remote`](https://github.com/punkpeye/mcp-remote) as a local proxy. Add this to that agent's MCP configuration, then restart or reload its MCP servers:

    ```json
    {
      "mcpServers": {
        "orq": {
          "command": "npx",
          "args": [
            "-y",
            "mcp-remote",
            "https://my.orq.ai/v2/mcp"
          ]
        }
      }
    }
    ```

    The first connection opens the orq.ai OAuth flow in the browser. `npx` downloads the proxy on demand; no global installation is required.

!!! warning "One MCP path only"
    Install the MCP server through the plugin **or** by hand, not both, or it registers twice and every tool shows up double.

### Step 2 · Check which models it can access

Ask your agent:

<blockquote class="claude-code-frame">
  <p>List the chat models available to me through the connected orq.ai MCP server. Return their provider/model IDs.</p>
</blockquote>

The agent can answer this with its model-list tool. Its answer reflects the models exposed to the current MCP session and your permissions, so compare it with the **AI Gateway** > **Models** list you can see in the Studio. Do not ask it to identify the workspace: that is not a reliable MCP capability.

!!! warning "orqi answers 401 Token verification failed"
    You used orqi before with another account, and it reuses that stored login for model calls even with `ORQ_API_KEY` exported. Move it aside and retry: `mv ~/.orqi/agent/auth.json ~/.orqi/agent/auth.json.bak`.

The simulation and fix-and-eval modules each include a Claude Code frame you can hand to the same agent once you have results.

## Official docs

- [orq.ai MCP server](https://docs.orq.ai/ai-studio/integrations/code-assistants/orq-mcp): tools on your workspace for any MCP client, OAuth or bearer key
- [orq.ai Skills](https://docs.orq.ai/ai-studio/integrations/code-assistants/orq-skills): the workflows, and the Claude Code plugin
- [Automate evals and observability in Claude Code](https://docs.orq.ai/ai-studio/cookbooks/evaluation-safety/automate-evals-and-observability-with-claude-code): a worked example
- [orq.ai CLI](https://docs.orq.ai/reference/cli)

## Done when

Your coding agent (or orqi) lists chat-model provider/model IDs available through its connected orq.ai MCP session.
