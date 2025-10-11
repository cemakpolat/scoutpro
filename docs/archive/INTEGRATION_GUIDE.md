# Frontend-Backend Integration Guide

**Quick Reference**: How to connect the React frontend to the Python backend

---

## Current Status

✅ **Backend**: Fully implemented and ready
⏳ **Frontend**: Using mock data, needs to switch to real backend

---

## Quick Start (5 Minutes)

### Step 1: Update Environment Variables

Edit `.env` file:

```bash
# Change from:
VITE_USE_MOCK_DATA=true
VITE_API_BASE_URL=http://localhost:3001/api

# To:
VITE_USE_MOCK_DATA=false
VITE_API_BASE_URL=http://localhost/api/v2
```

### Step 2: Start Backend Services

```bash
# Start all backend services
docker-compose up -d

# Wait for services to be ready (30 seconds)
sleep 30

# Verify backend is running
curl http://localhost/health
# Should return: {"status":"healthy","gateway":"nginx"}
```

### Step 3: Test Backend Endpoints

```bash
# Test player service
curl http://localhost/api/v2/players

# Test team service
curl http://localhost/api/v2/teams/all

# Test match service
curl http://localhost/api/v2/matches/live
```

### Step 4: Restart Frontend

```bash
# Stop frontend if running (Ctrl+C)

# Start with new config
npm run dev

# Open browser
open http://localhost:5173
```

### Step 5: Verify Integration

Open browser console and check:
- ✅ API calls go to `http://localhost/api/v2/*`
- ✅ No mock data warnings
- ✅ Real data loads from backend

---

## API Endpoint Mapping

### Frontend → Backend Mapping

| Frontend Call | Backend Endpoint | Service |
|---------------|------------------|---------|
| `api.getPlayers()` | `GET /api/v2/players` | Player |
| `api.getPlayer(id)` | `GET /api/v2/players/{id}` | Player |
| `api.getTeams()` | `GET /api/v2/teams/all` | Team |
| `api.getTeam(id)` | `GET /api/v2/teams/{id}` | Team |
| `api.getMatches()` | `GET /api/v2/matches` | Match |
| `api.getLiveMatches()` | `GET /api/v2/matches/live` | Match |

### WebSocket Topics

| Frontend Subscribe | Backend Topic | Description |
|-------------------|---------------|-------------|
| `subscribeToMatch(id)` | `live.match.{id}` | Specific match updates |
| `subscribeToMatches()` | `live.matches` | All live matches |
| `subscribeToPlayer(id)` | `live.player.{id}` | Player updates |
| - | `live.events` | All live events |

---

## Complete Integration Checklist

### ✅ Already Complete

- [x] Backend services implemented (12 services)
- [x] 44 REST API endpoints
- [x] Nginx API Gateway configured
- [x] WebSocket server running
- [x] Kafka event streaming
- [x] Database integration
- [x] Routers registered in FastAPI apps

### ⏳ To Do (One-Time Setup)

- [ ] Update `.env` to use real backend
- [ ] Create Kafka topics (optional, auto-created)
- [ ] Test API endpoints
- [ ] Test WebSocket connection
- [ ] Update TypeScript types if needed

---

## Detailed Integration Steps

### 1. API Service Integration

The API service (`src/services/api.ts`) already has the infrastructure. Just needs the environment variable change.

**No Code Changes Needed!** The service automatically switches based on `VITE_USE_MOCK_DATA`.

### 2. WebSocket Integration

The WebSocket service (`src/hooks/useWebSocket.ts`) also switches automatically.

**No Code Changes Needed!** Just update the `.env` file.

### 3. Type Compatibility

Frontend TypeScript types should mostly match backend responses. If there are mismatches:

**Backend Response Format**:
```json
{
  "id": "p_123",
  "name": "Bukayo Saka",
  "position": "RW",
  "club": "Arsenal",
  "age": 22,
  "stats": {
    "goals": 14,
    "assists": 9
  }
}
```

**Frontend Type** (already defined in `src/types/index.ts`):
```typescript
interface Player {
  id: string;
  name: string;
  position: string;
  club: string;
  age: number;
  stats: PlayerStats;
}
```

---

## Testing the Integration

