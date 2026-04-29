#!/bin/bash
# ScoutPro Local Development Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════╗"
echo "║       ScoutPro - Local Development Environment       ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp .env.backend.example .env
    echo -e "${RED}❌ Please configure .env file with your API keys before starting${NC}"
    echo -e "${BLUE}📝 Edit .env file and run this script again${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Create required directories
echo -e "${BLUE}📁 Creating required directories...${NC}"
mkdir -p {services,monitoring,logging,nginx,init-scripts}
mkdir -p monitoring/{prometheus,grafana/{dashboards,datasources}}
mkdir -p logging

# Create init scripts if they don't exist
if [ ! -f init-scripts/init-mongo.js ]; then
    echo -e "${BLUE}📝 Creating MongoDB init script...${NC}"
    cat > init-scripts/init-mongo.js << 'EOF'
db = db.getSiblingDB('scoutpro');

// Create collections
db.createCollection('players');
db.createCollection('teams');
db.createCollection('matches');
db.createCollection('statistics');

// Create indexes
db.players.createIndex({ "uID": 1 }, { unique: true });
db.players.createIndex({ "name": "text" });
db.teams.createIndex({ "uID": 1 }, { unique: true });
db.matches.createIndex({ "uID": 1 }, { unique: true });
db.matches.createIndex({ "date": 1 });

print('MongoDB initialization completed');
EOF
fi

if [ ! -f init-scripts/init-timescale.sql ]; then
    echo -e "${BLUE}📝 Creating TimescaleDB init script...${NC}"
    cat > init-scripts/init-timescale.sql << 'EOF'
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create MLflow database
CREATE DATABASE mlflow;

-- Create tables for time-series data
CREATE TABLE IF NOT EXISTS match_stats (
    time TIMESTAMPTZ NOT NULL,
    match_id VARCHAR(50) NOT NULL,
    minute INTEGER,
    home_possession FLOAT,
    away_possession FLOAT,
    home_xg FLOAT,
    away_xg FLOAT,
    home_shots INTEGER,
    away_shots INTEGER,
    metadata JSONB
);

SELECT create_hypertable('match_stats', 'time', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS player_performance (
    time TIMESTAMPTZ NOT NULL,
    player_id VARCHAR(50) NOT NULL,
    match_id VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100),
    metric_value FLOAT,
    metadata JSONB
);

