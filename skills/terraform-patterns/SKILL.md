---
name: terraform-patterns
description: Terraform infrastructure-as-code patterns and best practices. Use when writing Terraform configs, managing cloud infrastructure, or implementing IaC workflows.
---

# Terraform Patterns

Write clean, maintainable, and secure Terraform configurations.

## Project Structure

```
terraform/
├── modules/
│   ├── networking/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── compute/
│   └── database/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   └── production/
└── modules.tf
```

## Best Practices

### State Management
- Always use remote state (S3, GCS, Azure Blob)
- Enable state locking (DynamoDB for AWS)
- Use separate state files per environment
- Never commit state files to git
- Enable state file encryption

### Variables
- Define types and descriptions for all variables
- Use validation blocks for constraints
- Provide sensible defaults where appropriate
- Use terraform.tfvars for environment-specific values
- Never hardcode secrets — use vault or SSM parameters

### Modules
- One module per logical resource group
- Keep modules small and focused
- Version pin module sources
- Document inputs, outputs, and usage examples
- Use count/for_each for conditional resources

### Naming
- Use consistent naming: `{project}-{environment}-{resource}`
- Tag all resources: project, environment, team, managed-by
- Use locals for computed names to ensure consistency

## Security

- [ ] No secrets in terraform files or state
- [ ] S3 backend bucket has versioning and encryption
- [ ] IAM roles follow least privilege
- [ ] Security groups restrict ingress to needed ports
- [ ] Encryption enabled for all data stores
- [ ] VPC flow logs enabled
- [ ] CloudTrail/audit logging enabled

## Common Patterns

### Conditional Resource Creation
```hcl
resource "aws_instance" "bastion" {
  count = var.enable_bastion ? 1 : 0
  # ...
}
```

### Dynamic Blocks
```hcl
dynamic "ingress" {
  for_each = var.allowed_ports
  content {
    from_port   = ingress.value
    to_port     = ingress.value
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

### Data Sources for Existing Resources
```hcl
data "aws_vpc" "existing" {
  tags = { Name = "main-vpc" }
}

resource "aws_subnet" "new" {
  vpc_id = data.aws_vpc.existing.id
  # ...
}
```

## Workflow

1. `terraform fmt` — format code
2. `terraform validate` — check syntax
3. `terraform plan` — preview changes
4. Code review the plan output
5. `terraform apply` — apply changes
6. Verify in cloud console