### Test 1: API Endpoints

```bash
# In terminal
curl -X GET http://localhost/api/v2/players \
  -H "Content-Type: application/json"

# Should return array of players
```

### Test 2: WebSocket Connection

```javascript
// In browser console
const ws = new WebSocket('ws://localhost/socket.io');

ws.onopen = () => {
  console.log('Connected!');
  ws.send(JSON.stringify({
    type: 'subscribe',
    topic: 'live.matches'
  }));
};

ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
```

### Test 3: Full Frontend Flow

1. Open `http://localhost:5173`
2. Navigate to Player Database
3. Open browser DevTools → Network tab
4. Should see requests to `http://localhost/api/v2/players`
5. Should see WebSocket connection to `ws://localhost/socket.io`

---

## Troubleshooting

### Problem: "CORS Error"

**Solution**: Nginx already configured with CORS headers. Verify Nginx is running:
```bash
docker-compose ps nginx
```

### Problem: "404 Not Found"

**Solution**: Check that the endpoint exists:
```bash
# List all available endpoints
docker-compose logs player-service | grep "GET.*api"
```

### Problem: "WebSocket Connection Failed"

**Solution**: Check WebSocket server is running:
```bash
curl http://localhost:8080/health
# Should return: {"status":"healthy"}
```

### Problem: "Empty Response / No Data"

**Solution**: Backend might not have data yet. Check MongoDB has Opta data:
```bash
docker-compose exec mongodb mongosh scoutpro --eval "db.players.count()"
```

---

## Environment Variables Reference

### Frontend (.env)

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost/api/v2
VITE_API_KEY=                              # Optional
VITE_USE_MOCK_DATA=false                   # Set to false for real backend

# WebSocket (auto-configured via Nginx proxy)
# No additional config needed - connects to /socket.io
```

### Backend (docker-compose.yml)

```yaml
environment:
  # MongoDB
  MONGO_URI: mongodb://mongodb:27017/scoutpro

  # Kafka
  KAFKA_BOOTSTRAP_SERVERS: kafka:9092

  # Redis
  REDIS_HOST: redis
  REDIS_PORT: 6379

  # TimescaleDB
  TIMESCALE_HOST: timescaledb
  TIMESCALE_PORT: 5432
  TIMESCALE_DB: scoutpro_timeseries
```

---

## Data Flow Diagram

```
┌──────────┐
│ Frontend │
│ (React)  │
└────┬─────┘
     │
     ├─ HTTP REST ──────────┐
     │                      ↓
     │              ┌───────────────┐
     │              │ Nginx Gateway │
     │              │  Port 80      │
     │              └───────┬───────┘
     │                      │
     │              ┌───────┴────────┬────────────┬──────────┐
     │              ↓                ↓            ↓          ↓
     │         ┌─────────┐     ┌─────────┐  ┌─────────┐ ┌──────┐
     │         │ Player  │     │  Team   │  │ Match   │ │ ...  │
     │         │ Service │     │ Service │  │ Service │ │      │
     │         └─────────┘     └─────────┘  └─────────┘ └──────┘
     │              │                │            │
     │              └────────┬───────┴────────────┘
     │                       ↓
     │                  ┌─────────┐
     │                  │  Kafka  │
     │                  └────┬────┘
     │                       │
     │                       ↓
     │              ┌────────────────┐
     │              │  WebSocket     │
     ├─ WebSocket ─┤  Server        │
     │              │  Port 8080     │
     │              └────────────────┘
     │
     ↓
┌──────────┐
│ Browser  │
└──────────┘
```

---

## Next Steps After Integration

1. **Test All Features**: Go through each page and verify data loads
2. **Check Console**: Look for any errors or warnings
3. **Monitor Performance**: Check response times in Network tab
4. **Test Live Updates**: Subscribe to match and verify real-time events
5. **Production Deploy**: Once working locally, deploy to production

---

## Summary

**What Changed**: Just the `.env` file

**What Stayed the Same**: All frontend code

**Time Required**: 5 minutes + testing

**Result**: Frontend now connected to real backend with live data and real-time updates

---

**Need Help?** Check `SYSTEM_DOCUMENTATION.md` for detailed architecture and troubleshooting.
