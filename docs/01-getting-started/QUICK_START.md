# ScoutPro - Quick Start Guide

**Get your full-stack application running in 5 minutes!**

---

## 🚀 Quick Start (2 Options)

### Option 1: Frontend Only (Mock Data)
**Best for**: UI development, no backend needed

```bash
# Start frontend with mock data
npm run dev

# Access at: http://localhost:5173
```

### Option 2: Full Stack (Real Backend)
**Best for**: Full integration testing

```bash
# 1. Start backend services
docker-compose up -d

# 2. Create Kafka topics (one-time setup)
./scripts/create-kafka-topics.sh

# 3. Update frontend config
#    Edit .env and change:
#    VITE_USE_MOCK_DATA=false

# 4. Start frontend
npm run dev

# Access at: http://localhost:5173
```

---

## 📋 Prerequisites

### Required
- **Node.js** 18+ and npm
- **Docker** and Docker Compose
- **8GB+ RAM** available for Docker

### Optional
- Opta API credentials (for live data)
- StatsBomb API credentials (for enrichment)

---

## 🔧 Step-by-Step Setup

### Step 1: Clone & Install

```bash
# Clone repository
git clone <repository-url>
cd scoutpro

# Install frontend dependencies
npm install

# Copy environment files
cp .env.example .env
```

### Step 2: Start Backend Services

```bash
# Start all services (takes 30-60 seconds)
docker-compose up -d

# Check status
docker-compose ps

# You should see all services "Up" and "healthy"
```

**Services Started**:

**Application Services (13)**:
- ✅ Player Service (port 8001)
- ✅ Team Service (port 8002)
- ✅ Match Service (port 8003)
- ✅ Statistics Service (port 8004)
- ✅ ML Service (port 8005)
- ✅ Live Ingestion Service (port 8006)
- ✅ Search Service (port 8007)
- ✅ Notification Service (port 8008)
- ✅ **Report Service** (port 8009) ← NEW
- ✅ **Export Service** (port 8010) ← NEW
- ✅ **Video Service** (port 8011) ← NEW
- ✅ **Analytics Service** (port 8012) ← NEW
- ✅ WebSocket Server (port 8080)

**Infrastructure**:
- ✅ NGINX Gateway (port 80)
- ✅ MongoDB (port 27017)
- ✅ Redis (port 6379)
- ✅ Kafka + Zookeeper (ports 9092, 2181)
- ✅ Elasticsearch (port 9200)
- ✅ TimescaleDB (port 5432)
- ✅ MinIO (port 9000)

**Monitoring**:
- ✅ Prometheus (port 9090)
- ✅ Grafana (port 3000)
- ✅ Jaeger (port 16686)
- ✅ Kafka UI (port 8090)

### Step 3: Create Kafka Topics

```bash
# Make script executable (first time only)
chmod +x scripts/create-kafka-topics.sh

# Create all topics
./scripts/create-kafka-topics.sh

# Expected output:
# ✅ Creating topic: player.events... Created
# ✅ Creating topic: team.events... Created
# ✅ Creating topic: match.events... Created
# ... (30+ topics)
```

**Topics Created**:
- Core: `player.events`, `team.events`, `match.events`
- Live: `match.live.updates`, `match.events.stream`
- Stats: `statistics.calculated`, `player.stats.updated`
- ML: `ml.predictions`, `ml.model.trained`
- Search: `search.index.update`
- Notifications: `notifications.send`

### Step 4: Configure Frontend

Edit `.env`:

```env
# For REAL backend
VITE_API_BASE_URL=http://localhost/api
VITE_WS_URL=ws://localhost:8080
VITE_USE_MOCK_DATA=false  # ⬅️ Change this!

# For MOCK data (default)
VITE_USE_MOCK_DATA=true
```

### Step 5: Start Frontend

```bash
# Start development server
npm run dev

# Frontend will start at:
# http://localhost:5173
```

### Step 6: Verify Integration

#### Test Backend APIs

```bash
# Test API Gateway
curl http://localhost/health
# Expected: {"status":"healthy","gateway":"nginx"}

# Test Player Service
curl http://localhost/api/players
# or via direct port:
curl http://localhost:8001/health

# Test Team Service
curl http://localhost/api/teams

# Test Match Service
curl http://localhost/api/matches
```

#### Test WebSocket

