#!/bin/bash
# ScoutPro Development Startup Script
# Usage: ./start-dev.sh [--seed] [--reset]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     ScoutPro Development Server       ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════╝${NC}"
echo ""

SEED=false
RESET=false

for arg in "$@"; do
  case $arg in
    --seed) SEED=true ;;
    --reset) RESET=true; SEED=true ;;
    --help)
      echo "Usage: ./start-dev.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --seed    Seed the database with sample data"
      echo "  --reset   Reset everything (remove containers, reinstall, reseed)"
      echo "  --help    Show this help message"
      exit 0
      ;;
  esac
done

# Step 1: Start MongoDB
echo -e "${YELLOW}[1/5]${NC} Starting MongoDB..."
if docker ps --format '{{.Names}}' | grep -q 'scoutpro-mongo'; then
  echo -e "  ${GREEN}✓${NC} MongoDB already running"
else
  if [ "$RESET" = true ]; then
    docker-compose down -v 2>/dev/null || true
  fi
  docker-compose up -d mongo 2>&1 | grep -v "variable is not set"
  echo -e "  ${GREEN}✓${NC} MongoDB started"
  echo -e "  ${YELLOW}⏳${NC} Waiting for MongoDB to be ready..."
  sleep 8
fi

# Verify MongoDB is accessible
for i in {1..10}; do
  if docker exec scoutpro-mongo mongosh --eval "db.runCommand({ ping: 1 })" --quiet 2>/dev/null | grep -q "ok"; then
    echo -e "  ${GREEN}✓${NC} MongoDB is ready"
    break
  fi
  if [ $i -eq 10 ]; then
    echo -e "  ${RED}✗${NC} MongoDB not ready after 30s. Check: docker logs scoutpro-mongo"
    exit 1
  fi
  sleep 3
done

# Step 2: Install gateway dependencies
echo -e "${YELLOW}[2/5]${NC} Installing API Gateway dependencies..."
cd services/api-gateway
if [ ! -d "node_modules" ] || [ "$RESET" = true ]; then
  npm install --silent 2>&1 | tail -1
  echo -e "  ${GREEN}✓${NC} Dependencies installed"
else
  echo -e "  ${GREEN}✓${NC} Dependencies already installed"
fi
cd "$SCRIPT_DIR"

# Step 3: Seed database (if requested or first run)
if [ "$SEED" = true ]; then
  echo -e "${YELLOW}[3/5]${NC} Seeding database..."
  cd services/api-gateway
  node src/seed.js 2>&1 | grep -E "✅|✨|👤|❌"
  cd "$SCRIPT_DIR"
else
  # Check if database has data
  HAS_DATA=$(docker exec scoutpro-mongo mongosh --eval "db.getSiblingDB('scoutpro').players.countDocuments()" --quiet 2>/dev/null || echo "0")
  if [ "$HAS_DATA" = "0" ] || [ -z "$HAS_DATA" ]; then
    echo -e "${YELLOW}[3/5]${NC} Seeding database (first run)..."
    cd services/api-gateway
    node src/seed.js 2>&1 | grep -E "✅|✨|👤|❌"
    cd "$SCRIPT_DIR"
  else
    echo -e "${YELLOW}[3/5]${NC} Database already has data (${HAS_DATA} players). Use --seed to refresh."
  fi
fi

# Step 4: Start API Gateway
echo -e "${YELLOW}[4/5]${NC} Starting API Gateway..."
# Kill any existing gateway process
lsof -ti:3001 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 1

cd services/api-gateway
node src/index.js &
GATEWAY_PID=$!
cd "$SCRIPT_DIR"

# Wait for gateway to be ready
for i in {1..15}; do
  if curl -s http://localhost:3001/health >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} API Gateway running on http://localhost:3001"
    break
  fi
  if [ $i -eq 15 ]; then
    echo -e "  ${RED}✗${NC} Gateway failed to start"
    exit 1
  fi
  sleep 1
done

# Step 5: Start Frontend Dev Server
echo -e "${YELLOW}[5/5]${NC} Starting Frontend Dev Server..."
cd frontend
if [ ! -d "node_modules" ] || [ "$RESET" = true ]; then
  npm install --silent 2>&1 | tail -1
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ScoutPro is starting!                            ║${NC}"
echo -e "${GREEN}║                                                   ║${NC}"
echo -e "${GREEN}║  🌐 Frontend:  http://localhost:5173               ║${NC}"
echo -e "${GREEN}║  🔌 API:       http://localhost:3001/api           ║${NC}"
echo -e "${GREEN}║  � WebSocket: ws://localhost:3001/ws              ║${NC}"
echo -e "${GREEN}║  �💚 Health:    http://localhost:3001/health        ║${NC}"
echo -e "${GREEN}║  🗄️  MongoDB:   localhost:27017                    ║${NC}"
echo -e "${GREEN}║                                                   ║${NC}"
echo -e "${GREEN}║  Admin login:  admin@scoutpro.com / admin123      ║${NC}"
echo -e "${GREEN}║                                                   ║${NC}"
echo -e "${GREEN}║  Press Ctrl+C to stop all services                ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"
echo ""

# Trap Ctrl+C to clean up
cleanup() {
  echo -e "\n${YELLOW}Shutting down...${NC}"
  kill $GATEWAY_PID 2>/dev/null || true
  echo -e "${GREEN}✓${NC} API Gateway stopped"
  echo -e "${YELLOW}Note: MongoDB container still running. Stop with: docker-compose down${NC}"
  exit 0
}
trap cleanup SIGINT SIGTERM

# Start Vite dev server (foreground - will catch Ctrl+C)
npx vite --port 5173 --host
