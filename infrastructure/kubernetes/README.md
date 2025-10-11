# Kubernetes Deployment

## Overview

Kubernetes manifests for deploying ScoutPro to any Kubernetes cluster (EKS, AKS, GKE, or self-hosted).

## Prerequisites

- kubectl
- kustomize
- Helm 3+ (optional)
- Access to a Kubernetes cluster

## Structure

```
kubernetes/
├── base/                      # Base configurations
│   ├── deployments/          # Deployment manifests
│   ├── services/             # Service manifests
│   ├── configmaps/           # ConfigMaps
│   ├── secrets/              # Secrets (encrypted)
│   └── kustomization.yaml
└── overlays/                  # Environment-specific
    ├── dev/
    ├── staging/
    └── prod/
```

## Quick Start

### 1. Deploy to Development

```bash
kubectl apply -k overlays/dev
```

### 2. Deploy to Production

```bash
kubectl apply -k overlays/prod
```

### 3. Check Status

```bash
kubectl get pods -n scoutpro
kubectl get services -n scoutpro
```

## Services

All services will be deployed:
- player-service
- team-service
- match-service
- statistics-service
- ml-service
- websocket-server
- And supporting services

## Ingress

NGINX Ingress Controller routes traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: scoutpro-ingress
spec:
  rules:
  - host: api.scoutpro.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nginx-gateway
            port:
              number: 80
```

## Auto-Scaling

Horizontal Pod Autoscaler (HPA):

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: player-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: player-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Secrets Management

Use Sealed Secrets or External Secrets Operator:

```bash
# Using kubectl
kubectl create secret generic db-secrets \
  --from-literal=mongodb-url=mongodb://... \
  --from-literal=redis-url=redis://... \
  -n scoutpro
```

## Monitoring

Deploy Prometheus Stack:

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

## Troubleshooting

```bash
# Check pod logs
kubectl logs -f deployment/player-service -n scoutpro

# Describe pod
kubectl describe pod <pod-name> -n scoutpro

# Get events
kubectl get events -n scoutpro --sort-by='.lastTimestamp'
```
