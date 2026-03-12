# Observability Service

The Observability service provides tracing, monitoring, and logging capabilities for AgentCore agents and services.

## Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Runtime with agent deployed

### Enable Observability

**Step 1: Configure observability**
```bash
aws bedrock-agentcore-control update-agent \
 --runtime-identifier <runtime-id> \
 --agent-identifier <agent-id> \
 --observability-configuration '{"enabled": true, "cloudWatchLogs": {"enabled": true}, "xRayTracing": {"enabled": true}}'
```

**Step 2: Verify configuration**
```bash
aws bedrock-agentcore-control get-agent \
 --runtime-identifier <runtime-id> \
 --agent-identifier <agent-id> \
 --query 'observabilityConfiguration'
```

## Monitoring Setup

### CloudWatch Dashboards

Create a dashboard to monitor agent performance:

```bash
aws cloudwatch put-dashboard \
 --dashboard-name AgentCore-Monitoring \
 --dashboard-body '{
   "widgets": [
     {
       "type": "metric",
       "properties": {
         "metrics": [
           ["AWS/BedrockAgentCore", "InvocationCount", {"stat": "Sum"}],
           [".", "InvocationDuration", {"stat": "Average"}],
           [".", "ErrorCount", {"stat": "Sum"}]
         ],
         "period": 300,
         "stat": "Average",
         "region": "us-west-2",
         "title": "Agent Performance"
       }
     }
   ]
 }'
```

### CloudWatch Alarms

Set up alarms for error rates and latency:

```bash
# Error rate alarm
aws cloudwatch put-metric-alarm \
 --alarm-name AgentCore-HighErrorRate \
 --alarm-description "Alert when error rate exceeds 10%" \
 --metric-name ErrorRate \
 --namespace AWS/BedrockAgentCore \
 --statistic Average \
 --period 300 \
 --threshold 0.1 \
 --comparison-operator GreaterThanThreshold

# Latency alarm
aws cloudwatch put-metric-alarm \
 --alarm-name AgentCore-HighLatency \
 --alarm-description "Alert when latency exceeds 5 seconds" \
 --metric-name InvocationDuration \
 --namespace AWS/BedrockAgentCore \
 --statistic Average \
 --period 300 \
 --threshold 5000 \
 --comparison-operator GreaterThanThreshold
```

## Distributed Tracing

### X-Ray Integration

Enable X-Ray tracing for distributed tracing:

```bash
# Enable X-Ray for agent
aws bedrock-agentcore-control update-agent \
 --runtime-identifier <runtime-id> \
 --agent-identifier <agent-id> \
 --observability-configuration '{"xRayTracing": {"enabled": true}}'

# View traces in X-Ray console
aws xray get-trace-summaries \
 --start-time $(date -u -d '1 hour ago' +%s) \
 --end-time $(date -u +%s) \
 --filter-expression 'service("bedrock-agentcore")'
```

## Logging

### CloudWatch Logs

View agent execution logs:

```bash
# List log groups
aws logs describe-log-groups \
 --log-group-name-prefix /aws/bedrock-agentcore

# Tail logs
aws logs tail /aws/bedrock-agentcore/agents --follow
```

## Common Operations

### Query Metrics
```bash
aws cloudwatch get-metric-statistics \
 --namespace AWS/BedrockAgentCore \
 --metric-name InvocationCount \
 --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
 --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
 --period 300 \
 --statistics Sum
```

### View Traces
```bash
aws xray get-trace-summaries \
 --start-time $(date -u -d '1 hour ago' +%s) \
 --end-time $(date -u +%s) \
 --filter-expression 'service("bedrock-agentcore") AND error'
```

## Best Practices

1. **Enable observability early**: Set up monitoring from the start
2. **Set meaningful alarms**: Configure alerts for critical metrics
3. **Review logs regularly**: Check CloudWatch logs for errors
4. **Use X-Ray for debugging**: Trace requests across services
5. **Monitor costs**: CloudWatch and X-Ray have associated costs

## Related Resources

- [AWS Observability Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability.html)
- [CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
- [X-Ray Documentation](https://docs.aws.amazon.com/xray/)
- [Bedrock AgentCore CLI Reference](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/bedrock-agentcore-control/index.html)
