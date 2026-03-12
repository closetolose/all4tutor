# IaC Conversion Patterns

Reference for mapping constructs between CloudFormation, CDK, and Terraform.

## Concept Mapping

| Concept               | CloudFormation             | CDK (TypeScript)                | Terraform                        |
| --------------------- | -------------------------- | ------------------------------- | -------------------------------- |
| **Input parameters**  | `Parameters`               | Stack props / context values    | `variable` blocks                |
| **Resources**         | `Resources`                | Construct instances             | `resource` blocks                |
| **Data lookups**      | `Fn::ImportValue`, Mappings | `Fn.importValue`, lookups      | `data` sources                   |
| **Outputs**           | `Outputs`                  | `CfnOutput`                     | `output` blocks                  |
| **Conditionals**      | `Conditions` + `Fn::If`   | Native TypeScript `if`          | `count`, `for_each`, conditionals |
| **Loops**             | Not native (use macros)    | Native TypeScript loops         | `count`, `for_each`              |
| **Cross-references**  | `Ref`, `Fn::GetAtt`       | Construct property references   | Resource attribute references    |
| **Dependencies**      | `DependsOn`               | Implicit via construct refs     | Implicit refs, `depends_on`      |
| **Nested structures** | Nested stacks              | Nested stacks / constructs      | Modules                          |
| **State**             | CloudFormation stack state | CloudFormation stack state      | Terraform state file             |
| **Provider config**   | N/A (implicit AWS)        | Environment / account config    | `provider` block                 |

## CloudFormation to Terraform

### Resource Type Mapping

CloudFormation resource types map to Terraform as:

```
AWS::Service::Resource  →  aws_service_resource (lowercase, underscores)
```

**Examples:**

| CloudFormation                    | Terraform                          |
| --------------------------------- | ---------------------------------- |
| `AWS::Lambda::Function`           | `aws_lambda_function`              |
| `AWS::S3::Bucket`                 | `aws_s3_bucket` + policy resources |
| `AWS::DynamoDB::Table`            | `aws_dynamodb_table`               |
| `AWS::IAM::Role`                  | `aws_iam_role`                     |
| `AWS::EC2::Instance`              | `aws_instance`                     |
| `AWS::EC2::VPC`                   | `aws_vpc`                          |
| `AWS::EC2::Subnet`                | `aws_subnet`                       |
| `AWS::EC2::SecurityGroup`         | `aws_security_group`               |
| `AWS::SQS::Queue`                 | `aws_sqs_queue`                    |
| `AWS::SNS::Topic`                 | `aws_sns_topic`                    |
| `AWS::ApiGateway::RestApi`        | `aws_api_gateway_rest_api`         |
| `AWS::ECS::Cluster`               | `aws_ecs_cluster`                  |
| `AWS::RDS::DBInstance`            | `aws_db_instance`                  |
| `AWS::CloudFront::Distribution`   | `aws_cloudfront_distribution`      |

### Intrinsic Functions

| CloudFormation        | Terraform Equivalent                        |
| --------------------- | ------------------------------------------- |
| `Ref`                 | Resource attribute reference                |
| `Fn::GetAtt`          | Resource attribute reference                |
| `Fn::Join`            | `join()` function                           |
| `Fn::Sub`             | String interpolation `"${var}"`             |
| `Fn::Select`          | `element()` function                        |
| `Fn::Split`           | `split()` function                          |
| `Fn::If`              | Ternary `condition ? true : false`          |
| `Fn::Equals`          | `==` comparison                             |
| `Fn::FindInMap`       | `lookup()` or `local` values                |
| `Fn::ImportValue`     | `data.terraform_remote_state` or `data.aws_*` |
| `Fn::Base64`          | `base64encode()` function                   |
| `Fn::Cidr`            | `cidrsubnet()` function                     |

### Parameters to Variables

```yaml
# CloudFormation
Parameters:
  InstanceType:
    Type: String
    Default: t3.micro
    AllowedValues: [t3.micro, t3.small, t3.medium]
    Description: EC2 instance type
```

```hcl
# Terraform
variable "instance_type" {
  type        = string
  default     = "t3.micro"
  description = "EC2 instance type"

  validation {
    condition     = contains(["t3.micro", "t3.small", "t3.medium"], var.instance_type)
    error_message = "Must be one of: t3.micro, t3.small, t3.medium."
  }
}
```

### Outputs

```yaml
# CloudFormation
Outputs:
  BucketArn:
    Value: !GetAtt MyBucket.Arn
    Export:
      Name: my-bucket-arn
```

```hcl
# Terraform
output "bucket_arn" {
  value       = aws_s3_bucket.my_bucket.arn
  description = "ARN of the S3 bucket"
}
```

## CloudFormation to CDK (TypeScript)

### Resource Mapping

CloudFormation resources map to CDK L2 constructs (preferred) or L1 (`Cfn*`) constructs:

| CloudFormation                  | CDK L2 Construct                         | CDK L1 (Cfn) Fallback                |
| ------------------------------- | ---------------------------------------- | ------------------------------------- |
| `AWS::Lambda::Function`         | `lambda.Function`                        | `lambda.CfnFunction`                 |
| `AWS::S3::Bucket`               | `s3.Bucket`                              | `s3.CfnBucket`                       |
| `AWS::DynamoDB::Table`          | `dynamodb.Table`                         | `dynamodb.CfnTable`                  |
| `AWS::IAM::Role`                | `iam.Role`                               | `iam.CfnRole`                        |
| `AWS::SQS::Queue`               | `sqs.Queue`                              | `sqs.CfnQueue`                       |
| `AWS::SNS::Topic`               | `sns.Topic`                              | `sns.CfnTopic`                       |
| `AWS::EC2::VPC`                 | `ec2.Vpc`                                | `ec2.CfnVPC`                         |
| `AWS::ECS::Cluster`             | `ecs.Cluster`                            | `ecs.CfnCluster`                     |

