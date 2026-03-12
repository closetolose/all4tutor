# Troubleshooting

Common issues and solutions when creating and managing AgentCore agents.

## Agent Not Responding

If your agent doesn't respond to invocations:

1. **Check agent status:**
   - Use `mcp__aws-mcp__aws___call_aws` with service `bedrock-agentcore-control`, operation `GetAgent`, runtime identifier, and agent identifier
   - Verify the agent status is `ACTIVE` or `READY`

2. **Verify runtime status:**
   - Use `mcp__aws-mcp__aws___call_aws` with service `bedrock-agentcore-control`, operation `GetRuntime`, and runtime identifier
   - Ensure the runtime is operational

3. **Check CloudWatch logs** (if observability enabled):
   - Use `mcp__aws-mcp__aws___call_aws` with service `cloudwatch-logs`, operation `TailLogEvents` for the log group `/aws/bedrock-agentcore/agents`
   - Look for error messages or exceptions

4. **Verify model access:**
   - Ensure the foundation model specified in agent configuration is available in your region
   - Check that your account has access to the model

## Permission Errors

If you encounter permission errors:

**Verify IAM permissions include:**
- `bedrock-agentcore-control:CreateRuntime`
- `bedrock-agentcore-control:CreateAgent`
- `bedrock-agentcore-control:GetRuntime`
- `bedrock-agentcore-control:GetAgent`
- `bedrock-agentcore-control:UpdateAgent`
- `bedrock-agentcore-runtime:InvokeAgent`
- `bedrock:InvokeModel` (for the specific model)

**For Memory service:**
- `bedrock-agentcore-control:CreateMemory`
- `bedrock-agentcore-runtime:StoreConversation`
- `bedrock-agentcore-runtime:RetrieveConversation`

**For Gateway service:**
- `bedrock-agentcore-control:CreateGatewayTarget`
- `bedrock-agentcore-control:CreateApiKeyCredentialProvider`
- `s3:PutObject` (for schema uploads)

**For Observability:**
- `logs:CreateLogGroup`
- `logs:PutLogEvents`
- `xray:PutTraceSegments`

## Model Access Issues

If you can't access foundation models:

1. **Verify model availability:**
   - Use `mcp__aws-mcp__aws___call_aws` with service `bedrock`, operation `ListFoundationModels`, and region parameter
   - Check that your target model is listed

2. **Request model access:**
   - Some models require explicit access requests in the AWS Bedrock console
   - Navigate to AWS Bedrock → Model access and request access to your desired model

3. **Check region availability:**
   - Not all models are available in all regions
   - Verify your model is available in your target region

## Runtime Creation Failures

If runtime creation fails:

1. **Check IAM permissions:**
   - Ensure you have `bedrock-agentcore-control:CreateRuntime` permission
   - Verify your IAM role or user has the necessary permissions

2. **Verify service quotas:**
   - Check if you've reached runtime creation limits
   - Review AWS service quotas for Bedrock AgentCore

3. **Check region support:**
   - Ensure AgentCore Runtime is available in your target region
   - Some regions may not support all AgentCore services

## Memory Service Issues

If memory isn't working:

1. **Verify memory is linked:**
   - Use `GetAgent` to check if `memoryConfiguration` is present
   - Ensure the memory identifier is correct

2. **Check conversation ID:**
   - Memory requires consistent `conversationId` values across invocations
   - Verify you're using the same `conversationId` for related conversations

3. **Verify IAM permissions:**
   - Ensure the agent's execution role has memory service permissions
   - Check `bedrock-agentcore-runtime:StoreConversation` and `RetrieveConversation` permissions

## Gateway Target Issues

If Gateway targets aren't working:

1. **Verify target status:**
   - Use `GetGatewayTarget` to check target health
   - Ensure the target is in `ACTIVE` status

2. **Check schema validity:**
   - Verify your OpenAPI schema is valid
   - Ensure the schema is accessible from the S3 location

3. **Verify credentials:**
   - Check that credential providers are correctly configured
   - Ensure API keys are valid and not expired

4. **Check network connectivity:**
   - Verify the target API endpoint is accessible
   - Test the API endpoint directly to ensure it's responding

## Code Interpreter Issues

If Code Interpreter isn't executing code:

1. **Verify configuration:**
   - Check that `codeInterpreterConfiguration.enabled` is `true`
   - Use `GetAgent` to verify the configuration

2. **Check code syntax:**
   - Ensure the Python code requested is valid
   - Code Interpreter only supports Python

3. **Review execution limits:**
   - Code execution has time and resource limits
   - Very long-running or resource-intensive code may fail

## Browser Service Issues

If Browser service isn't working:

1. **Verify configuration:**
   - Check that `browserConfiguration.enabled` is `true`
   - Use `GetAgent` to verify the configuration

2. **Check website accessibility:**
   - Some websites may block automated access
   - Verify the target website is accessible

3. **Review content restrictions:**
   - Browser service may have content filtering
   - Check if the requested content violates policies
