---
name: aws-mcp-setup
description: Configure AWS MCP servers including AWS Documentation MCP, AWS IaC MCP Server, Terraform MCP Server, AWS Bedrock AgentCore MCP Server, and Context7 MCP Server. Use when setting up AWS MCP tools, configuring AWS documentation access, CloudFormation/CDK validation, Terraform validation, Bedrock AgentCore documentation, library documentation queries, or when the user mentions AWS MCP, AWS documentation, AWS API queries, IaC validation, infrastructure as code tools, AgentCore, or Context7.
---

# AWS MCP Server Configuration Guide

## Overview

This guide helps you configure AWS MCP tools for AI agents. Six options are available:

| Option                           | Requirements                                  | Capabilities                                                                         |
| -------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------ |
| **Full AWS MCP Server**          | Python 3.10+, uvx, AWS credentials            | Execute AWS API calls + documentation search                                         |
| **AWS Documentation MCP**       | None                                          | Documentation search only                                                            |
| **AWS IaC MCP Server**           | Python 3.10+, uvx, AWS credentials (optional) | CloudFormation validation, CDK docs, compliance checking, deployment troubleshooting |
| **Terraform MCP Server**         | Python 3.10+, uvx, Terraform CLI, Checkov     | Terraform validation, security scanning, AWS provider docs, workflow execution       |
| **Bedrock AgentCore MCP Server** | Python 3.10+, uvx                              | AgentCore documentation search, runtime/memory/gateway management guides             |
| **Context7 MCP Server**          | None                                          | Up-to-date documentation and code examples for any programming library or framework  |

## Step 1: Check Existing Configuration

Before configuring, check if AWS MCP tools are already available using either method:

### Method A: Check Available Tools (Recommended)

Look for these tool name patterns in your agent's available tools:

- `mcp__aws-mcp__*` or `mcp__aws__*` → Full AWS MCP Server configured
- `mcp__*awsdocs*__aws___*` → AWS Documentation MCP configured
- `mcp__*aws-iac*__*` or `mcp__*awslabs.aws-iac-mcp-server*__*` → AWS IaC MCP Server configured
- `mcp__*terraform*__*` or `mcp__*awslabs.terraform-mcp-server*__*` → Terraform MCP Server configured
- `mcp__*bedrock-agentcore*__*` or `mcp__*awslabs.amazon-bedrock-agentcore-mcp-server*__*` → Bedrock AgentCore MCP Server configured
- `mcp__*Context7*__*` or `mcp__*user-Context7*__*` → Context7 MCP Server configured

**How to check**: Use the MCP file system tools to list available MCP servers and their tools.

### Method B: Check Configuration Files

MCP servers use hierarchical configuration (precedence: local → project → user → enterprise):

| Scope      | File Location                   | Use Case               |
| ---------- | ------------------------------- | ---------------------- |
| Local      | `.cursor/mcp.json` (in project) | Personal/experimental  |
| Project    | `.mcp.json` (project root)      | Team-shared            |
| User       | `~/.cursor/mcp.json`            | Cross-project personal |
| Enterprise | System managed directories      | Organization-wide      |

Check these files for `mcpServers` containing `aws-mcp`, `aws`, `awsdocs`, `aws-iac`, `terraform`, `bedrock-agentcore`, or `Context7` keys:

```bash
# Check project config
cat .mcp.json 2>/dev/null | grep -E '"(aws-mcp|aws|awsdocs|aws-iac|terraform|bedrock-agentcore|Context7)"'

# Check user config
cat ~/.cursor/mcp.json 2>/dev/null | grep -E '"(aws-mcp|aws|awsdocs|aws-iac|terraform|bedrock-agentcore|Context7)"'
```

If AWS MCP is already configured, no further setup needed.

## Step 2: Choose Configuration Method

### Automatic Detection

Run these commands to determine which option to use:

```bash
# Check for uvx (requires Python 3.10+)
which uvx || echo "uvx not available"

# Check for valid AWS credentials
aws sts get-caller-identity || echo "AWS credentials not configured"
```

