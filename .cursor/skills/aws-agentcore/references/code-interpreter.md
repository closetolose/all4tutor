# Code Interpreter Service

The Code Interpreter service enables secure code execution in isolated sandboxes, allowing agents to run Python code safely.

## Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Runtime with agent deployed

### Enable Code Interpreter for Agent

**Step 1: Configure code interpreter**
```bash
aws bedrock-agentcore-control update-agent \
 --runtime-identifier <runtime-id> \
 --agent-identifier <agent-id> \
 --code-interpreter-configuration '{"enabled": true}'
```

**Step 2: Verify configuration**
```bash
aws bedrock-agentcore-control get-agent \
 --runtime-identifier <runtime-id> \
 --agent-identifier <agent-id> \
 --query 'codeInterpreterConfiguration'
```

## Security Considerations

Code Interpreter runs code in isolated sandboxes with:
- Network isolation (no outbound access by default)
- Resource limits (CPU, memory, execution time)
- File system restrictions
- Automatic cleanup after execution

## Common Operations

### Execute Code
```bash
aws bedrock-agentcore-runtime invoke-agent \
 --runtime-identifier <runtime-id> \
 --agent-identifier <agent-id> \
 --input '{"messages": [{"role": "user", "content": "Calculate 2+2 in Python"}]}'
```

The agent will automatically use Code Interpreter when code execution is needed.

## Limitations

- **Supported languages**: Python only
- **Execution time**: Limited by agent timeout
- **Network access**: Disabled by default (can be configured)
- **File system**: Temporary, isolated per execution

## Related Resources

- [AWS Code Interpreter Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter.html)
- [Bedrock AgentCore CLI Reference](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/bedrock-agentcore-control/index.html)