SELECT create_hypertable('player_performance', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_match_stats_match_id ON match_stats (match_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_player_performance_player_id ON player_performance (player_id, time DESC);

-- Create retention policies (keep 1 year)
SELECT add_retention_policy('match_stats', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('player_performance', INTERVAL '1 year', if_not_exists => TRUE);
EOF
fi

# Create Prometheus config if it doesn't exist
if [ ! -f monitoring/prometheus.yml ]; then
    echo -e "${BLUE}📝 Creating Prometheus config...${NC}"
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'player-service'
    static_configs:
      - targets: ['player-service:8000']
    metrics_path: '/metrics'

  - job_name: 'team-service'
    static_configs:
      - targets: ['team-service:8000']

  - job_name: 'match-service'
    static_configs:
      - targets: ['match-service:8000']

  - job_name: 'statistics-service'
    static_configs:
      - targets: ['statistics-service:8000']

  - job_name: 'ml-service'
    static_configs:
      - targets: ['ml-service:8000']

  - job_name: 'kafka'
    static_configs:
      - targets: ['kafka:9092']
EOF
fi

# Create Logstash config if it doesn't exist
if [ ! -f logging/logstash.conf ]; then
    echo -e "${BLUE}📝 Creating Logstash config...${NC}"
    cat > logging/logstash.conf << 'EOF'
input {
  beats {
    port => 5044
  }
  tcp {
    port => 5000
    codec => json
  }
}

filter {
  if [service] {
    mutate {
      add_field => { "[@metadata][service]" => "%{service}" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch-logs:9200"]
    index => "scoutpro-logs-%{+YYYY.MM.dd}"
  }
  stdout { codec => rubydebug }
}
EOF
fi

# Create Nginx config if it doesn't exist
if [ ! -f nginx/nginx.conf ]; then
    echo -e "${BLUE}📝 Creating Nginx config...${NC}"
    cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream player_service {
        server player-service:8000;
    }

    upstream team_service {
        server team-service:8000;
    }

    upstream match_service {
        server match-service:8000;
    }

    upstream websocket_server {
        server websocket-server:8080;
    }

    server {
        listen 80;
        server_name localhost;

        # Player Service
        location /api/v2/players {
            proxy_pass http://player_service;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Team Service
        location /api/v2/teams {
            proxy_pass http://team_service;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Match Service
        location /api/v2/matches {
            proxy_pass http://match_service;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # WebSocket
        location /ws {
            proxy_pass http://websocket_server;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }
    }
}
EOF
fi

# Function to wait for service
wait_for_service() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=0

    echo -ne "${YELLOW}⏳ Waiting for $service to be ready...${NC}"
    while [ $attempt -lt $max_attempts ]; do
        if nc -z localhost $port 2>/dev/null; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
        echo -n "."
    done
    echo -e " ${RED}✗${NC}"
    return 1
}

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose down 2>/dev/null || true

# Build services
echo -e "${BLUE}📦 Building services...${NC}"
docker-compose build --parallel

# Start infrastructure first
echo -e "${BLUE}🔧 Starting infrastructure (databases, message queue)...${NC}"
docker-compose up -d mongo timescaledb redis zookeeper kafka elasticsearch minio

# Wait for databases
wait_for_service "MongoDB" 27017
wait_for_service "TimescaleDB" 5432
wait_for_service "Redis" 6379
wait_for_service "Kafka" 9092
wait_for_service "Elasticsearch" 9200
wait_for_service "MinIO" 9000

# Start MLflow
echo -e "${BLUE}🤖 Starting MLflow...${NC}"
docker-compose up -d mlflow
sleep 5

# Start all microservices
echo -e "${BLUE}🚀 Starting microservices...${NC}"
docker-compose up -d player-service team-service match-service statistics-service data-sync-service ml-service
docker-compose up -d live-ingestion-service search-service notification-service report-service export-service analytics-service websocket-server

# Start monitoring stack
echo -e "${BLUE}📊 Starting monitoring stack...${NC}"
docker-compose up -d prometheus grafana jaeger

# Start logging stack
echo -e "${BLUE}📝 Starting logging stack...${NC}"
docker-compose up -d elasticsearch-logs logstash kibana

# Start API Gateway
echo -e "${BLUE}🌐 Starting API Gateway...${NC}"
docker-compose up -d nginx kafka-ui

echo ""
echo -e "${GREEN}✅ ScoutPro is up and running!${NC}"
echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗"
echo "║              Access Points                            ║"
echo "╠═══════════════════════════════════════════════════════╣"
echo -e "║ ${GREEN}🌐 API Gateway:${NC}       http://localhost:80              ║"
echo -e "║ ${GREEN}📊 Grafana:${NC}           http://localhost:3000            ║"
echo -e "║                       ${YELLOW}(admin/admin123)${NC}                ║"
echo -e "║ ${GREEN}🔍 Jaeger:${NC}            http://localhost:16686           ║"
echo -e "║ ${GREEN}📨 Kafka UI:${NC}          http://localhost:8090            ║"
echo -e "║ ${GREEN}📈 Prometheus:${NC}        http://localhost:9090            ║"
echo -e "║ ${GREEN}📝 Kibana:${NC}            http://localhost:5601            ║"
echo -e "║ ${GREEN}🤖 MLflow:${NC}            http://localhost:5000            ║"
echo -e "║ ${GREEN}💾 MinIO Console:${NC}     http://localhost:9001            ║"
echo -e "║                       ${YELLOW}(minioadmin/minioadmin123)${NC}      ║"
echo "╠═══════════════════════════════════════════════════════╣"
echo -e "║ ${GREEN}📦 Services:${NC}                                           ║"
echo -e "║   Player Service:     http://localhost:8001           ║"
echo -e "║   Team Service:       http://localhost:8002           ║"
echo -e "║   Match Service:      http://localhost:8003           ║"
echo -e "║   Statistics Service: http://localhost:8004           ║"
echo -e "║   ML Service:         http://localhost:8005           ║"
echo -e "║   Live Ingestion:     http://localhost:8006           ║"
echo -e "║   Search Service:     http://localhost:8007           ║"
echo -e "║   WebSocket Server:   http://localhost:8080           ║"
echo "╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📝 Useful commands:${NC}"
echo -e "  ${GREEN}View logs:${NC}        docker-compose logs -f [service-name]"
echo -e "  ${GREEN}Stop all:${NC}         docker-compose down"
echo -e "  ${GREEN}Restart service:${NC}  docker-compose restart [service-name]"
echo -e "  ${GREEN}View status:${NC}      docker-compose ps"
echo ""
