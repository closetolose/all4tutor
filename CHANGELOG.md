# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### ✨ New Features

- **AWS Diagram Generator Agent**: Added `aws-diagram-generator` agent for AWS architecture diagrams using MCP servers. Supports Python diagrams package DSL and YAML-based Diagram-as-Code (e.g. `user-awsdac-mcp-server`). Generates PNG diagrams with proper AWS resource relationships, grouping, and best practices for complex architectures.
- **Terraform Module Version Updater Agent**: Added `terraform-module-version-updater` agent that discovers Terraform files in the repo and updates module versions from a user-provided module→version map (file or inline). Targets `app.terraform.io/sseplc/<module>/aws` sources; changes only the `version` attribute and reports changes and unscanned modules.
- **AWS IaC Converter Skill**: Added `aws-iac-converter` skill to convert AWS Infrastructure as Code between CloudFormation, CDK (TypeScript/Python), and Terraform. Seven-phase workflow: repo input → analysis & detection → target selection → conversion planning → implementation (via orchestrator) → verification → reporting. Uses AWS IaC MCP, Terraform MCP, and AWS Documentation MCP; includes analysis script, validation script, and conversion report template.

### 🔧 Improvements

- **Implementer Agent**: Set model to `claude-4.6-opus-high-thinking` for implementation tasks. Added "Analyze codebase" and "Plan directory structure" steps before applying standards and implementing. Ensures new code aligns with existing layout and reduces conflicts.
- **JIRA TDD Skill (Mermaid)**: Documented that line breaks inside Mermaid node labels should use `<br/>` (not `\n`) for correct rendering in markdown and diagram renderers.
- **Terraform Standards Rule**: Simplified code structure guidance (main config, variables, outputs). Removed dedicated Modules section; documentation scope is configurations only.

## [1.0.0] - 2026-01-30

### ✨ New Features

- **Orchestrator, Planner, and Implementer Agents**: Added orchestrated delivery flow: **planner** (analyzes requirements, produces technical plan) → **implementer** (one per tech stack, parallel) → **verifier**. Orchestrator coordinates the flow, prompts for clarifications, and uses MCP/skills/rules. Implementer updates `.gitignore` per stack and reports blockers.
- **JIRA Ticket to Technical Design Workflow Skill**: Added `jira-ticket-technical-design-workflow` skill: fetch open JIRA tickets via Atlassian MCP → user picks one → generate TDD with inline Mermaid in `docs/jira/<KEY>/technical-design.md` → update JIRA (comment with design summary, transition to In Progress, assign). Includes references for JQL, Mermaid conventions, and JIRA update template.

### 🔧 Improvements

- **Verifier Agent**: Updated description and steps for use by the orchestrator; verifier now compares implementation to the technical plan and acceptance criteria and reports mismatches.

- **Project Rules (Terraform & Python Standards)**: Added `.cursor/rules/` with agent-requestable rules: `terraform-standards.mdc` for Terraform/IaC best practices (structure, variables, modules, state) and `python-standards.mdc` for Python on AWS (Lambda, API Gateway, boto3, serverless patterns).
- **Architecture Diagram Generator Agent**: Replaced AWS-specific diagram agent with a generic architecture diagram generator that analyzes the codebase and produces Mermaid diagrams. Supports multiple views (by layer, domain, deployment, data flow, package/module), overview + focused diagrams, and placement in existing design docs or new `docs/architecture.md`.
- **GitHub Actions Validator Subagent**: Added comprehensive GitHub Actions workflow validation subagent that validates workflow structure, checks reusable actions for latest versions, and verifies runtime/utility versions (Python, Node.js, Terraform, etc.). Automatically fixes outdated versions and structural issues. Supports MCP server integration (Context7) and web search fallback for version checking. Runs in background with parallel processing support.
- **AWS AgentCore Agent Workflow Skill**: Added comprehensive workflow skill for creating complete AI agents on AWS Bedrock using AgentCore services. Provides step-by-step guidance for Runtime creation, agent configuration, and optional service enhancements (Memory, Gateway, Code Interpreter, Browser, Observability). Uses MCP servers exclusively for all operations.
- **AWS AgentCore Skill**: Added comprehensive AWS Bedrock AgentCore skill for deploying and managing all AgentCore services including Gateway, Runtime, Memory, Identity, Code Interpreter, Browser, and Observability. Includes detailed documentation and reference guides for each service.
- **JIRA Epic Generation Skill**: Added `jira-epic-generation` skill to generate epics, stories, and tasks from a requirements document (PRD/BRD/SRS) and create them in JIRA via Atlassian MCP.

### 🔧 Improvements

- **JIRA Epic Generation Skill**: Enhanced with Atlassian MCP workflow details, explicit steps for getVisibleJiraProjects/getJiraProjectIssueTypesMetadata/createJiraIssue/editJiraIssue, subtask parent linking, and optional directory structure for saving artifacts.
- **AWS MCP Setup Skill**: Enhanced to include setup instructions for AWS Bedrock AgentCore MCP Server and Context7 MCP Server, providing access to AgentCore documentation, management guides, and up-to-date library documentation queries.
- **Agent Skills Best Practices**: Refactored workflow skill to follow Agent Skills best practices with progressive disclosure, concise main file (144 lines), and detailed content in reference files.
- **MCP-First Approach**: Removed all AWS CLI command examples from workflow skill, using MCP servers exclusively for operations.
- **Create PR Command**: Updated the `create-pr` command to include a step for generating changelog entries using the changelog-generator agent, ensuring PRs include proper change documentation.
- **Create PR Command**: Enhanced the `create-pr` command workflow to require explicit target branch confirmation before proceeding, preventing accidental PRs to wrong branches. Updated all step references to use "target branch" instead of hardcoded "main" for better flexibility.

### 🗑️ Removed

- **AWS Diagram Generator Agent**: Removed in favor of the generic architecture-diagram-generator agent (Mermaid-based, codebase-agnostic).
