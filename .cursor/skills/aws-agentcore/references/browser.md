# Browser Service

The Browser service enables AI agents to interact with websites, perform web automation, and scrape web content safely.

## Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Runtime with agent deployed

### Enable Browser for Agent

**Step 1: Configure browser**
```bash
aws bedrock-agentcore-control update-agent \
 --runtime-identifier <runtime-id> \
 --agent-identifier <agent-id> \
 --browser-configuration '{"enabled": true}'
```

**Step 2: Verify configuration**
```bash
aws bedrock-agentcore-control get-agent \
 --runtime-identifier <runtime-id> \
 --agent-identifier <agent-id> \
 --query 'browserConfiguration'
```

## Common Operations

### Use Browser in Agent
```bash
aws bedrock-agentcore-runtime invoke-agent \
 --runtime-identifier <runtime-id> \
 --agent-identifier <agent-id> \
 --input '{"messages": [{"role": "user", "content": "Navigate to example.com and tell me the page title"}]}'
```

The agent will automatically use Browser service when web interaction is needed.

## Security Considerations

Browser service provides:
- Isolated browser instances per execution
- Automatic cleanup after use
- Network restrictions (configurable)
- Content filtering options

## Limitations

- **Concurrent sessions**: Limited by service quotas
- **Execution time**: Limited by agent timeout
- **JavaScript support**: Full modern browser capabilities
- **Network access**: Configurable per agent

## Related Resources

- [AWS Browser Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/browser.html)
- [Bedrock AgentCore CLI Reference](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/bedrock-agentcore-control/index.html)
