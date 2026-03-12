# Awesome Cursor Skills

A curated collection of awesome Cursor rules, agents, skills, commands, and templates to enhance your development workflow with Cursor AI.

## 📚 What's Inside

This repository contains templates and examples for:

- **Rules** - Persistent AI guidance for your codebase
- **Subagents** - Specialized AI assistants for specific tasks
- **Skills** - Reusable agent capabilities with scripts and assets
- **Commands** - Quick workflows and repeatable tasks

## 🚀 Quick Start

### Using Templates

Browse the [templates directory](./docs/templates/) to find ready-to-use templates for:

- **[Rules Template](./docs/templates/rules.md)** - Create project-specific or global rules
- **[Subagents Template](./docs/templates/subagents.md)** - Build specialized AI assistants
- **[Skills Template](./docs/templates/skills.md)** - Develop reusable agent capabilities
- **[Commands Template](./docs/templates/commands.md)** - Define quick workflows

### Installation

1. **Clone this repository:**

   ```bash
   git clone https://github.com/yourusername/awesome-cursor-skills.git
   ```

2. **Copy templates to your project:**

   ```bash
   # Copy rules template
   cp docs/templates/rules.md .cursor/rules/my-rule.md

   # Copy subagents template
   cp docs/templates/subagents.md .cursor/agents/my-subagent.md

   # Copy skills template
   mkdir -p .cursor/skills/my-skill
   cp docs/templates/skills.md .cursor/skills/my-skill/SKILL.md

   # Copy commands template
   cp docs/templates/commands.md .cursor/commands/my-command.md
   ```

3. **Customize the templates** for your specific needs

## 📖 Resource Types

### Rules

Rules provide persistent AI guidance that helps Cursor understand your project's conventions, patterns, and best practices.

**Location:**

- Project rules: `.cursor/rules/`
- User rules: `Cursor Settings → Rules`
- Team rules: Cursor Dashboard (Team/Enterprise plans)

**Features:**

- Always apply or apply intelligently based on context
- File-specific rules using glob patterns
- Reference files using `@filename` syntax
- Support for frontmatter configuration

**Learn more:** [Rules Template](./docs/templates/rules.md)

### Subagents

Subagents are specialized AI assistants that handle specific tasks or domains. They can be automatically invoked by the main agent or called explicitly.

**Location:**

- Project subagents: `.cursor/agents/`
- User subagents: `~/.cursor/agents/`

**Features:**

- Automatic delegation based on task complexity
- Explicit invocation with `/subagent-name`
- Parallel execution for multiple tasks
- Configurable model selection (fast, inherit, or specific model)

**Learn more:** [Subagents Template](./docs/templates/subagents.md)

### Skills

Skills extend agent capabilities with reusable instructions, scripts, and assets. They follow an open standard and can be shared across different AI agents.

**Location:**

- Project skills: `.cursor/skills/`
- User skills: `~/.cursor/skills/`

**Features:**

- Automatic or manual invocation
- Include executable scripts
- Reference documentation and assets
- Open standard (portable across agents)
- Version control friendly

**Learn more:** [Skills Template](./docs/templates/skills.md)

### Commands

Commands are quick workflows and repeatable tasks that can be triggered with a slash prefix.

**Location:**

- Project commands: `.cursor/commands/`
- Global commands: `~/.cursor/commands/`
- Team commands: Cursor Dashboard (Team/Enterprise plans)

**Features:**

- Simple markdown format
- Parameter support
- Checklists and structured workflows
- Easy to share and version control

**Learn more:** [Commands Template](./docs/templates/commands.md)

## 🎯 Use Cases

### For Individual Developers

- Create project-specific rules to enforce coding standards
- Build custom commands for repetitive workflows
- Develop skills for domain-specific tasks
- Set up subagents for specialized code reviews or debugging

### For Teams

- Share rules and commands via version control
- Use team commands for standardized workflows
- Create shared skills for common development tasks
- Establish consistent patterns across the codebase

### For Open Source Projects

- Document project conventions with rules
- Provide contributor-friendly commands
- Share reusable skills with the community
- Create onboarding subagents for new contributors

## 📁 Repository Structure

