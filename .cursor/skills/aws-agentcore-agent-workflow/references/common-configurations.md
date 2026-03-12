# Common Agent Configurations

Pre-built configuration patterns for different agent use cases.

## Configuration 1: Basic Conversational Agent

Minimal setup with Runtime and Agent only.

1. Use `mcp__aws-mcp__aws___call_aws` with `bedrock-agentcore-control` service, `CreateRuntime` operation
2. Use `mcp__aws-mcp__aws___call_aws` with `bedrock-agentcore-control` service, `CreateAgent` operation
   - Required: `runtimeIdentifier`, `name`, `agentConfiguration.modelId`, `region`

## Configuration 2: Agent with Memory

Runtime + Agent + Memory for persistent conversations.

1. Get Memory guide: `mcp__*bedrock-agentcore*__manage_agentcore_memory`
2. Use `mcp__aws-mcp__aws___call_aws` for:
   - `CreateRuntime` operation
   - `CreateAgent` operation
   - `CreateMemory` operation
   - `UpdateAgent` operation (include `memoryConfiguration.memoryIdentifier` to link memory)

## Configuration 3: Full-Featured Agent

Runtime + Agent + Memory + Code Interpreter + Browser + Observability.

1. Get guides: `mcp__*bedrock-agentcore*__manage_agentcore_runtime` and `mcp__*bedrock-agentcore*__manage_agentcore_memory`
2. Use `mcp__aws-mcp__aws___call_aws` for:
   - `CreateRuntime` operation
   - `CreateAgent` operation
   - `CreateMemory` operation
   - `UpdateAgent` operation (include all configurations: `memoryConfiguration`, `codeInterpreterConfiguration.enabled: true`, `browserConfiguration.enabled: true`, `observabilityConfiguration` with CloudWatch and X-Ray enabled)