```bash
# Install wscat if needed
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8080

# Send subscribe message
> {"type":"subscribe","channel":"match"}

# You should see connection confirmation
```

#### Test Frontend

1. Open http://localhost:5173
2. Open Browser Console (F12)
3. Look for:
   - ✅ `API Response:` logs (if real backend)
   - ✅ `WebSocket connected` (if real backend)
   - ⚠️ `Using mock data` (if mock mode)

---

## 🎯 Quick Health Check

Run this script to check all services:

```bash
#!/bin/bash
# health-check.sh

echo "Checking services..."

# API Gateway
curl -s http://localhost/health | jq .

# Player Service
curl -s http://localhost:8001/health | jq .

# Team Service
curl -s http://localhost:8002/health | jq .

# Match Service
curl -s http://localhost:8003/health | jq .

# WebSocket Server
curl -s http://localhost:8080/health | jq .

# Check Docker containers
docker-compose ps
```

---

## 🐛 Troubleshooting

### Issue: "Cannot connect to backend"

**Symptoms**: Frontend shows errors, API calls fail

**Solution**:
```bash
# 1. Check if backend is running
docker-compose ps

# 2. Check if services are healthy
docker-compose logs player-service
docker-compose logs nginx

# 3. Restart services
docker-compose restart

# 4. Check .env
cat .env | grep VITE_USE_MOCK_DATA
# Should be: false
```

### Issue: "Kafka connection failed"

**Symptoms**: Services start but Kafka warnings in logs

**Solution**:
```bash
# 1. Check Kafka is running
docker-compose ps kafka

# 2. Create topics
./scripts/create-kafka-topics.sh

# 3. Verify topics exist
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# 4. Restart services that need Kafka
docker-compose restart player-service team-service match-service
```

### Issue: "MongoDB connection failed"

**Symptoms**: Services fail to start, "connection refused" errors

**Solution**:
```bash
# 1. Check MongoDB is running
docker-compose ps mongo

# 2. Check MongoDB logs
docker-compose logs mongo

# 3. Restart MongoDB
docker-compose restart mongo

# 4. Wait 10 seconds, then restart services
sleep 10
docker-compose restart player-service team-service
```

### Issue: "Port already in use"

**Symptoms**: Docker compose fails to start

**Solution**:
```bash
# Find what's using the port (e.g., 27017)
lsof -i :27017

# Kill the process or change the port in docker-compose.yml
```

### Issue: "Frontend shows mock data"

**Symptoms**: Data doesn't change, shows sample data

**Solution**:
```bash
# 1. Check .env
cat .env | grep VITE_USE_MOCK_DATA

# 2. Change to false
sed -i '' 's/VITE_USE_MOCK_DATA=true/VITE_USE_MOCK_DATA=false/' .env

# 3. Restart frontend
# Press Ctrl+C to stop npm run dev
npm run dev
```

---

## 📊 Monitoring & Debugging

### Access Monitoring Tools

| Tool | URL | Purpose |
|------|-----|---------|
| **Grafana** | http://localhost:3000 | Metrics dashboards (admin/admin123) |
| **Prometheus** | http://localhost:9090 | Metrics collection |
| **Jaeger** | http://localhost:16686 | Distributed tracing |
| **Kafka UI** | http://localhost:8090 | Kafka topics & messages |
| **API Docs - Player** | http://localhost:8001/docs | Player Service API |
| **API Docs - Team** | http://localhost:8002/docs | Team Service API |
| **API Docs - Match** | http://localhost:8003/docs | Match Service API |
| **API Docs - Statistics** | http://localhost:8004/docs | Statistics Service API |
| **API Docs - ML** | http://localhost:8005/docs | ML Service API |
| **API Docs - Search** | http://localhost:8007/docs | Search Service API |
| **API Docs - Report** | http://localhost:8009/docs | Report Service API (NEW) |
| **API Docs - Export** | http://localhost:8010/docs | Export Service API (NEW) |
| **API Docs - Video** | http://localhost:8011/docs | Video Service API (NEW) |
| **API Docs - Analytics** | http://localhost:8012/docs | Analytics Service API (NEW) |

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f player-service

# Last 100 lines
docker-compose logs --tail=100 player-service

# Filter by error
docker-compose logs player-service | grep ERROR
```

### Check Service Metrics

```bash
# Player Service metrics
curl http://localhost:8001/metrics