```
awesome-cursor-skills/
├── .cursor/
│   ├── agents/               # Example subagents
│   │   ├── architecture-diagram-generator.md  # Architecture diagram generator (Mermaid, codebase analysis)
│   │   ├── aws-diagram-generator.md  # AWS architecture diagrams via MCP (Python DSL or YAML Diagram-as-Code)
│   │   ├── changelog-generator.md   # Automated changelog creator
│   │   ├── debugger.md       # Debugging assistant
│   │   ├── github-actions-validator.md  # GitHub Actions workflow validator
│   │   ├── iac-validator.md  # Infrastructure as Code validator
│   │   ├── implementer.md    # Implements code from a plan for a given tech stack (used by orchestrator)
│   │   ├── orchestrator.md   # Coordinates planner → implementers (parallel) → verifier
│   │   ├── planner.md        # Technical planner; produces structured plan for implementers
│   │   ├── security-auditor.md  # Security review agent
│   │   ├── terraform-module-version-updater.md  # Updates Terraform module versions from user-provided map
│   │   ├── test-runner.md    # Test execution agent
│   │   └── verifier.md       # Work verification agent (plan/acceptance criteria check)
│   ├── rules/                # Project rules (coding standards, conventions)
│   │   ├── python-standards.mdc   # Python coding standards for AWS development
│   │   └── terraform-standards.mdc  # Terraform coding standards
│   ├── commands/             # Example commands
│   │   ├── code-review-checklist.md
│   │   ├── create-pr.md
│   │   ├── onboard-new-developer.md
│   │   ├── run-all-tests-and-fix.md
│   │   ├── security-audit.md
│   │   └── setup-new-feature.md
│   └── skills/               # Example skills
│       ├── aws-mcp-setup/    # AWS MCP server configuration skill
│       │   └── SKILL.md
│       ├── aws-cdk-development/  # AWS CDK development skill
│       │   ├── SKILL.md
│       │   ├── references/
│       │   │   └── cdk-patterns.md
│       │   └── scripts/
│       │       └── validate-stack.sh
│       ├── aws-agentcore/    # AWS Bedrock AgentCore comprehensive expert
│       │   ├── SKILL.md
│       │   └── references/
│       │       ├── browser.md
│       │       ├── code-interpreter.md
│       │       ├── credential-management.md
│       │       ├── gateway-deployment.md
│       │       ├── gateway-troubleshooting.md
│       │       ├── gateway.md
│       │       ├── identity.md
│       │       ├── memory.md
│       │       ├── observability.md
│       │       └── runtime.md
│       ├── aws-agentcore-agent-workflow/  # Complete workflow for creating AI agents
│       │   ├── SKILL.md
│       │   └── references/
│       │       ├── common-configurations.md
│       │       ├── optional-services.md
│       │       ├── testing.md
│       │       └── troubleshooting.md
│       ├── aws-iac-converter/    # Convert AWS IaC between CloudFormation, CDK, Terraform
│       │   ├── SKILL.md
│       │   ├── references/
│       │   │   ├── analysis-guide.md
│       │   │   ├── conversion-patterns.md
│       │   │   ├── report-template.md
│       │   │   └── verification-checklist.md
│       │   └── scripts/
│       │       ├── analyze-repo.sh
│       │       └── validate-conversion.sh
│       ├── jira-epic-generation/  # Generate JIRA issues from requirements docs
│       │   └── SKILL.md
│       └── jira-ticket-technical-design-workflow/  # JIRA ticket → TDD in docs/jira/<KEY>/; update JIRA (Atlassian MCP)
│           ├── SKILL.md
│           └── references/
│               ├── jira-update.md
│               ├── jql-and-paths.md
│               ├── mermaid-diagram.md
│               └── technical-design-template.md
├── docs/
│   └── templates/
│       ├── rules.md          # Rules template
│       ├── subagents.md      # Subagents template
│       ├── skills.md         # Skills template
│       └── commands.md       # Commands template
└── README.md                 # This file
```

## 🤝 Contributing

Contributions are welcome! Whether you have:

- New templates or examples
- Improvements to existing templates
- Documentation enhancements
- Use case examples

Please feel free to submit a pull request or open an issue.

### Contribution Guidelines

1. Follow the existing template structure
2. Include clear examples and use cases
3. Document any dependencies or requirements
4. Test your contributions before submitting

## 📝 License

This repository is open source. Please check individual resource licenses if applicable.

## 🔗 Resources

- [Cursor Documentation](https://docs.cursor.com)
- [Agent Skills Standard](https://agentskills.io)
- [Cursor Community](https://cursor.com/community)

## ⭐ Show Your Support

If you find this repository helpful, please consider giving it a star!

---

**Note:** This repository contains templates and examples. Customize them to fit your specific needs and project requirements.
