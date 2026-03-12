# Identity Service

The Identity service manages API credentials, authentication tokens, and access control for AgentCore services.

## Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions

### Create API Key Credential Provider

**Step 1: Create credential provider**
```bash
aws bedrock-agentcore-control create-api-key-credential-provider \
 --name MyAPICredentialProvider \
 --api-key "YOUR_API_KEY" \
 --region us-west-2
```

**Step 2: Verify creation**
```bash
aws bedrock-agentcore-control get-api-key-credential-provider \
 --name MyAPICredentialProvider \
 --region us-west-2
```

**Step 3: Use in Gateway target**
```bash
aws bedrock-agentcore-control create-gateway-target \
 --gateway-identifier <gateway-id> \
 --name MyTarget \
 --credential-provider-configurations '[{"credentialProviderType": "GATEWAY_API_KEY_CREDENTIAL_PROVIDER", "apiKeyCredentialProvider": {"providerArn": "arn:aws:bedrock-agentcore:us-west-2:ACCOUNT_ID:api-key-credential-provider/MyAPICredentialProvider"}}]'
```

## Common Operations

### List Credential Providers
```bash
aws bedrock-agentcore-control list-api-key-credential-providers \
 --region us-west-2
```

### Update Credential Provider
```bash
aws bedrock-agentcore-control update-api-key-credential-provider \
 --name MyAPICredentialProvider \
 --api-key "NEW_API_KEY" \
 --region us-west-2
```

### Delete Credential Provider
```bash
aws bedrock-agentcore-control delete-api-key-credential-provider \
 --name MyAPICredentialProvider \
 --region us-west-2
```

## Security Best Practices

1. **Use AWS KMS encryption**: Credentials are automatically encrypted using AWS KMS
2. **Rotate regularly**: Update credentials quarterly or when compromised
3. **Least privilege**: Grant minimal permissions required
4. **Monitor usage**: Set up CloudWatch alarms for unusual activity
5. **Audit access**: Enable CloudTrail for credential access logging

## Related Resources

- [Credential Management](credential-management.md)
- [AWS Identity Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity.html)
- [Bedrock AgentCore CLI Reference](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/bedrock-agentcore-control/index.html)
