# Terraform Infrastructure

## Overview

Terraform configurations for deploying ScoutPro to AWS, Azure, and GCP.

## Prerequisites

- Terraform 1.5+
- AWS CLI (for AWS deployment)
- Azure CLI (for Azure deployment)
- gcloud CLI (for GCP deployment)

## Structure

```
terraform/
├── modules/                    # Reusable modules
│   ├── ecs-service/           # ECS service module
│   ├── rds/                   # RDS database module
│   ├── kafka/                 # MSK (Kafka) module
│   └── networking/            # VPC, subnets, etc.
└── environments/
    ├── dev/                   # Development environment
    ├── staging/               # Staging environment
    └── prod/                  # Production environment
```

## Usage

### 1. Configure AWS Credentials

```bash
aws configure
```

### 2. Initialize Terraform

```bash
cd environments/dev
terraform init
```

### 3. Plan Deployment

```bash
terraform plan -out=tfplan
```

### 4. Apply Configuration

```bash
terraform apply tfplan
```

### 5. Destroy Resources

```bash
terraform destroy
```

## Environment Variables

Create `terraform.tfvars` in each environment:

```hcl
# Development
environment = "dev"
region      = "us-east-1"
vpc_cidr    = "10.0.0.0/16"

# Service configuration
player_service_replicas = 2
team_service_replicas   = 2
match_service_replicas  = 2

# Database
rds_instance_class = "db.t3.small"
mongo_instance_class = "db.t3.medium"
```

## Modules

### ECS Service Module

```hcl
module "player_service" {
  source = "../../modules/ecs-service"

  service_name = "player-service"
  image        = "scoutpro/player-service:latest"
  port         = 8000
  replicas     = var.player_service_replicas
  vpc_id       = module.networking.vpc_id
  subnet_ids   = module.networking.private_subnet_ids
}
```

## Remote State

Configure S3 backend:

```hcl
terraform {
  backend "s3" {
    bucket = "scoutpro-terraform-state"
    key    = "dev/terraform.tfstate"
    region = "us-east-1"
  }
}
```

## Cost Estimation

Use `terraform cost` or AWS Cost Calculator to estimate monthly costs.

**Estimated Monthly Cost (Production)**:
- ECS Fargate: $200-500
- RDS: $100-300
- MSK (Kafka): $500-1000
- DocumentDB: $200-400
- **Total**: $1000-2200/month
