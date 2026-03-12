---
name: aws-iac-converter
description: Convert AWS Infrastructure as Code between CloudFormation, CDK (TypeScript/Python), and Terraform. Use when converting IaC code from one format to another, migrating infrastructure definitions, or when the user mentions IaC conversion, CloudFormation to Terraform, CDK to CloudFormation, Terraform to CDK, or any AWS IaC migration.
skills:
  - aws-mcp-setup
allowed-tools:
  - mcp__awslabs.aws-iac-mcp-server__*
  - mcp__awslabs.terraform-mcp-server__*
  - mcp__aws-mcp__*
  - mcp__awsdocs__*
  - Bash(git *)
  - Bash(terraform *)
  - Bash(cdk *)
  - Bash(aws cloudformation *)
  - Bash(npm *)
  - Bash(npx *)
  - Bash(pip *)
  - Bash(python *)
---

# AWS IaC Converter

Convert AWS Infrastructure as Code between CloudFormation, CDK (TypeScript/Python), and Terraform with a structured, interactive workflow.

## When to Use

Use when the user wants to convert or migrate AWS IaC between CloudFormation, CDK, or Terraform (see description).

## Supported Conversions

| Source            | Target Options                           |
| ----------------- | ---------------------------------------- |
| **CloudFormation** | CDK (TypeScript/Python), Terraform       |
| **CDK**            | CloudFormation, Terraform                |
| **Terraform**      | CloudFormation, CDK (TypeScript/Python)  |

## MCP Server Integration

This skill leverages MCP servers for accurate, up-to-date conversions:

| Server                              | Purpose                                                      |
| ----------------------------------- | ------------------------------------------------------------ |
| **AWS IaC MCP Server**              | CloudFormation validation, CDK docs, compliance checking     |
| **Terraform MCP Server**            | Terraform validation, security scanning, provider docs       |
| **AWS Documentation MCP**           | Service feature verification, API reference                  |

### Before Converting

1. **Always verify** resource properties using MCP tools to ensure accurate mapping
2. If MCP tools are unavailable, guide user to configure them via the `aws-mcp-setup` skill (auto-loaded as dependency)

### Why this skill keeps its own planning and verification

The [orchestrator](.cursor/agents/orchestrator.md) has a **planner** and a **verifier**, but they are generic (technical plans; “does work match plan?”). This skill keeps **conversion-specific** steps:

- **Planning (Phases 1–4)** — Repo analysis, IaC detection, target selection, and the **conversion plan** (resource mapping, target output path, conversion patterns, parameters→variables) are IaC-conversion concerns. The orchestrator’s planner does not produce conversion plans. The skill produces the plan and then hands it to the orchestrator; the orchestrator **skips its planner** and runs only the **implementer**.
- **Verification & reporting (Phases 6–7)** — Running `validate-conversion.sh`, the “resolve lint / security report-only” policy, and generating `CONVERSION-REPORT.md` (source-to-target mapping, security findings) are conversion-specific. The orchestrator’s verifier does not run these. After the implementer completes, **this skill** runs Phase 6–7.

So: **only implementation (Phase 5)** is delegated to the orchestrator’s implementer. Planning and verification stay in the skill.

## Workflow

### Phase 1: Repository Input

1. **Ask the user** for the source code repository URL.
   - **Do NOT proceed** until the user provides the URL.
   - Accept: GitHub URL, GitLab URL, Bitbucket URL, or local path.
2. If the URL is a remote repository, clone it into a temporary working directory.
3. If the URL is a local path, confirm it exists and is accessible.

### Phase 2: Analysis & Detection

4. **Analyze the repository** to identify all AWS IaC code. Run the analysis script:

   ```bash
   bash .cursor/skills/aws-iac-converter/scripts/analyze-repo.sh <repo-path>
   ```

5. **Identify the IaC type(s)** found. Detection rules: [references/analysis-guide.md](references/analysis-guide.md).
6. **Present findings** to the user:
   - IaC type detected (CloudFormation, CDK, Terraform, or mixed)
   - Files and directories containing IaC code
   - AWS resources identified
   - Any non-IaC code detected (application code, CI/CD, etc.)

### Phase 3: Target Selection

7. **Ask the user** for the target IaC type.
   - **Do NOT proceed** until the user provides the target type.
   - The target type **must be different** from the source type.
   - If CDK is selected, ask for the language preference (TypeScript or Python).
   - Validate the selection and confirm with the user.

