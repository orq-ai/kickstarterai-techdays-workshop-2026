# Coding agents

!!! abstract "12-Factor Agents · Factor 11: trigger from anywhere"
    The rest of the workshop works from a terminal. It also works from your coding agent: with the orq skills and the orq MCP server, the agent can read your traces, run a simulation or explain a failed eval in the same workspace you are using.

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
    orqi "is my workspace ready for the workshop?"
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
Which orq workspace are you connected to, and does it have an agent called <your WS_PREFIX>-refund-agent?
```

OAuth signs in as *you*, and your kickstart key is not a workspace membership: an agent connected over OAuth may land in your own workspace instead of the workshop one. If it does not find your agent, connect the MCP server with your workshop key instead. For Claude Code:

```bash
set -a; source .env; set +a
claude mcp add --transport http orq https://my.orq.ai/v2/mcp --header "Authorization: Bearer ${ORQ_API_KEY}"
```

OAuth is the right path for your own workspace after today.

### Step 3 · Keep it open

The simulation and fix-and-eval modules each end with an **Ask your assistant** box: questions to hand to this agent once you have results.

## Done when

Your coding agent (or orqi) names your `-refund-agent` and its version.
