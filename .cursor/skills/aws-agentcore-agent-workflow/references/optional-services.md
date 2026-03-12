# Optional Service Enhancements

Detailed instructions for adding optional services to your AgentCore agent.

## Add Memory Service

Enable persistent conversation memory across sessions.

**Step 1: Get Memory management guide**

Use `mcp__*bedrock-agentcore*__manage_agentcore_memory` or `mcp__*awslabs.amazon-bedrock-agentcore-mcp-server*__manage_agentcore_memory` for comprehensive Memory setup instructions.

**Step 2: Create memory configuration**

Use `mcp__aws-mcp__aws___call_aws` with service `bedrock-agentcore-control`, operation `CreateMemory`. Required parameters: `name`, `region`.

Save the memory identifier from the response.

**Step 3: Link memory to agent**

Use `mcp__aws-mcp__aws___call_aws` with service `bedrock-agentcore-control`, operation `UpdateAgent`. Include `memoryConfiguration` with `memoryIdentifier` in the parameters.

**For detailed Memory setup:** See [`../../aws-agentcore/references/memory.md`](../../aws-agentcore/references/memory.md)

## Add Gateway Service

Enable agent to use external REST APIs as tools via MCP.

**Prerequisites:**

- Gateway already created (via Console or MCP)
- OpenAPI schema for target API
- S3 bucket for schema storage

**Step 1: Get Gateway deployment guide**

Use `mcp__*bedrock-agentcore*__manage_agentcore_gateway` or `mcp__*awslabs.amazon-bedrock-agentcore-mcp-server*__manage_agentcore_gateway` for comprehensive Gateway setup instructions.

**Step 2: Upload OpenAPI schema**

Use `mcp__aws-mcp__aws___call_aws` with service `s3`, operation `PutObject` to upload your OpenAPI schema file to S3.

**Step 3: Create credential provider (if API key auth needed)**

Use `mcp__aws-mcp__aws___call_aws` with service `bedrock-agentcore-control`, operation `CreateApiKeyCredentialProvider`. Required parameters: `name`, `apiKey`, `region`.

Save the credential provider ARN from the response.

**Step 4: Create gateway target**

Use `mcp__aws-mcp__aws___call_aws` with service `bedrock-agentcore-control`, operation `CreateGatewayTarget`. Required parameters: `gatewayIdentifier`, `name`, `endpointConfiguration` (with `openApiSchema.s3.uri`), `credentialProviderConfigurations` (if using API key auth), `region`.

**For detailed Gateway setup:** See [`../../aws-agentcore/references/gateway.md`](../../aws-agentcore/references/gateway.md) and [`../../aws-agentcore/references/gateway-deployment.md`](../../aws-agentcore/references/gateway-deployment.md)

## Add Code Interpreter

Enable secure Python code execution in sandboxes.

Use `mcp__aws-mcp__aws___call_aws` with service `bedrock-agentcore-control`, operation `UpdateAgent`. Include `codeInterpreterConfiguration` with `enabled: true` in the parameters.

**For detailed Code Interpreter setup:** See [`../../aws-agentcore/references/code-interpreter.md`](../../aws-agentcore/references/code-interpreter.md)

## Add Browser Service

Enable web automation and scraping capabilities.

Use `mcp__aws-mcp__aws___call_aws` with service `bedrock-agentcore-control`, operation `UpdateAgent`. Include `browserConfiguration` with `enabled: true` in the parameters.

**For detailed Browser setup:** See [`../../aws-agentcore/references/browser.md`](../../aws-agentcore/references/browser.md)

## Add Observability

Enable monitoring, logging, and tracing.

Use `mcp__aws-mcp__aws___call_aws` with service `bedrock-agentcore-control`, operation `UpdateAgent`. Include `observabilityConfiguration` with `enabled: true`, `cloudWatchLogs.enabled: true`, and `xRayTracing.enabled: true` in the parameters.

**For detailed Observability setup:** See [`../../aws-agentcore/references/observability.md`](../../aws-agentcore/references/observability.md)