### Phase 4: Conversion Planning

8. **Create a detailed conversion plan** covering:
   - **Target output path** — Directory where converted code will be written (e.g. `<workspace>/converted-terraform`). Required so the orchestrator’s implementer and Phase 6/7 use the same path.
   - Resource-by-resource mapping from source to target
   - Parameter/variable conversion strategy
   - Output/export handling
   - State management considerations (especially for Terraform)
   - Dependencies and ordering
   - Resources that **cannot** be directly converted (with workarounds)
   - Conversion patterns used: [references/conversion-patterns.md](references/conversion-patterns.md)

9. **Present the plan** to the user for review.
   - Show a summary table of resources and their conversion status
   - Highlight any risks, limitations, or manual steps required
   - **Do NOT proceed** until the user approves the plan.
   - Incorporate any user feedback into the plan before proceeding.

### Phase 5: Implementation

10. **Delegate implementation to the orchestrator agent** — Do not implement in-place. Invoke the [orchestrator agent](.cursor/agents/orchestrator.md) with:
    - **Input**: The **approved conversion plan** (from Phase 4), including the **target output path**; the **target IaC stack/scope** (e.g. Terraform, CDK TypeScript, CloudFormation); and the **source repo path**.
    - **Orchestrator**: Skip the orchestrator’s planner. Have the orchestrator run its **implementer** subagent(s) for the target IaC stack. Implementer writes converted code to the **target output path** from the plan, using [references/conversion-patterns.md](references/conversion-patterns.md) and MCP for property mappings, and generates dependency files (`package.json`, `requirements.txt`, `versions.tf`, etc.).
    - **Resume**: After the implementer(s) complete, **resume this skill** with the **target output path** (from the plan) and run Phase 6 (Verification) and Phase 7 (Reporting).

### Phase 6: Verification

11. **Verify** the converted code at the **target output path** (from the plan; where the orchestrator’s implementer wrote output). Run:

    ```bash
    bash .cursor/skills/aws-iac-converter/scripts/validate-conversion.sh <target-path> <target-type>
    ```
    Use `<target-path>` = target output path from the conversion plan.

12. **Resolve** all lint/validation failures (syntax, structure, formatting, cfn-lint, terraform validate/fmt, cdk synth/build). **Do not resolve** security-specific findings (Checkov, cfn-guard, etc.) — run those scans and **record results for the report only** (may be intentional from source). See [references/verification-checklist.md](references/verification-checklist.md).

### Phase 7: Reporting

13. **Generate a conversion report** at `<target-output-path>/CONVERSION-REPORT.md` (same path used in Phase 6).
    - Report template: [references/report-template.md](references/report-template.md)
    - Include:
      - Source-to-target resource mapping table
      - Successfully converted resources
      - Partially converted resources (with manual steps needed)
      - Resources that could not be converted (with reasons)
      - Validation results (syntax, structure)
      - Security scan findings (report only; do not mark as issues to fix)
      - Recommendations and next steps

14. **Summarize to the user**:
    - Total resources converted vs. total in source
    - Any resources requiring manual attention
    - Location of converted code and report
    - Suggested next steps (testing, deployment, etc.)

## Output Layout

The **target output path** (agreed in the conversion plan) is where the orchestrator’s implementer writes converted code. After Phase 6–7 it will contain:

```
<target-output-path>/
├── <converted IaC files>         # Written by orchestrator's implementer
├── <dependency files>            # package.json, requirements.txt, versions.tf, etc.
├── README.md                     # Generated README for the converted project
└── CONVERSION-REPORT.md         # Added by this skill in Phase 7
```

## Key Principles

- Wait for user input at checkpoints (repo URL, target type, plan approval). Do not proceed until provided.
- Implementation is **only** via the orchestrator’s implementer; this skill owns planning (Phases 1–4), handoff (Phase 5), verification (Phase 6), and reporting (Phase 7).
- The conversion plan must include a **target output path** so the implementer and this skill use the same directory for output and verification.
- Resolve lint/validation in Phase 6; record security findings only. Generate a conversion report that maps every source resource to target (or documents unconvertible ones).

**References:** [analysis-guide](references/analysis-guide.md) · [conversion-patterns](references/conversion-patterns.md) · [report-template](references/report-template.md) · [verification-checklist](references/verification-checklist.md)
