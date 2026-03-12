# Memory Service

The Memory service manages conversation state and context for AI agents, enabling persistent memory across sessions.

## Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Runtime with agent deployed

### Configure Memory for Agent

**Step 1: Create memory configuration**
```bash
aws bedrock-agentcore-control create-memory \
 --name MyAgentMemory \
 --region us-west-2
```

**Step 2: Link memory to agent**
```bash
aws bedrock-agentcore-control update-agent \
 --runtime-identifier <runtime-id> \
 --agent-identifier <agent-id> \
 --memory-configuration '{"memoryIdentifier": "<memory-id>"}'
```

**Step 3: Verify configuration**
```bash
aws bedrock-agentcore-control get-agent \
 --runtime-identifier <runtime-id> \
 --agent-identifier <agent-id> \
 --query 'memoryConfiguration'
```

## Common Operations

### Store Conversation
```bash
aws bedrock-agentcore-runtime store-conversation \
 --memory-identifier <memory-id> \
 --conversation-id "session-123" \
 --messages '[{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}]'
```

### Retrieve Conversation
```bash
aws bedrock-agentcore-runtime retrieve-conversation \
 --memory-identifier <memory-id> \
 --conversation-id "session-123"
```

### Delete Conversation
```bash
aws bedrock-agentcore-runtime delete-conversation \
 --memory-identifier <memory-id> \
 --conversation-id "session-123"
```

## Data Access

Memory service uses IAM roles for data access permissions. Ensure the agent's execution role has appropriate permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore-runtime:StoreConversation",
        "bedrock-agentcore-runtime:RetrieveConversation",
        "bedrock-agentcore-runtime:DeleteConversation"
      ],
      "Resource": "arn:aws:bedrock-agentcore:*:*:memory/*"
    }
  ]
}
```

## Related Resources

- [Credential Management](credential-management.md)
- [AWS Memory Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html)
- [Bedrock AgentCore CLI Reference](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/bedrock-agentcore-control/index.html)
