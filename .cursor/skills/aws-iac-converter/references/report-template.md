# Conversion Report Template

Use this template to generate `CONVERSION-REPORT.md` after completing a conversion.

---

```markdown
# IaC Conversion Report

**Generated**: <date>
**Source Repository**: <repository-url-or-path>
**Source Type**: <CloudFormation | CDK (TypeScript/Python) | Terraform>
**Target Type**: <CloudFormation | CDK (TypeScript/Python) | Terraform>
**Target Output Path**: <path from conversion plan>
**Implementation**: Performed by orchestrator agent (implementer subagent).

## Summary

| Metric                        | Count |
| ----------------------------- | ----- |
| Total source resources        | X     |
| Successfully converted        | X     |
| Partially converted           | X     |
| Could not be converted        | X     |
| New supporting resources added | X    |

**Conversion rate**: X%

## Source-to-Target Resource Mapping

| # | Source Resource Type | Source Logical Name | Target Resource Type | Target Logical Name | Status | Notes |
|---|---------------------|---------------------|----------------------|---------------------|--------|-------|
| 1 | <source-type>       | <source-name>       | <target-type>        | <target-name>       | OK     |       |
| 2 | <source-type>       | <source-name>       | <target-type>        | <target-name>       | Partial | <reason> |
| 3 | <source-type>       | <source-name>       | N/A                  | N/A                 | Failed | <reason> |

**Status legend:**
- **OK** — Fully converted with all properties mapped
- **Partial** — Converted but some properties require manual review or were approximated
- **Failed** — Could not be converted; manual implementation required

## File Mapping

| Source File              | Target File(s)               |
| ------------------------ | ---------------------------- |
| <source-file-path>       | <target-file-path>           |

## Parameters / Variables Mapping

| Source Parameter  | Target Variable/Prop | Type    | Default | Notes |
| ----------------- | -------------------- | ------- | ------- | ----- |
| <source-param>    | <target-var>         | <type>  | <val>   |       |

## Outputs Mapping

| Source Output  | Target Output | Value Reference | Notes |
| -------------- | ------------- | --------------- | ----- |
| <source-out>   | <target-out>  | <reference>     |       |

## Resources That Could Not Be Converted

List each resource that failed or was skipped:

### <Resource Name>

- **Source type**: <type>
- **Reason**: <why it could not be converted>
- **Workaround**: <suggested manual approach or alternative>

## Validation Results

### Syntax & Linting (Resolved)
- [ ] <validation-tool> — <result>

### Security Scan (Report Only)
- [ ] <scanner> — <result / findings count>
- *Record for awareness only; do not resolve (may be intentional from source).*

### Additional Checks
- [ ] <check-description> — <result>

## Recommendations

1. **<recommendation-title>**: <description>
2. **<recommendation-title>**: <description>

## Next Steps

1. Review all resources marked as **Partial** and verify the conversion
2. Manually implement resources marked as **Failed**
3. Run a full deployment to a test/dev environment
4. Compare the deployed resources against the original infrastructure
5. Update CI/CD pipelines to use the new IaC framework
6. Plan state import if migrating existing infrastructure (Terraform)
7. Remove or archive the original IaC code after validation

## Appendix: Conversion Details

### Assumptions Made

- <assumption-1>
- <assumption-2>

### Known Limitations

- <limitation-1>
- <limitation-2>
```

---

## Report Generation Guidelines

When filling in this template:

1. **Be specific** in the resource mapping — include actual resource types and logical names
2. **Document every resource** — even trivially converted ones, for traceability
3. **Explain failures** with enough detail that a developer can take action
4. **Include validation output** — paste actual command output or summarize findings
5. **Tailor recommendations** to the user's specific context and detected issues
