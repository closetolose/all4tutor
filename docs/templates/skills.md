---
name: my-skill
description: Short description of what this skill does and when to use it.
license: MIT
compatibility: Requires Node.js 18+ and network access
metadata:
  version: 1.0.0
  author: Your Name
disable-model-invocation: false
---

# My Skill

Detailed instructions for the agent on how to use this skill.

## When to Use

- Use this skill when...
- This skill is helpful for...
- Invoke this skill for...

## Instructions

- Step-by-step guidance for the agent
- Domain-specific conventions
- Best practices and patterns
- Use the ask questions tool if you need to clarify requirements with the user

## Examples

Example usage scenarios or code snippets that demonstrate the skill.

---

## Template Notes

### Skill Directory Structure

Each skill should be a folder containing a `SKILL.md` file:

```text
.cursor/
└── skills/
    └── my-skill/
        └── SKILL.md
```

Skills can also include optional directories:

```text
.cursor/
└── skills/
    └── deploy-app/
        ├── SKILL.md
        ├── scripts/
        │   ├── deploy.sh
        │   └── validate.py
        ├── references/
        │   └── REFERENCE.md
        └── assets/
            └── config-template.json
```

### Skill Locations

Skills are automatically loaded from these locations:

| Location | Scope |
|----------|-------|
| `.cursor/skills/` | Project-level |
| `.claude/skills/` | Project-level (Claude compatibility) |
| `.codex/skills/` | Project-level (Codex compatibility) |
| `~/.cursor/skills/` | User-level (global) |
| `~/.claude/skills/` | User-level (global, Claude compatibility) |
| `~/.codex/skills/` | User-level (global, Codex compatibility) |

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Skill identifier. Lowercase letters, numbers, and hyphens only. Must match the parent folder name. |
| `description` | Yes | Describes what the skill does and when to use it. Used by the agent to determine relevance. |
| `license` | No | License name or reference to a bundled license file. |
| `compatibility` | No | Environment requirements (system packages, network access, etc.). |
| `metadata` | No | Arbitrary key-value mapping for additional metadata. |
| `disable-model-invocation` | No | When `true`, the skill is only included when explicitly invoked via `/skill-name`. The agent will not automatically apply it based on context. |

### Disabling Automatic Invocation

By default, skills are automatically applied when the agent determines they are relevant. Set `disable-model-invocation: true` to make a skill behave like a traditional slash command, where it is only included in context when you explicitly type `/skill-name` in chat.

### Optional Directories

| Directory | Purpose |
|-----------|---------|
| `scripts/` | Executable code that agents can run |
| `references/` | Additional documentation loaded on demand |
| `assets/` | Static resources like templates, images, or data files |

Keep your main `SKILL.md` focused and move detailed reference material to separate files. This keeps context usage efficient since agents load resources progressively—only when needed.

### Example Skills

#### Skill with Scripts

```markdown
---
name: deploy-app
description: Deploy the application to staging or production environments. Use when deploying code or when the user mentions deployment, releases, or environments.
---

# Deploy App

Deploy the application using the provided scripts.

## Usage

Run the deployment script: `scripts/deploy.sh <environment>`

Where `<environment>` is either `staging` or `production`.

## Pre-deployment Validation

Before deploying, run the validation script: `python scripts/validate.py`

## Steps

1. Validate the codebase using the validation script
2. Run the deployment script with the target environment
3. Verify deployment success
4. Check application health endpoints
```

#### Skill with References

```markdown
---
name: api-documentation
description: Generate API documentation from code comments. Use when creating or updating API docs.
---

# API Documentation

Generate comprehensive API documentation from code comments and annotations.

## When to Use

- Creating new API documentation
- Updating existing documentation
- Reviewing API endpoints

## Instructions

1. Scan the codebase for API endpoints
2. Extract code comments and annotations
3. Generate markdown documentation
4. Reference `references/API_STANDARDS.md` for formatting guidelines

## Reference Material

See `references/API_STANDARDS.md` for detailed formatting and style guidelines.
```

#### Skill with Assets

```markdown
---
name: create-component
description: Create a new React component following project standards. Use when creating new UI components.
---

# Create Component

Create a new React component following project conventions and standards.

## When to Use

- Creating new React components
- Setting up component structure
- Initializing component files

## Instructions

1. Use the template from `assets/component-template.tsx`
2. Follow naming conventions (PascalCase for components)
3. Include TypeScript types for props
4. Add component to the appropriate directory structure

## Template

Reference `assets/component-template.tsx` for the standard component structure.
```

