# Verification Checklist

Post-conversion verification steps by target IaC type.

**Policy:** Resolve all **lint and validation** failures (syntax, structure, formatting). **Security-specific** scans (Checkov, cfn-guard, cdk-nag) — record findings in the conversion report only; do not resolve (may be intentional from source).

## Universal Checks (All Target Types)

### Completeness

- [ ] Every source resource has a corresponding target resource (or is documented as unconvertible)
- [ ] All input parameters/variables are mapped
- [ ] All outputs/exports are mapped
- [ ] Cross-resource dependencies are preserved
- [ ] Tags are carried over to target resources
- [ ] Comments and documentation are preserved where possible

### Semantic Equivalence

- [ ] Resource configurations produce the same infrastructure when deployed
- [ ] Security group rules, IAM policies, and access controls are identical
- [ ] Encryption settings are preserved (KMS keys, SSE, TLS)
- [ ] Networking configuration matches (VPC, subnets, route tables)
- [ ] Resource sizing and capacity settings are unchanged (instance types, storage, throughput)

### Best Practices

- [ ] Target code follows the conventions of the target framework
- [ ] No hardcoded secrets or sensitive values
- [ ] Proper use of variables/parameters for environment-specific values
- [ ] Code formatting follows target framework standards

---

## CloudFormation Target

### Syntax & Structure

- [ ] Template validates: `aws cloudformation validate-template --template-body file://template.yaml`
- [ ] Template is valid YAML/JSON
- [ ] `AWSTemplateFormatVersion` is set
- [ ] All `Ref` and `Fn::GetAtt` references resolve correctly
- [ ] All `Conditions` are properly defined and referenced
- [ ] Nested stacks (if any) have valid `TemplateURL` references

### MCP Validation

- [ ] Run `validate_cloudformation_template` — resolve any errors
- [ ] Run `check_cloudformation_template_compliance` — record for report only (see policy above)

### CloudFormation-Specific

- [ ] Parameter constraints (`AllowedValues`, `MinLength`, etc.) are reasonable
- [ ] `DependsOn` is used only where implicit dependencies are insufficient
- [ ] Outputs have `Export` names if cross-stack references are needed
- [ ] Template size is under 1 MB (51,200 bytes for direct upload)

---

## Terraform Target

### Syntax & Formatting

- [ ] `terraform fmt` produces no changes (code is properly formatted)
- [ ] `terraform validate` passes with no errors
- [ ] `terraform init` succeeds (providers resolve)
- [ ] `terraform plan` runs without errors (may show resource creation)

### MCP Validation

- [ ] Run `ExecuteTerraformCommand` (`validate`) — resolve any errors
- [ ] Run `RunCheckovScan` — record for report only (see policy above)

### Terraform-Specific

- [ ] Provider versions are pinned in `required_providers`
- [ ] Backend configuration is appropriate (local for testing, remote for production)
- [ ] Variables have `description`, `type`, and `validation` where appropriate
- [ ] Outputs have `description` fields
- [ ] No deprecated resource types or arguments
- [ ] `for_each` preferred over `count` for collections
- [ ] Sensitive values use `sensitive = true`
- [ ] Module structure follows standard layout (`main.tf`, `variables.tf`, `outputs.tf`)

---

## CDK Target (TypeScript)

### Build & Synthesis

- [ ] `npm install` / `npm ci` succeeds
- [ ] `npm run build` compiles with no TypeScript errors
- [ ] `cdk synth` produces valid CloudFormation template(s)
- [ ] No circular dependencies between stacks

### MCP Validation

- [ ] Use AWS IaC MCP to search CDK documentation for correct construct usage
- [ ] Validate synthesized template with `validate_cloudformation_template`

### CDK-Specific

- [ ] L2 constructs used where available (prefer over L1 `Cfn*` constructs)
- [ ] Resource names are NOT explicitly set (let CDK generate unique names)
- [ ] Stack props are properly typed with interfaces
- [ ] `cdk.Tags.of()` used for tagging
- [ ] Environment-specific config uses CDK context or stack props, not hardcoded values
- [ ] `cdk-nag` added for synthesis-time validation (recommended)
- [ ] No `any` types in TypeScript code

### CDK Security (cdk-nag)

- [ ] Run cdk-nag if available — record for report only (see policy above)

---

## CDK Target (Python)

### Build & Synthesis

- [ ] Virtual environment created and activated
- [ ] `pip install -r requirements.txt` succeeds
- [ ] `cdk synth` produces valid CloudFormation template(s)
- [ ] No circular dependencies between stacks

### Python-Specific

- [ ] L2 constructs used where available
- [ ] Type hints used for stack props
- [ ] Python naming conventions followed (`snake_case`)
- [ ] `requirements.txt` includes `aws-cdk-lib` and `constructs` with version pins

---

## Verification Strategy

### Recommended Order

1. **Syntax validation & linting** — resolve errors
2. **Security scanning** — run and record for report only (see policy above)
3. **Semantic review** — compare source and target
4. **Plan/synth review** — examine planned changes
5. **Test deployment** — deploy to sandbox and compare

### Comparison Approach

For high-confidence verification:

1. Deploy both source and target to separate test environments
2. Use AWS CLI or Console to compare deployed resources side-by-side
3. Verify key attributes: ARNs, configurations, permissions, networking
4. Run application tests against both environments if applicable
