# Testing Your Agent

Comprehensive testing procedures for AgentCore agents.

## Basic Invocation Test

Test that your agent responds correctly to basic queries.

Use `mcp__aws-mcp__aws___call_aws` with service `bedrock-agentcore-runtime`, operation `InvokeAgent`. Required parameters: `runtimeIdentifier`, `agentIdentifier`, `input.messages` (array with `role: "user"` and `content`), `region`.

**Expected result:** Agent should respond with "4" or a similar mathematical answer.

## Test with Memory (if enabled)

Verify that memory persists across conversations.

Use `mcp__aws-mcp__aws___call_aws` with `InvokeAgent` operation. Include the same `conversationId` in `input` for related conversations.

**First conversation:** Include `conversationId: "test-session-1"` and message `"My name is Alice"`

**Second conversation:** Use the same `conversationId: "test-session-1"` and ask `"What is my name?"`

**Expected result:** Agent should respond with "Alice" or reference the previous conversation.

## Test Code Interpreter (if enabled)

Verify that the agent can execute Python code.

Use `mcp__aws-mcp__aws___call_aws` with service `bedrock-agentcore-runtime`, operation `InvokeAgent`. Request Python code execution in the message content (e.g., "Write Python code to calculate the factorial of 10").

**Expected result:** Agent should execute Python code and return the factorial result (3628800).

## Test Gateway Integration (if enabled)

If you've configured Gateway targets, test that the agent can use external APIs.

Use `mcp__aws-mcp__aws___call_aws` with `InvokeAgent` operation. Request API usage in the message content (e.g., "Use the API to get the current weather in Seattle").

**Expected result:** Agent should invoke the Gateway target and return API results.

## Test Browser Service (if enabled)

Verify that the agent can interact with web pages.

Use `mcp__aws-mcp__aws___call_aws` with `InvokeAgent` operation. Request web navigation in the message content (e.g., "Navigate to example.com and tell me what's on the page").

**Expected result:** Agent should use the Browser service to fetch and summarize web content.
