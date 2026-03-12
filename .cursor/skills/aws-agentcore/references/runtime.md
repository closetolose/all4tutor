# Runtime Service

The Runtime service provides serverless execution environment for AI agents, handling scaling, resource management, and agent lifecycle.

## Quick Start

### Prerequisites

- AWS CLI configured with appropriate permissions
- Agent definition or configuration

### Deploy an Agent Runtime

**Step 1: Create runtime configuration**

```bash
aws bedrock-agentcore-control create-runtime \
 --name MyAgentRuntime \
 --region us-west-2
```

**Step 2: Configure agent**

```bash
aws bedrock-agentcore-control create-agent \
 --runtime-identifier <runtime-id> \
 --name MyAgent \
 --agent-configuration '{"modelId": "anthropic.claude-3-sonnet-20240229-v1:0"}'
```

**Step 3: Verify deployment**

```bash
aws bedrock-agentcore-control get-agent \
 --runtime-identifier <runtime-id> \
 --agent-identifier <agent-id>
```

## Common Operations

### List Agents

```bash
aws bedrock-agentcore-control list-agents \
 --runtime-identifier <runtime-id> \
 --region us-west-2
```

### Invoke Agent

```bash
aws bedrock-agentcore-runtime invoke-agent \
 --runtime-identifier <runtime-id> \
 --agent-identifier <agent-id> \
 --input '{"messages": [{"role": "user", "content": "Hello"}]}'
```

### Update Agent Configuration

```bash
aws bedrock-agentcore-control update-agent \
 --runtime-identifier <runtime-id> \
 --agent-identifier <agent-id> \
 --agent-configuration '{"modelId": "anthropic.claude-3-5-sonnet-20241022-v2:0"}'
```

## Authentication

Runtime supports two inbound authentication methods:

- **IAM (SigV4)**: Default authentication using AWS IAM credentials
- **JWT Bearer Token**: Token-based authentication with discovery URL

> **Note**: A Runtime can only use one inbound auth type (IAM or JWT), not both simultaneously.

## Related Resources

- [Credential Management](credential-management.md)
- [AWS Runtime Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime.html)
- [Bedrock AgentCore CLI Reference](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/bedrock-agentcore-control/index.html)
