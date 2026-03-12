# Gateway Troubleshooting Guide

Common errors, diagnosis steps, and solutions for Gateway service issues.

## Common Errors

### Error: "Target not found"

**Symptoms**: `ResourceNotFoundException` when accessing gateway target

**Diagnosis**:
```bash
# Check if target exists
aws bedrock-agentcore-control get-gateway-target \
 --gateway-identifier <gateway-id> \
 --target-identifier <target-id>

# List all targets
aws bedrock-agentcore-control list-gateway-targets \
 --gateway-identifier <gateway-id>
```

**Solution**: Verify gateway and target identifiers are correct. Check region matches.

---

### Error: "Invalid schema format"

**Symptoms**: `ValidationException` when creating target with OpenAPI schema

**Diagnosis**:
```bash
# Validate OpenAPI schema locally first
# Use openapi-validator or similar tool
npm install -g @apidevtools/swagger-cli
swagger-cli validate api-schema.yaml
```

**Solution**: Ensure OpenAPI schema is valid YAML/JSON and follows OpenAPI 3.0+ specification.

---

### Error: "Credential provider not found"

**Symptoms**: `ResourceNotFoundException` when referencing credential provider ARN

**Diagnosis**:
```bash
# Check if credential provider exists
aws bedrock-agentcore-control get-api-key-credential-provider \
 --name MyAPICredentialProvider

# Verify ARN format
# Should be: arn:aws:bedrock-agentcore:REGION:ACCOUNT_ID:api-key-credential-provider/NAME
```

**Solution**: Create credential provider before referencing it, or verify ARN format matches.

---

### Error: "S3 access denied"

**Symptoms**: Cannot read OpenAPI schema from S3

**Diagnosis**:
```bash
# Test S3 access
aws s3 ls s3://bucket-name/schemas/

# Check bucket policy
aws s3api get-bucket-policy --bucket bucket-name
```

**Solution**: Ensure Gateway service role has `s3:GetObject` permission on the schema bucket.

---

### Error: "Target status: FAILED"

**Symptoms**: Target created but status shows FAILED

**Diagnosis**:
```bash
# Get detailed target status
aws bedrock-agentcore-control get-gateway-target \
 --gateway-identifier <gateway-id> \
 --target-identifier <target-id> \
 --query 'status'

# Check CloudWatch logs
aws logs tail /aws/bedrock-agentcore/gateway --follow
```

**Solution**: Review CloudWatch logs for specific error messages. Common causes:
- Invalid schema format
- Network connectivity issues
- Authentication failures
- Missing IAM permissions

## Diagnosis Workflow

1. **Verify prerequisites**:
   - Gateway exists and is accessible
   - AWS credentials are valid
   - Region is correct

2. **Check resource status**:
   - Target status (ACTIVE, FAILED, PENDING)
   - Credential provider status
   - S3 bucket accessibility

3. **Review logs**:
   - CloudWatch logs for Gateway service
   - CloudTrail for API call history

4. **Validate configuration**:
   - Schema format and validity
   - ARN formats
   - IAM permissions

## Getting Help

- **AWS Documentation**: [Gateway Troubleshooting](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-troubleshooting.html)
- **AWS Support**: Open a support case with error details
- **CloudWatch Logs**: Review service logs for detailed error messages