### Option A: Full AWS MCP Server (Recommended)

**Use when**: uvx available AND AWS credentials valid

**Prerequisites**:

- Python 3.10+ with `uv` package manager
- AWS credentials configured (via profile, environment variables, or IAM role)

**Required IAM Permissions**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "aws-mcp:InvokeMCP",
        "aws-mcp:CallReadOnlyTool",
        "aws-mcp:CallReadWriteTool"
      ],
      "Resource": "*"
    }
  ]
}
```

**Configuration** (add to your MCP settings):

```json
{
  "mcpServers": {
    "aws-mcp": {
      "command": "uvx",
      "args": [
        "mcp-proxy-for-aws@latest",
        "https://aws-mcp.us-east-1.api.aws/mcp",
        "--metadata",
        "AWS_REGION=us-west-2"
      ]
    }
  }
}
```

**Credential Configuration Options**:

1. **AWS Profile** (recommended for development):

```json
"args": [
  "mcp-proxy-for-aws@latest",
  "https://aws-mcp.us-east-1.api.aws/mcp",
  "--profile", "my-profile",
  "--metadata", "AWS_REGION=us-west-2"
]
```

2. **Environment Variables**:

```json
"env": {
  "AWS_ACCESS_KEY_ID": "...",
  "AWS_SECRET_ACCESS_KEY": "...",
  "AWS_REGION": "us-west-2"
}
```

3. **IAM Role** (for EC2/ECS/Lambda): No additional config needed - uses instance credentials

**Additional Options**:

- `--region <region>`: Override AWS region
- `--read-only`: Restrict to read-only tools
- `--log-level <level>`: Set logging level (debug, info, warning, error)

**Reference**: https://github.com/aws/mcp-proxy-for-aws

### Option B: AWS Documentation MCP Server (No Auth)

**Use when**:

- No Python/uvx environment
- No AWS credentials
- Only need documentation search (no API execution)

**Configuration**:

```json
{
  "mcpServers": {
    "awsdocs": {
      "type": "http",
      "url": "https://knowledge-mcp.global.api.aws"
    }
  }
}
```

### Option C: AWS IaC MCP Server

**Use when**: When uvx available AND AWS credentials are valid

**Required IAM Permissions** (for deployment troubleshooting only):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:DescribeStackResources",
        "cloudtrail:LookupEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

**Configuration** (add to your MCP settings):

```json
{
  "mcpServers": {
    "awslabs.aws-iac-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.aws-iac-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "your-named-profile",
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

**Windows Configuration**:

```json
{
  "mcpServers": {
    "awslabs.aws-iac-mcp-server": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "uv",
      "args": [
        "tool",
        "run",
        "--from",
        "awslabs.aws-iac-mcp-server@latest",
        "awslabs.aws-iac-mcp-server.exe"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR",
        "AWS_PROFILE": "your-aws-profile",
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

### Option D: Terraform MCP Server

**Use when**: When uvx, python, terraform CLI AND Checkov is installed.

**Configuration** (add to your MCP settings):

```json
{
  "mcpServers": {
    "awslabs.terraform-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.terraform-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

**Windows Configuration**:

```json
{
  "mcpServers": {
    "awslabs.terraform-mcp-server": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "uv",
      "args": [
        "tool",
        "run",
        "--from",
        "awslabs.terraform-mcp-server@latest",
        "awslabs.terraform-mcp-server.exe"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR",
        "AWS_PROFILE": "your-aws-profile",
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

### Option E: AWS Bedrock AgentCore MCP Server

**Use when**: When uvx AND python is already installed. 

**Configuration** (add to your MCP settings):

```json
{
  "mcpServers": {
    "bedrock-agentcore-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.amazon-bedrock-agentcore-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": ["search_agentcore_docs", "fetch_agentcore_doc"]
    }
  }
}
```

**Windows Configuration**:

```json
{
  "mcpServers": {
    "bedrock-agentcore-mcp-server": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "uv",
      "args": [
        "tool",
        "run",
        "--from",
        "awslabs.amazon-bedrock-agentcore-mcp-server@latest",
        "awslabs.amazon-bedrock-agentcore-mcp-server.exe"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

### Option F: Context7 MCP Server

**Use when**: You need up-to-date documentation and code examples for any programming library or framework.

**Prerequisites**: None - Context7 MCP Server requires no additional dependencies or credentials.

**Capabilities**:
- Resolve library names to Context7-compatible library IDs
- Query up-to-date documentation and code examples for any library
- Support for popular libraries like MongoDB, Next.js, Supabase, React, Express.js, and many more

**Configuration** (add to your MCP settings):

The Context7 MCP Server is typically configured automatically by Cursor. If you need to configure it manually, check your MCP settings file for a server named `user-Context7` or `Context7`.

**Usage**:
1. Use `resolve-library-id` to find the Context7-compatible library ID for a package name
2. Use `query-docs` with the library ID to retrieve documentation and code examples

**Example Workflow**:
- Query: "How to set up authentication with JWT in Express.js"
- Step 1: Call `resolve-library-id` with libraryName: "express" and query: "JWT authentication"
- Step 2: Use the returned library ID (e.g., "/expressjs/express") with `query-docs` to get documentation

**Note**: Context7 provides documentation for a wide range of libraries. If a library is not found, try alternative names or check Context7's supported libraries list.

## Step 3: Verification

After configuration, verify tools are available:

**For Full AWS MCP**:

- Look for tools: `mcp__aws-mcp__aws___search_documentation`, `mcp__aws-mcp__aws___call_aws`

**For Documentation MCP**:

- Look for tools: `mcp__awsdocs__aws___search_documentation`, `mcp__awsdocs__aws___read_documentation`

**For AWS IaC MCP Server**:

- Look for tools: `mcp__*aws-iac*__validate_cloudformation_template`, `mcp__*aws-iac*__search_cdk_documentation`, `mcp__*awslabs.aws-iac-mcp-server*__*`

**For Terraform MCP Server**:

- Look for tools: `mcp__*terraform*__*`, `mcp__*awslabs.terraform-mcp-server*__*`

**For Bedrock AgentCore MCP Server**:

- Look for tools: `mcp__*bedrock-agentcore*__*`, `mcp__*awslabs.amazon-bedrock-agentcore-mcp-server*__search_agentcore_docs`, `mcp__*awslabs.amazon-bedrock-agentcore-mcp-server*__fetch_agentcore_doc`, `mcp__*awslabs.amazon-bedrock-agentcore-mcp-server*__manage_agentcore_*`

**For Context7 MCP Server**:

- Look for tools: `mcp__*Context7*__query-docs`, `mcp__*Context7*__resolve-library-id`, `mcp__*user-Context7*__*`

## Troubleshooting

| Issue                          | Cause                       | Solution                                                                   |
| ------------------------------ | --------------------------- | -------------------------------------------------------------------------- |
| `uvx: command not found`       | uv not installed            | Install with `pip install uv` or use Option B                              |
| `AccessDenied` error           | Missing IAM permissions     | Add aws-mcp:\* permissions to IAM policy                                   |
| `InvalidSignatureException`    | Credential issue            | Check `aws sts get-caller-identity`                                        |
| Tools not appearing            | MCP not started             | Restart your agent after config change                                     |
| `terraform: command not found` | Terraform CLI not installed | Install Terraform from https://developer.hashicorp.com/terraform/downloads |
| `checkov: command not found`   | Checkov not installed       | Install with `pip install checkov` or `brew install checkov`               |
| AWS IaC MCP tools missing           | Server not configured       | Add `awslabs.aws-iac-mcp-server` to MCP settings (see Option C)            |
| Terraform MCP tools missing         | Server not configured       | Add `awslabs.terraform-mcp-server` to MCP settings (see Option D)          |
| Bedrock AgentCore MCP tools missing | Server not configured       | Add `bedrock-agentcore-mcp-server` to MCP settings (see Option E)          |
| Context7 MCP tools missing          | Server not configured       | Context7 is typically auto-configured. Check MCP settings for `user-Context7` or `Context7` server |
