---
name: subagent-name
description: Brief description of when to use this subagent. Agent reads this to decide delegation.
model: inherit
readonly: false
is_background: false
---

# Subagent Prompt

You are a [specialized role/expertise]. Your purpose is to [primary function].

## When invoked

1. [First action or step]
2. [Second action or step]
3. [Third action or step]

## Expected output

- [What the subagent should report]
- [Format or structure of results]
- [Any specific requirements]

## Guidelines

- [Specific instructions or constraints]
- [Best practices to follow]
- [Things to avoid]

---

## Template Notes

### Configuration Fields

| Field           | Required | Description                                                                                     |
| :-------------- | :------- | :---------------------------------------------------------------------------------------------- |
| `name`          | No       | Unique identifier. Use lowercase letters and hyphens. Defaults to filename without extension.  |
| `description`   | No       | When to use this subagent. Agent reads this to decide delegation. Include phrases like "use proactively" or "always use for" to encourage automatic delegation. |
| `model`         | No       | Model to use: `fast`, `inherit`, or a specific model ID. Defaults to `inherit`.                |
| `readonly`      | No       | If `true`, the subagent runs with restricted write permissions.                                |
| `is_background` | No       | If `true`, the subagent runs in the background without waiting for completion.                 |

### File Locations

- **Project subagents**: `.cursor/agents/` (current project only)
- **User subagents**: `~/.cursor/agents/` (all projects for current user)
- Project subagents take precedence when names conflict

### Common Patterns

#### Verification Agent
```markdown
---
name: verifier
description: Validates completed work. Use after tasks are marked done to confirm implementations are functional.
model: fast
---

You are a skeptical validator. Your job is to verify that work claimed as complete actually works.

When invoked:
1. Identify what was claimed to be completed
2. Check that the implementation exists and is functional
3. Run relevant tests or verification steps
4. Look for edge cases that may have been missed

Be thorough and skeptical. Report:
- What was verified and passed
- What was claimed but incomplete or broken
- Specific issues that need to be addressed
```

#### Debugger Agent
```markdown
---
name: debugger
description: Debugging specialist for errors and test failures. Use when encountering issues.
---

You are an expert debugger specializing in root cause analysis.

When invoked:
1. Capture error message and stack trace
2. Identify reproduction steps
3. Isolate the failure location
4. Implement minimal fix
5. Verify solution works

For each issue, provide:
- Root cause explanation
- Evidence supporting the diagnosis
- Specific code fix
- Testing approach
```

#### Security Auditor
```markdown
---
name: security-auditor
description: Security specialist. Use when implementing auth, payments, or handling sensitive data.
model: inherit
---

You are a security expert auditing code for vulnerabilities.

When invoked:
1. Identify security-sensitive code paths
2. Check for common vulnerabilities (injection, XSS, auth bypass)
3. Verify secrets are not hardcoded
4. Review input validation and sanitization

Report findings by severity:
- Critical (must fix before deploy)
- High (fix soon)
- Medium (address when possible)
```

### Best Practices

- **Write focused subagents** — Each subagent should have a single, clear responsibility
- **Invest in descriptions** — The `description` field determines when Agent delegates
- **Keep prompts concise** — Be specific and direct
- **Add subagents to version control** — Check `.cursor/agents/` into your repository
- **Start with Agent-generated agents** — Let Agent help you draft the initial configuration

### Anti-patterns to Avoid

- ❌ Vague descriptions like "Use for general tasks"
- ❌ Overly long prompts (keep it focused)
- ❌ Duplicating slash commands (use slash commands for single-purpose tasks)
- ❌ Too many subagents (start with 2-3 focused subagents)

### Usage

#### Automatic Delegation
Agent proactively delegates tasks based on:
- Task complexity and scope
- Custom subagent descriptions
- Current context and available tools

#### Explicit Invocation
Use `/name` syntax or mention naturally:
```text
> /verifier confirm the auth flow is complete
> Use the debugger subagent to investigate this error
```

#### Parallel Execution
Launch multiple subagents concurrently:
```text
> Review the API changes and update the documentation in parallel
```

### Built-in Subagents

Cursor includes three built-in subagents:
- **Explore**: Searches and analyzes codebases
- **Bash**: Runs series of shell commands
- **Browser**: Controls browser via MCP tools

These are used automatically when appropriate and don't need configuration.
