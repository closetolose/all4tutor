# Gateway Deployment Strategies

This guide covers deployment patterns, credential management, and multi-environment setup for Gateway targets.

## Deployment Patterns

### Pattern 1: Single Environment

**Use Case**: Development or simple production deployments

```bash
# Upload schema
aws s3 cp api-schema.yaml s3://my-bucket/schemas/

# Create credential provider
aws bedrock-agentcore-control create-api-key-credential-provider \
 --name ProductionAPIKey \
 --api-key "$API_KEY"

# Create target
aws bedrock-agentcore-control create-gateway-target \
 --gateway-identifier <gateway-id> \
 --name ProductionTarget \
 --endpoint-configuration '{"openApiSchema": {"s3": {"uri": "s3://my-bucket/schemas/api-schema.yaml"}}}' \
 --credential-provider-configurations '[{"credentialProviderType": "GATEWAY_API_KEY_CREDENTIAL_PROVIDER", "apiKeyCredentialProvider": {"providerArn": "arn:aws:bedrock-agentcore:us-west-2:ACCOUNT_ID:api-key-credential-provider/ProductionAPIKey"}}]'
```

### Pattern 2: Multi-Environment

**Use Case**: Separate dev, staging, and production environments

```bash
# Development
aws bedrock-agentcore-control create-api-key-credential-provider \
 --name DevAPIKey \
 --api-key "$DEV_API_KEY"

aws bedrock-agentcore-control create-gateway-target \
 --gateway-identifier <dev-gateway-id> \
 --name DevTarget \
 --endpoint-configuration '{"openApiSchema": {"s3": {"uri": "s3://dev-bucket/schemas/api-schema.yaml"}}}' \
 --credential-provider-configurations '[{"credentialProviderType": "GATEWAY_API_KEY_CREDENTIAL_PROVIDER", "apiKeyCredentialProvider": {"providerArn": "arn:aws:bedrock-agentcore:us-west-2:ACCOUNT_ID:api-key-credential-provider/DevAPIKey"}}]'

# Production
aws bedrock-agentcore-control create-api-key-credential-provider \
 --name ProdAPIKey \
 --api-key "$PROD_API_KEY"

aws bedrock-agentcore-control create-gateway-target \
 --gateway-identifier <prod-gateway-id> \
 --name ProdTarget \
 --endpoint-configuration '{"openApiSchema": {"s3": {"uri": "s3://prod-bucket/schemas/api-schema.yaml"}}}' \
 --credential-provider-configurations '[{"credentialProviderType": "GATEWAY_API_KEY_CREDENTIAL_PROVIDER", "apiKeyCredentialProvider": {"providerArn": "arn:aws:bedrock-agentcore:us-west-2:ACCOUNT_ID:api-key-credential-provider/ProdAPIKey"}}]'
```

## Credential Rotation

### Rotating API Keys

```bash
# Step 1: Generate new API key
NEW_KEY=$(generate-new-api-key)

# Step 2: Update credential provider
aws bedrock-agentcore-control update-api-key-credential-provider \
 --name MyAPICredentialProvider \
 --api-key "$NEW_KEY"

# Step 3: Verify targets still work
aws bedrock-agentcore-control get-gateway-target \
 --gateway-identifier <gateway-id> \
 --target-identifier <target-id>
```

### Zero-Downtime Rotation

For zero-downtime rotation, use a two-provider approach:

```bash
# Step 1: Create new provider with new key
aws bedrock-agentcore-control create-api-key-credential-provider \
 --name MyAPICredentialProviderV2 \
 --api-key "$NEW_KEY"

# Step 2: Update target to use both providers (if supported)
# Or update target to new provider
aws bedrock-agentcore-control update-gateway-target \
 --gateway-identifier <gateway-id> \
 --target-identifier <target-id> \
 --credential-provider-configurations '[{"credentialProviderType": "GATEWAY_API_KEY_CREDENTIAL_PROVIDER", "apiKeyCredentialProvider": {"providerArn": "arn:aws:bedrock-agentcore:us-west-2:ACCOUNT_ID:api-key-credential-provider/MyAPICredentialProviderV2"}}]'

# Step 3: Verify new provider works
# Step 4: Delete old provider
aws bedrock-agentcore-control delete-api-key-credential-provider \
 --name MyAPICredentialProvider
```

## IAM Configuration

### Required Permissions for Gateway Operations

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore-control:CreateGatewayTarget",
        "bedrock-agentcore-control:GetGatewayTarget",
        "bedrock-agentcore-control:ListGatewayTargets",
        "bedrock-agentcore-control:UpdateGatewayTarget",
        "bedrock-agentcore-control:DeleteGatewayTarget",
        "bedrock-agentcore-control:CreateApiKeyCredentialProvider",
        "bedrock-agentcore-control:GetApiKeyCredentialProvider",
        "bedrock-agentcore-control:UpdateApiKeyCredentialProvider",
        "bedrock-agentcore-control:DeleteApiKeyCredentialProvider",
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "*"
    }
  ]
}
```

## Best Practices

1. **Separate schemas by environment**: Use different S3 buckets or prefixes
2. **Version your schemas**: Include version numbers in schema filenames
3. **Monitor target health**: Set up CloudWatch alarms for target status
4. **Use least privilege**: Grant minimal IAM permissions required
5. **Rotate credentials regularly**: Implement quarterly rotation schedule
