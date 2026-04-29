#!/bin/bash

# ScoutPro - Backend Startup Script
# Starts all backend services in the correct order

set -e

echo "========================================="
echo "ScoutPro - Starting Backend Services"
echo "========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a service is healthy
wait_for_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    echo -n "Waiting for $service to be healthy..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo -e " ${GREEN}✓ Ready${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo -e " ${RED}✗ Failed${NC}"
    return 1
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi

echo -e "${BLUE}Step 1/5: Starting Infrastructure Services${NC}"
echo "-------------------------------------------"

# Start infrastructure (databases, message queue)
echo "Starting MongoDB, Redis, Kafka, Elasticsearch..."
docker-compose up -d mongo redis zookeeper kafka elasticsearch timescaledb

echo ""
echo "Waiting for infrastructure to be ready (30 seconds)..."
sleep 30

# Verify infrastructure
echo ""
echo "Verifying infrastructure..."
wait_for_service "MongoDB" "http://localhost:27017" || echo "MongoDB may still be starting..."
wait_for_service "Redis" "http://localhost:6379" || echo "Redis may still be starting..."
wait_for_service "Elasticsearch" "http://localhost:9200"

echo ""
echo -e "${GREEN}Infrastructure started successfully!${NC}"

echo ""
echo -e "${BLUE}Step 2/5: Creating Kafka Topics${NC}"
echo "-------------------------------------------"

# Check if topics script exists
if [ -f "./scripts/create-kafka-topics.sh" ]; then
    chmod +x ./scripts/create-kafka-topics.sh
    ./scripts/create-kafka-topics.sh
else
    echo -e "${YELLOW}Warning: Kafka topics script not found${NC}"
    echo "Topics will be auto-created on first use"
fi

echo ""
echo -e "${BLUE}Step 3/5: Starting Core Microservices${NC}"
echo "-------------------------------------------"

# Start core services
echo "Starting Player, Team, and Match services..."
docker-compose up -d player-service team-service match-service

echo "Waiting for services to initialize (15 seconds)..."
sleep 15

# Verify services
echo ""
echo "Verifying services..."
wait_for_service "Player Service" "http://localhost:8001/health"
wait_for_service "Team Service" "http://localhost:8002/health"
wait_for_service "Match Service" "http://localhost:8003/health"

echo ""
echo -e "${GREEN}Core services started successfully!${NC}"

echo ""
echo -e "${BLUE}Step 4/5: Starting Supporting Services${NC}"
echo "-------------------------------------------"

# Start supporting services
echo "Starting Statistics, Data Sync, ML, Search, Notification, Report, Export, and Analytics services..."
docker-compose up -d statistics-service data-sync-service ml-service search-service notification-service report-service export-service analytics-service

echo "Starting WebSocket server..."
docker-compose up -d websocket-server

echo "Waiting for services to initialize (10 seconds)..."
sleep 10

# Verify services
echo ""
echo "Verifying services..."
wait_for_service "Statistics Service" "http://localhost:8004/health"
wait_for_service "Data Sync Service" "http://localhost:8006/health" || echo "Data Sync Service may not expose /health"
wait_for_service "ML Service" "http://localhost:8005/health"
wait_for_service "Search Service" "http://localhost:8007/health"
wait_for_service "Notification Service" "http://localhost:8008/health"
wait_for_service "Report Service" "http://localhost:8009/health" || echo "Report Service may not expose /health"
wait_for_service "Export Service" "http://localhost:8010/health" || echo "Export Service may not expose /health"
wait_for_service "Analytics Service" "http://localhost:8012/health" || echo "Analytics Service may not expose /health"
wait_for_service "WebSocket Server" "http://localhost:8080/health"

echo ""
echo -e "${GREEN}Supporting services started successfully!${NC}"

echo ""
echo -e "${BLUE}Step 5/5: Starting Monitoring & Gateway${NC}"
echo "-------------------------------------------"

# Start monitoring stack
echo "Starting Prometheus, Grafana, and Jaeger..."
docker-compose up -d prometheus grafana jaeger kafka-ui

# Start API gateway
echo "Starting NGINX API Gateway..."
docker-compose up -d nginx

echo "Waiting for monitoring services (5 seconds)..."
sleep 5

echo ""
echo -e "${GREEN}Monitoring and gateway started successfully!${NC}"

echo ""
echo "========================================="
echo "Backend Startup Complete!"
echo "========================================="
echo ""

# Show service status
echo -e "${BLUE}Service Status:${NC}"
docker-compose ps

echo ""
echo "========================================="
echo "Access Points"
echo "========================================="
echo ""
echo -e "${GREEN}Core Services:${NC}"
echo "  • API Gateway:        http://localhost"
echo "  • Player Service:     http://localhost:8001"
echo "  • Team Service:       http://localhost:8002"
echo "  • Match Service:      http://localhost:8003"
echo "  • WebSocket Server:   ws://localhost:8080"
echo ""
echo -e "${GREEN}Monitoring & Tools:${NC}"
echo "  • Grafana:            http://localhost:3000 (admin/admin123)"
echo "  • Prometheus:         http://localhost:9090"
echo "  • Jaeger Tracing:     http://localhost:16686"
echo "  • Kafka UI:           http://localhost:8090"
echo ""
echo -e "${GREEN}API Documentation:${NC}"
echo "  • Player API Docs:    http://localhost:8001/docs"
echo "  • Team API Docs:      http://localhost:8002/docs"
echo "  • Match API Docs:     http://localhost:8003/docs"
echo ""
echo "========================================="
echo "Next Steps"
echo "========================================="
echo ""
echo "1. Test API Gateway:"
echo "   ${BLUE}curl http://localhost/health${NC}"
echo ""
echo "2. Test Player Service:"
echo "   ${BLUE}curl http://localhost/api/players${NC}"
echo ""
echo "3. Start Frontend:"
echo "   ${BLUE}npm run dev${NC}"
echo ""
echo "4. Update frontend .env:"
echo "   ${BLUE}VITE_USE_MOCK_DATA=false${NC}"
echo ""
echo "5. View logs:"
echo "   ${BLUE}docker-compose logs -f player-service${NC}"
echo ""
echo "========================================="
echo -e "${GREEN}All systems ready! 🚀${NC}"
echo "========================================="
echo ""