**Preference order**: Always prefer L2 constructs over L1 — they provide better defaults, simpler APIs, and built-in best practices.

### Parameters to Props

```yaml
# CloudFormation Parameters
Parameters:
  BucketName:
    Type: String
    Description: Name of the S3 bucket
```

```typescript
// CDK Stack Props
interface MyStackProps extends cdk.StackProps {
  bucketName: string;
}
```

### Conditions

```yaml
# CloudFormation
Conditions:
  IsProd: !Equals [!Ref Environment, "prod"]
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Condition: IsProd
```

```typescript
// CDK — use native TypeScript conditionals
if (props.environment === 'prod') {
  new s3.Bucket(this, 'MyBucket', { /* ... */ });
}
```

## Terraform to CloudFormation

### Resource Type Mapping

```
aws_service_resource  →  AWS::Service::Resource (PascalCase)
```

### Variables to Parameters

```hcl
# Terraform
variable "environment" {
  type    = string
  default = "dev"
}
```

```yaml
# CloudFormation
Parameters:
  Environment:
    Type: String
    Default: dev
```

### Key Differences to Handle

| Terraform Feature         | CloudFormation Approach                         |
| ------------------------- | ----------------------------------------------- |
| `for_each`                | Use `AWS::CloudFormation::Macro` or duplicate    |
| `count`                   | Use `Conditions` or duplicate resources          |
| `data` sources            | `Fn::ImportValue`, custom resources, or hardcode |
| `locals`                  | `Mappings` or repeated values                    |
| Dynamic blocks            | Requires manual expansion                        |
| `terraform_remote_state`  | `Fn::ImportValue` with stack exports             |
| Module composition        | Nested stacks                                    |

## Terraform to CDK (TypeScript)

### Resource Mapping

```
aws_service_resource  →  service.ConstructName (CDK L2 construct)
```

### Key Patterns

```hcl
# Terraform
resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket"
  tags   = { Environment = "prod" }
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration {
    status = "Enabled"
  }
}
```

```typescript
// CDK — consolidated into single L2 construct
const dataBucket = new s3.Bucket(this, 'DataBucket', {
  versioned: true,
});
cdk.Tags.of(dataBucket).add('Environment', 'prod');
```

**Note**: Terraform often requires multiple resources for a single logical entity (e.g., S3 bucket + versioning + encryption + policy). CDK L2 constructs consolidate these into a single construct with properties.

## CDK to Terraform

### Construct to Resource Mapping

CDK L2 constructs may map to **multiple** Terraform resources:

| CDK L2 Construct       | Terraform Resources                                          |
| ---------------------- | ------------------------------------------------------------ |
| `s3.Bucket`            | `aws_s3_bucket` + `aws_s3_bucket_versioning` + `aws_s3_bucket_server_side_encryption_configuration` + ... |
| `lambda.Function`      | `aws_lambda_function` + `aws_iam_role` + `aws_iam_role_policy_attachment` + ... |
| `ec2.Vpc`              | `aws_vpc` + `aws_subnet` (multiple) + `aws_internet_gateway` + `aws_nat_gateway` + ... |
| `ecs.FargateService`   | `aws_ecs_service` + `aws_ecs_task_definition` + `aws_iam_role` + ... |

### Strategy

1. **Synthesize first**: Run `cdk synth` to generate CloudFormation templates
2. **Analyze the CloudFormation output** to understand all generated resources
3. **Map CloudFormation resources to Terraform** using the CloudFormation-to-Terraform patterns above
4. **Simplify**: Look for Terraform modules that can replace verbose resource blocks

## CDK to CloudFormation

### Strategy

1. **Synthesize**: Run `cdk synth` to generate CloudFormation templates directly
2. **Clean up**: Remove CDK metadata, bootstrap references, and CDK-specific constructs
3. **Parameterize**: Replace hardcoded values with CloudFormation Parameters
4. **Validate**: Run `aws cloudformation validate-template` on the output

**Note**: This is the most straightforward conversion since CDK already generates CloudFormation under the hood.

## Common Gotchas

| Issue                              | Mitigation                                                       |
| ---------------------------------- | ---------------------------------------------------------------- |
| **S3 bucket split resources (TF)** | Terraform splits bucket config across multiple resources; CDK/CFN consolidate |
| **IAM implicit roles (CDK)**       | CDK auto-creates IAM roles; extract and map explicitly for TF/CFN |
| **Default security settings**      | CDK L2 constructs add secure defaults; replicate in target       |
| **Cross-stack references**         | Map `Fn::ImportValue`/`CfnOutput` to `data` sources or outputs  |
| **Dynamic naming**                 | CDK generates unique names; decide on naming strategy in target  |
| **Custom resources**               | May need Lambda-backed custom resources in all formats           |
| **Terraform state**                | New Terraform state won't know about existing resources; plan imports |
| **CDK aspects/tags**               | Must be manually replicated as tags in target                    |