#### Manual Invocation Only

```markdown
---
name: generate-changelog
description: Generate a changelog from git commits. Use when preparing releases.
disable-model-invocation: true
---

# Generate Changelog

Generate a changelog from git commit history.

## Usage

Invoke this skill explicitly with `/generate-changelog` when you need to create a changelog.

## Instructions

1. Analyze git commit history since last release
2. Categorize commits by type (feat, fix, docs, etc.)
3. Format according to Keep a Changelog standards
4. Write to CHANGELOG.md
```

### Best Practices

✅ **Do:**
- Write clear, focused descriptions that help the agent determine when to use the skill
- Keep `SKILL.md` concise and move detailed information to `references/`
- Make scripts self-contained with helpful error messages
- Use descriptive skill names (lowercase, hyphens)
- Include examples in your skill documentation
- Test skills to ensure they work as expected
- Version control skills in your repository
- Document compatibility requirements

❌ **Don't:**
- Create overly broad skills that try to do too much
- Include large files directly in `SKILL.md` (use `references/` or `assets/`)
- Write vague descriptions that don't help the agent decide relevance
- Create skills that duplicate built-in agent capabilities
- Forget to handle errors in scripts gracefully
- Use spaces or special characters in skill names

### Script Guidelines

When including scripts in skills:

- **Self-contained**: Scripts should include all necessary logic
- **Error handling**: Include helpful error messages
- **Edge cases**: Handle edge cases gracefully
- **Documentation**: Comment complex logic
- **Portability**: Consider cross-platform compatibility

Example script structure:
```bash
#!/bin/bash
# deploy.sh - Deploy application to specified environment

set -e  # Exit on error

ENVIRONMENT=$1

if [ -z "$ENVIRONMENT" ]; then
    echo "Error: Environment must be specified (staging or production)"
    exit 1
fi

# Deployment logic here
echo "Deploying to $ENVIRONMENT..."
```

### Viewing Skills

To view discovered skills:

1. Open **Cursor Settings** (Cmd+Shift+J on Mac, Ctrl+Shift+J on Windows/Linux)
2. Navigate to **Rules**
3. Skills appear in the **Agent Decides** section

### Installing Skills from GitHub

You can import skills from GitHub repositories:

1. Open **Cursor Settings → Rules**
2. In the **Project Rules** section, click **Add Rule**
3. Select **Remote Rule (Github)**
4. Enter the GitHub repository URL

### Migrating Rules and Commands to Skills

Cursor includes a built-in `/migrate-to-skills` skill that helps you convert:

- **Dynamic rules**: Rules with `alwaysApply: false` (or undefined) and no `globs` patterns
- **Slash commands**: Both user-level and workspace-level commands

To migrate:

1. Type `/migrate-to-skills` in Agent chat
2. The agent will identify eligible rules and commands
3. Review the generated skills in `.cursor/skills/`

**Note**: Rules with `alwaysApply: true` or specific `globs` patterns are not migrated, as they have explicit triggering conditions that differ from skill behavior.

### Skill vs Rules vs Commands vs Subagents

| Feature | Skills | Rules | Commands | Subagents |
|---------|--------|-------|----------|-----------|
| **Purpose** | Extend agent capabilities | Persistent instructions | Quick workflows | Specialized AI assistants |
| **Invocation** | Automatic or manual (`/skill-name`) | Automatic (based on type) | Manual (`/command-name`) | Automatic or manual (`/subagent-name`) |
| **Context** | Project or user-level | Project, user, or team | Project or user-level | Project or user-level |
| **Scripts** | ✅ Can include scripts | ❌ No scripts | ❌ No scripts | ❌ No scripts |
| **Portability** | ✅ Open standard | ❌ Cursor-specific | ❌ Cursor-specific | ❌ Cursor-specific |
| **Version Control** | ✅ File-based | ✅ File-based | ✅ File-based | ✅ File-based |

### Tips

- **Start simple**: Create skills for specific, well-defined tasks
- **Iterate**: Refine skills based on actual usage
- **Share**: Skills are portable across any agent supporting the standard
- **Document**: Clear descriptions help the agent use skills effectively
- **Organize**: Use optional directories to keep `SKILL.md` focused
- **Test**: Verify skills work as expected before sharing

### Learn More

Agent Skills is an open standard. Learn more at [agentskills.io](https://agentskills.io).
