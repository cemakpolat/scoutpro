# Infrastructure as Code (IaC)

This directory contains infrastructure configuration for deploying ScoutPro to various cloud providers.

## Directory Structure

```
infrastructure/
├── terraform/              # Terraform configurations
│   ├── modules/           # Reusable Terraform modules
│   └── environments/      # Environment-specific configs
│       ├── dev/
│       ├── staging/
│       └── prod/
├── kubernetes/            # Kubernetes manifests
│   ├── base/             # Base configurations
│   └── overlays/         # Environment-specific overlays
│       ├── dev/
│       ├── staging/
│       └── prod/
├── cloudformation/        # AWS CloudFormation templates
└── helm/                  # Helm charts
```

## Quick Start

### Terraform (AWS)

```bash
cd terraform/environments/dev
terraform init
terraform plan
terraform apply
```

### Kubernetes

```bash
cd kubernetes
kubectl apply -k overlays/dev
```

### CloudFormation

```bash
cd cloudformation
aws cloudformation create-stack \
  --stack-name scoutpro-dev \
  --template-body file://main.yml
```

## Supported Cloud Providers

- **AWS**: ECS Fargate, EKS, RDS, MSK, DocumentDB
- **Azure**: AKS, Cosmos DB, Event Hubs
- **GCP**: GKE, Firestore, Cloud Pub/Sub

## Documentation

See individual README files in each subdirectory for detailed instructions.