# API Gateway metrics
curl http://localhost/metrics

# WebSocket stats
curl http://localhost:8080/stats
```

---

## 🧪 Testing

### Test Backend Endpoints

```bash
# Get all players
curl http://localhost/api/players | jq .

# Get player by ID
curl http://localhost/api/players/123 | jq .

# Get all teams
curl http://localhost/api/teams | jq .

# Get all matches
curl http://localhost/api/matches | jq .

# Get live matches
curl http://localhost/api/matches/live | jq .

# Export players data (NEW)
curl "http://localhost/api/v2/exports/players?format=csv" --output players.csv

# Get analytics dashboard (NEW)
curl http://localhost/api/v2/analytics/dashboard/overview | jq .

# Generate player report (NEW)
curl "http://localhost/api/v2/reports/player/player_1?format=pdf" --output report.pdf
```

### Test WebSocket Connection

```bash
# Connect and subscribe to matches
wscat -c ws://localhost:8080

# Send subscription
{"type":"subscribe","channel":"match","matchId":"123"}

# You should receive updates when match events occur
```

### Test Kafka Event Flow

```bash
# Produce a test event
docker-compose exec kafka kafka-console-producer \
  --bootstrap-server localhost:9092 \
  --topic player.events

# Type a JSON message:
{"event_type":"PLAYER_UPDATED","player_id":"123"}

# Press Ctrl+C to exit

# Consume events
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic player.events \
  --from-beginning
```

---

## 🛑 Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean start)
docker-compose down -v

# Stop but keep data
docker-compose stop
```

---

## 🔄 Reset Everything

If you need a fresh start:

```bash
# 1. Stop all services
docker-compose down -v

# 2. Remove all Docker data
docker system prune -a --volumes

# 3. Restart from Step 2
docker-compose up -d
./scripts/create-kafka-topics.sh
```

---

## ⚡ Performance Tips

### For Development

```env
# In .env
VITE_USE_MOCK_DATA=true  # Faster, no backend needed
```

### For Production-Like Testing

```bash
# Run fewer replicas
docker-compose up -d --scale player-service=1

# Or edit docker-compose.yml:
# Remove "replicas: 2" from services
```

### Speed Up Startup

```bash
# Start infrastructure first
docker-compose up -d mongo redis kafka elasticsearch

# Wait 20 seconds
sleep 20

# Then start services
docker-compose up -d player-service team-service match-service
```

---

## 📚 Next Steps

1. ✅ **You're Running!** - System is operational
2. 📖 **Read the Docs**: Check `FRONTEND_BACKEND_INTEGRATION.md`
3. 🔍 **Explore APIs**: Visit http://localhost:8001/docs
4. 📊 **Monitor**: Open Grafana at http://localhost:3000
5. 🎯 **Customize**: Add your own data, configure services

---

## 🆘 Need Help?

### Check Status

```bash
# Overall status
docker-compose ps

# Service health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

### View Errors

```bash
# Check logs for errors
docker-compose logs | grep -i error

# Service-specific errors
docker-compose logs player-service | grep ERROR
```

### Common Commands

```bash
# Restart a service
docker-compose restart player-service

# Rebuild a service
docker-compose up -d --build player-service

# Check resource usage
docker stats

# Check disk space
docker system df
```

---

## 🎉 Success Checklist

- [ ] Backend services running (`docker-compose ps` shows all "Up")
- [ ] Kafka topics created (`./scripts/create-kafka-topics.sh` succeeded)
- [ ] Frontend configured (`.env` has correct settings)
- [ ] Frontend started (`npm run dev` running)
- [ ] Can access http://localhost:5173
- [ ] API calls working (check browser console)
- [ ] WebSocket connected (check browser console)
- [ ] Monitoring tools accessible (Grafana, Jaeger, Kafka UI)

---

**You're ready to build!** 🚀

For more details, see:
- `FRONTEND_BACKEND_INTEGRATION.md` - Complete integration guide
- `SYSTEM_DOCUMENTATION.md` - System architecture
- `GAP_ANALYSIS.md` - Feature status & roadmap

---

**Last Updated**: 2025-10-19
**Version**: 2.0
**Services**: 13 microservices (4 new services added: Report, Export, Video, Analytics)
