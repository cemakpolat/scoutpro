# ScoutPro — CI/CD & Automation Guide

Automate ScoutPro deployment, seeding, and testing.

---

## Quick CI/CD Setup

ScoutPro is designed to be automated from the command line. All operations use `manage.sh` which returns exit codes for CI/CD pipelines.

---

## GitHub Actions (Example)

### Automated Test Pipeline

Create `.github/workflows/test.yml`:

```yaml
name: Test & Seed ScoutPro

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      docker:
        image: docker:latest
        options: --privileged

    steps:
      - uses: actions/checkout@v3

      - name: Install Docker Compose
        run: |
          curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
          chmod +x /usr/local/bin/docker-compose

      - name: Start Services
        run: ./manage.sh start
        timeout-minutes: 2

      - name: Seed Data
        run: ./manage.sh seed
        timeout-minutes: 15

      - name: Validate Data
        run: ./manage.sh validate

      - name: Check API Health
        run: |
          sleep 2
          curl -f http://localhost:3001/api/players?limit=1 || exit 1
```

---

## GitLab CI (Example)

Create `.gitlab-ci.yml`:

```yaml
stages:
  - build
  - test
  - deploy

variables:
  DOCKER_DRIVER: overlay2

test_scoutpro:
  stage: test
  image: docker:latest
  services:
    - docker:dind

  script:
    - docker-compose up -d
    - sleep 30
    - ./manage.sh status
    - ./manage.sh seed
    - ./manage.sh validate

  timeout: 20 minutes
  only:
    - main
```

---

## Jenkins (Example)

Create `Jenkinsfile`:

```groovy
pipeline {
    agent any

    environment {
        DOCKER_COMPOSE = 'docker-compose -f docker-compose.yml'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Start Services') {
            steps {
                sh './manage.sh start'
                sh 'sleep 30'
            }
        }

        stage('Seed Data') {
            steps {
                sh './manage.sh seed'
            }
        }

        stage('Validate') {
            steps {
                sh './manage.sh validate'
                sh 'curl -f http://localhost:3001/api/players?limit=1'
            }
        }

        stage('Test') {
            steps {
                sh 'npm run test'
            }
        }
    }

    post {
        always {
            sh './manage.sh clean'
        }
    }
}
```

---

## Docker-Based Automation

### Build & Push Docker Image

```bash
# Build the image
docker build -t myregistry/scoutpro:latest .

# Push to registry
docker push myregistry/scoutpro:latest
```

### Run in Kubernetes

Create `kubernetes/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scoutpro-api-gateway
spec:
  replicas: 1
  selector:
    matchLabels:
      app: scoutpro-api-gateway
  template:
    metadata:
      labels:
        app: scoutpro-api-gateway
    spec:
      containers:
      - name: api-gateway
        image: scoutpro:latest
        ports:
        - containerPort: 3001
        env:
        - name: MONGODB_URL
          value: "mongodb://mongo:27017/scoutpro"
```

---

## Automated Seeding Script

For automated deployments, create a seeding script:

```bash
#!/bin/bash
# scripts/deploy-and-seed.sh

set -e

echo "🚀 Starting ScoutPro deployment..."

# Wait for Docker to be ready
max_retries=30
retries=0
while ! docker ps > /dev/null 2>&1; do
  if [ $retries -eq $max_retries ]; then
    echo "❌ Docker not available after $max_retries retries"
    exit 1
  fi
  echo "⏳ Waiting for Docker... ($retries/$max_retries)"
  sleep 1
  retries=$((retries + 1))
done

echo "✅ Docker is ready"

# Start services
echo "🔧 Starting services..."
./manage.sh start

# Verify all services are healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30
./manage.sh status || exit 1

# Seed data
echo "🌱 Seeding data..."
./manage.sh seed || exit 1

# Validate
echo "✓ Validating..."
./manage.sh validate || exit 1

echo "✅ ScoutPro is ready!"
echo "   Frontend: http://localhost:5173"
echo "   API: http://localhost:3001/api"
```

Run it:
```bash
chmod +x scripts/deploy-and-seed.sh
./scripts/deploy-and-seed.sh
```

---

## Environment-Specific Configs

### Development

```bash
#!/bin/bash
# scripts/deploy-dev.sh

export LOG_LEVEL=DEBUG
export DATA_ROOT=./data/opta/2019

./manage.sh start
./manage.sh seed
```

### Staging

```bash
#!/bin/bash
# scripts/deploy-staging.sh

export LOG_LEVEL=INFO
export MONGODB_URL=mongodb://root:pass@staging-mongo:27017/scoutpro

./manage.sh start
./manage.sh seed
./manage.sh validate
```

### Production

