# Coding agents

| | |
|---|---|
| **Time** | 10 min |
| **Prerequisites** | onboarding done; one coding agent of your choice, or none (orqi below needs nothing else) |
| **You will have** | a coding agent that answers questions about your orq workspace |

## Why

The skills are workflows written for an agent (simulate an agent, build an evaluator, analyze traces); the MCP server gives it the tools to act on your workspace. Pick **one** path below. You can skip this module entirely and follow along by hand.

## Steps

### Step 1 · Pick your agent

=== "orqi"

    [orqi](https://github.com/orq-ai/orqi) is the orq helper agent for the terminal, with the orq tools and skills already wired in.

    ```bash
    curl -fsSL https://raw.githubusercontent.com/orq-ai/orqi/main/install.sh | sh
    set -a; source .env; set +a     # export your workshop key into this shell
    orqi "which models are enabled in my workspace?"
    ```

    orqi does not read `.env` by itself: the `set -a` line exports the key for this shell only. Its header line ends with the credential it used; it must say `ORQ_API_KEY`.

=== "Claude Code"

    ```bash
    claude plugin marketplace add orq-ai/assistant-plugins
    claude plugin install orq-skills@orq-claude-plugin
    ```

    The plugin brings the skills, the MCP server and slash commands such as `/orq:traces`.

=== "Other agents"

    ```bash
    npx skills add orq-ai/assistant-plugins
    ```

    Then add the MCP server `https://my.orq.ai/v2/mcp` (HTTP transport) in your agent's MCP settings. It signs you in with OAuth on first use.

!!! warning "One MCP path only"
    Install the MCP server through the plugin **or** by hand, not both, or it registers twice and every tool shows up double.

### Step 2 · Check which workspace it sees

Ask your agent:

```text
Which orq workspace are you connected to? List the chat models enabled there.
```

The answer must name the workshop workspace and the same models you saw in the Model Garden. OAuth signs in as *you*, and your kickstart key is not a workspace membership: an agent connected over OAuth may land in your own workspace instead of the workshop one. If it does, connect the MCP server with your workshop key instead. For Claude Code:

```bash
set -a; source .env; set +a
claude mcp add --transport http orq https://my.orq.ai/v2/mcp --header "Authorization: Bearer ${ORQ_API_KEY}"
```

OAuth is the right path for your own workspace after today.

### Step 3 · Keep it open

The simulation and fix-and-eval modules each end with an **Ask your assistant** box: questions to hand to this agent once you have results.

## Official docs

- [Orq MCP server](https://docs.orq.ai/ai-studio/integrations/code-assistants/orq-mcp): tools on your workspace for any MCP client, OAuth or bearer key
- [Orq Skills](https://docs.orq.ai/ai-studio/integrations/code-assistants/orq-skills): the workflows, and the Claude Code plugin
- [Automate evals and observability in Claude Code](https://docs.orq.ai/ai-studio/cookbooks/evaluation-safety/automate-evals-and-observability-with-claude-code): a worked example
- [orq CLI](https://docs.orq.ai/reference/cli)

## Done when

Your coding agent (or orqi) names the workshop workspace and its models.
