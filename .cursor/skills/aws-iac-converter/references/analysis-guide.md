# IaC Analysis & Detection Guide

Reference for identifying AWS IaC types in a source code repository.

## Detection Rules

### CloudFormation

**File patterns:**
- `*.yaml`, `*.yml`, `*.json` with CloudFormation structure

**Identifiers (must contain at least one):**
- Top-level key `AWSTemplateFormatVersion`
- Top-level key `Resources` with resource entries using `Type: AWS::*`
- Top-level key `Transform` (e.g., `AWS::Serverless-2016-10-31`)
- Nested stack references (`AWS::CloudFormation::Stack`)

**Common file names:**
- `template.yaml`, `template.json`
- `cloudformation.yaml`, `cfn-template.yaml`
- `*.cfn.yaml`, `*.cfn.json`
- `samconfig.toml` (indicates SAM / CloudFormation)

**Key sections to analyze:**
- `Parameters` — input parameters
- `Resources` — AWS resource definitions
- `Outputs` — exported values
- `Mappings` — lookup tables
- `Conditions` — conditional resource creation
- `Metadata` — stack metadata

### CDK (TypeScript / Python)

**File patterns:**
- `cdk.json` in the project root (strongest signal)
- `*.ts`, `*.py` files importing CDK constructs

**Identifiers:**
- `cdk.json` file with `app` field
- TypeScript imports: `aws-cdk-lib`, `@aws-cdk/*`, `constructs`
- Python imports: `aws_cdk`, `constructs`
- Classes extending `Stack`, `Construct`, `NestedStack`
- `cdk.out/` directory (synthesized output)

**Common file names:**
- `bin/*.ts` or `app.py` — CDK app entry point
- `lib/*.ts` or `*_stack.py` — stack definitions
- `cdk.json` — CDK configuration

**Key elements to analyze:**
- Stack classes and their construct trees
- L1 (`Cfn*`), L2, and L3 constructs used
- Cross-stack references
- Context values and environment configuration
- Custom constructs and patterns

### Terraform

**File patterns:**
- `*.tf` files (HCL syntax)
- `*.tf.json` files (JSON syntax)

**Identifiers:**
- `terraform {}` block with `required_providers`
- `provider "aws" {}` block
- `resource "aws_*"` blocks
- `data "aws_*"` blocks
- `.terraform/` directory or `.terraform.lock.hcl`

**Common file names:**
- `main.tf` — primary resource definitions
- `variables.tf` — input variables
- `outputs.tf` — output values
- `providers.tf` or `versions.tf` — provider configuration
- `backend.tf` — state backend configuration
- `terraform.tfvars`, `*.auto.tfvars` — variable values

**Key elements to analyze:**
- Resource blocks and their types
- Module usage (local and remote)
- Data sources
- Variable definitions and defaults
- Output definitions
- Backend configuration
- Provider version constraints

## Mixed IaC Detection

A repository may contain **multiple IaC types**. Common scenarios:

| Scenario                    | Example                                              |
| --------------------------- | ---------------------------------------------------- |
| CDK + CloudFormation        | CDK project with raw CloudFormation custom resources  |
| Terraform + CloudFormation  | Terraform for infra, CloudFormation for specific stacks |
| Multiple Terraform roots    | Separate Terraform configs for different environments |

When multiple types are detected:
1. List all detected types with their file locations
2. Ask the user which source type to convert (or convert all)
3. Handle each conversion independently

## Resource Inventory

When analyzing, build an inventory of:

| Field               | Description                                              |
| ------------------- | -------------------------------------------------------- |
| **Resource Type**   | AWS service (e.g., `AWS::Lambda::Function`, `aws_lambda_function`) |
| **Logical Name**    | Name/identifier in the IaC code                         |
| **Properties**      | Key configuration properties                             |
| **Dependencies**    | Other resources this depends on                          |
| **File Location**   | File path and line number                                |

This inventory feeds directly into the conversion plan (Phase 4).