```bash
#!/bin/bash
# scripts/deploy-production.sh

export LOG_LEVEL=WARN
export MONGODB_URL=mongodb://root:${MONGO_PASS}@prod-mongo:27017/scoutpro
export OPTA_API_KEY=${OPTA_KEY}

./manage.sh start
# Note: Don't seed in production; use live data via API
```

---

## Monitoring & Alerting

### Health Check Script

```bash
#!/bin/bash
# scripts/health-check.sh

# Check API health
if ! curl -f http://localhost:3001/api/players?limit=1 > /dev/null 2>&1; then
  echo "❌ API not responding"
  exit 1
fi

# Check database connectivity
if ! docker-compose exec -T mongo mongosh 'mongodb://localhost:27017/scoutpro' --eval 'db.teams.count()' > /dev/null 2>&1; then
  echo "❌ MongoDB not responding"
  exit 1
fi

# Check event counts
events=$(docker-compose exec -T mongo mongosh 'mongodb://localhost:27017/scoutpro' --eval 'db.match_events.count()' 2>/dev/null | grep -oE '[0-9]+$' | head -1)
if [ "$events" -lt 1000 ]; then
  echo "⚠️  Warning: Only $events events in database (expected ~100k)"
fi

echo "✅ All systems healthy"
exit 0
```

Schedule with cron:
```bash
# Check health every 5 minutes
*/5 * * * * /path/to/health-check.sh || send_alert
```

---

## Automated Testing

### Integration Tests

```bash
#!/bin/bash
# scripts/integration-test.sh

echo "Running integration tests..."

# Test 1: Data seeding
echo "Test 1: Data seeding..."
./manage.sh seed || exit 1

# Test 2: API endpoints
echo "Test 2: API endpoints..."
curl -f http://localhost:3001/api/players || exit 1
curl -f http://localhost:3001/api/teams || exit 1
curl -f http://localhost:3001/api/matches || exit 1

# Test 3: Database integrity
echo "Test 3: Database integrity..."
teams=$(docker-compose exec -T mongo mongosh 'mongodb://localhost:27017/scoutpro' \
  --eval 'db.teams.count()' 2>/dev/null | grep -oE '[0-9]+$' | head -1)
[ "$teams" -eq 18 ] || exit 1

# Test 4: Event counts
echo "Test 4: Event counts..."
events=$(docker-compose exec -T mongo mongosh 'mongodb://localhost:27017/scoutpro' \
  --eval 'db.match_events.count()' 2>/dev/null | grep -oE '[0-9]+$' | head -1)
[ "$events" -gt 90000 ] || exit 1

echo "✅ All integration tests passed"
```

---

## Cleanup & Teardown

### Post-Deployment Cleanup

```bash
#!/bin/bash
# scripts/cleanup.sh

echo "Cleaning up..."

# Stop services
./manage.sh stop

# Optional: Full reset
# ./manage.sh clean

# Remove temporary files
rm -rf /tmp/scoutpro-*

echo "✅ Cleanup complete"
```

---

## Exit Codes Reference

Use these in CI/CD conditions:

```bash
./manage.sh start
if [ $? -eq 0 ]; then
  echo "✅ Services started"
else
  echo "❌ Failed to start services"
  exit 1
fi

./manage.sh validate
if [ $? -eq 0 ]; then
  echo "✅ Data validated"
else
  echo "❌ Data validation failed"
  exit 1
fi
```

| Exit Code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | Failure |
| 127 | Command not found |

---

## Example Full Pipeline

```bash
#!/bin/bash
# .github/scripts/deploy.sh

set -e  # Exit on any error

echo "🚀 ScoutPro CI/CD Pipeline"

# 1. Start
echo "Step 1/4: Starting services..."
./manage.sh start
sleep 30

# 2. Seed
echo "Step 2/4: Seeding data..."
./manage.sh seed

# 3. Validate
echo "Step 3/4: Validating..."
./manage.sh validate

# 4. Test
echo "Step 4/4: Running tests..."
npm run test

echo "✅ Pipeline complete!"
exit 0
```

---

## Summary

| Tool | File | Command |
|------|------|---------|
| GitHub Actions | `.github/workflows/test.yml` | `./manage.sh start && ./manage.sh seed` |
| GitLab CI | `.gitlab-ci.yml` | Same |
| Jenkins | `Jenkinsfile` | Same |
| Docker | `docker-compose.yml` | `docker-compose up -d` |
| Kubernetes | `k8s/deployment.yaml` | `kubectl apply -f k8s/` |

All use the same underlying commands: `./manage.sh start`, `./manage.sh seed`, `./manage.sh validate`.

---

## Next Steps

- Review [MANAGE_COMMANDS.md](MANAGE_COMMANDS.md) for all available commands
- Check [STATISTICS_OPERATIONS.md](STATISTICS_OPERATIONS.md) for data operations
- Set up your preferred CI/CD platform above
