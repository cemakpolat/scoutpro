# ScoutPro System Documentation

**Last Updated**: 2025-10-05
**System Status**: Backend Complete, Frontend Integration Pending

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Backend Services](#backend-services)
4. [Frontend Application](#frontend-application)
5. [Integration Status](#integration-status)
6. [Missing Components](#missing-components)
7. [How to Connect Frontend to Backend](#how-to-connect-frontend-to-backend)
8. [Deployment Guide](#deployment-guide)

---

## System Overview

ScoutPro is a football analytics platform built with a **microservices architecture**:

- **Frontend**: React + TypeScript (Vite)
- **Backend**: 12 Python microservices (FastAPI)
- **Message Bus**: Kafka for event-driven communication
- **Databases**: MongoDB, TimescaleDB, Redis, Elasticsearch
- **Real-Time**: WebSocket server for live updates
- **Monitoring**: Prometheus metrics + structured logging

### Current State

✅ **Complete**:
- Backend microservices (12 services)
- 44 REST API endpoints
- Kafka event streaming
- WebSocket real-time layer
- Multi-database integration
- Monitoring & observability

⏳ **Pending**:
- Frontend → Backend API integration
- WebSocket connection configuration
- Environment configuration for production

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│           React Frontend (Port 5173)                    │
│  • Mock data mode: VITE_USE_MOCK_DATA=true             │
│  • Real API mode: VITE_USE_MOCK_DATA=false             │
└────────────────────┬────────────────────────────────────┘
                     │
         HTTP REST   │   WebSocket
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│          Nginx API Gateway (Port 80)                    │
│  • Rate limiting: 100 req/s                            │
│  • CORS enabled                                         │
│  • Routes: /api/v2/* → services                        │
│  • WebSocket: /socket.io → ws-server                   │
└──┬──────────┬──────────┬──────────┬──────────┬─────────┘
   │          │          │          │          │
   ↓          ↓          ↓          ↓          ↓
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
│Player  │ │Team    │ │Match   │ │Stats   │ │WebSocket │
│:8000   │ │:8000   │ │:8000   │ │:8000   │ │:8080     │
└───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └────┬─────┘
    │          │          │          │           │
    └──────────┴──────────┴──────────┴───────────┘
                     │
                     ↓
            ┌────────────────┐
            │ Kafka (Port    │
            │     9092)      │
            └────────────────┘
                     │
    ┌────────────────┼────────────────┬──────────┐
    ↓                ↓                ↓          ↓
┌────────┐    ┌──────────┐    ┌─────────┐  ┌────────┐
│MongoDB │    │TimescaleDB│    │Redis    │  │Elastic │
│:27017  │    │:5432      │    │:6379    │  │:9200   │
└────────┘    └──────────┘    └─────────┘  └────────┘
```

---

## Backend Services

### 1. Player Service (Port 8000)

**Purpose**: Player data and statistics

**Endpoints (12)**:
```
GET  /api/v2/players/{player_id}           # Get player by ID
GET  /api/v2/players                       # Search players
GET  /api/v2/players/by-name               # Player by team+name
GET  /api/v2/players/{player_id}/stats     # Player statistics
GET  /api/v2/players/stats/by-name         # Stats by name
GET  /api/v2/players/events/passes         # Pass events
GET  /api/v2/players/events/shots          # Shot events
GET  /api/v2/players/{player_id}/events    # All events
GET  /api/v2/players/compare               # Compare players
GET  /api/v2/players/minutes               # Minutes played
GET  /api/v2/players/by-team               # Players by team
GET  /api/v2/players/top                   # Top performers
```

**Code**: `/services/player-service/api/endpoints/players.py`

**Features**:
- MongoEngine models for Opta data (F1, F9, F24, F40)
- Async endpoints with ThreadPoolExecutor bridge
- Publishes events to Kafka (`player.events` topic)
- Cross-service calls to Match Service for events

### 2. Team Service (Port 8000)

**Purpose**: Team data and statistics

**Endpoints (17)**:
```
GET  /api/v2/teams/{team_id}              # Get team by ID
GET  /api/v2/teams/by-name                # Team by name
GET  /api/v2/teams                        # Search teams
GET  /api/v2/teams/{team_id}/stats        # Team statistics
GET  /api/v2/teams/stats/by-name          # Stats by name
GET  /api/v2/teams/stats/season           # Season statistics
GET  /api/v2/teams/{team_id}/players      # Team players
GET  /api/v2/teams/players/by-name        # Players by team name
GET  /api/v2/teams/squad                  # Full squad
GET  /api/v2/teams/compare                # Compare teams
GET  /api/v2/teams/{team_id}/matches      # Team matches
GET  /api/v2/teams/matches/by-name        # Matches by team name
GET  /api/v2/teams/fixtures               # Upcoming fixtures
GET  /api/v2/teams/form                   # Recent form
GET  /api/v2/teams/standings              # League standings
GET  /api/v2/teams/{team_id}/events       # All events
GET  /api/v2/teams/all                    # All teams
```

**Code**: `/services/team-service/api/endpoints/teams.py`

**Features**:
- Team data from Opta F1 feeds
- Squad management
- Form and standings calculation
- Publishes to `team.events` Kafka topic

### 3. Match Service (Port 8000)

**Purpose**: Match data and events

**Endpoints (15)**:
```
GET  /api/v2/matches/{match_id}                    # Get match
GET  /api/v2/matches                               # List matches
GET  /api/v2/matches/search                        # Search
GET  /api/v2/matches/{match_id}/stats              # Statistics
GET  /api/v2/matches/{match_id}/summary            # Summary
GET  /api/v2/matches/live                          # Live matches
GET  /api/v2/matches/{match_id}/live               # Live match data
GET  /api/v2/matches/{match_id}/events             # All events
GET  /api/v2/events/{event_id}                     # Event by ID
GET  /api/v2/matches/{match_id}/events/filter      # Filtered
GET  /api/v2/matches/by-team                       # By team
GET  /api/v2/matches/{match_id}/players/{player_id}/stats  # Player stats
GET  /api/v2/matches/date-range                    # Date range
GET  /api/v2/matches/season                        # Season matches
GET  /api/v2/matches/season/events                 # Season events
```

**Code**: `/services/match-service/api/endpoints/matches.py`

**Features**:
- F9 (Match data) and F24 (Event data)
- Live match tracking
- Event timeline
- Publishes to `match.events` Kafka topic

### 4. Statistics Service (Port 8000)

**Purpose**: Real-time statistics aggregation

**Code**: `/services/statistics-service/consumers/event_consumer.py`

**Features**:
- Consumes from Kafka: `match.events`, `player.events`, `team.events`
- Handles live events:
  - GOAL_SCORED → Increment goals
  - ASSIST_MADE → Increment assists
  - CARD_ISSUED → Increment cards
  - SHOT_TAKEN → Track shot statistics
  - PASS_COMPLETED → Track pass statistics
- Aggregates stats when match ends
- Publishes `STATS_AGGREGATED` back to Kafka

### 5. Search Service (Port 8000)

**Purpose**: Full-text search indexing

**Code**: `/services/search-service/consumers/event_consumer.py`

**Features**:
- Consumes from Kafka: `player.events`, `team.events`, `match.events`
- Indexes to Elasticsearch:
  - `players` index
  - `teams` index
  - `matches` index
- Real-time index updates
- Handles CREATED/UPDATED events

### 6. WebSocket Server (Port 8080)

**Purpose**: Real-time updates to frontend

**Endpoints**:
```
WS   /ws                  # Anonymous connection
WS   /ws/{user_id}        # Authenticated connection
GET  /health              # Health check
GET  /stats               # Connection statistics
```

**Code**:
- `/services/websocket-server/main.py`
- `/services/websocket-server/kafka_bridge/event_bridge.py`

**Features**:
- Kafka → WebSocket bridge
- Topic subscriptions:
  - `live.match.{match_id}` - Specific match
  - `live.matches` - All matches
  - `live.player.{player_id}` - Player updates
  - `live.team.{team_id}` - Team updates
  - `live.events` - All live events
  - `live.statistics` - Statistics updates
- Broadcasts Kafka events to subscribed clients
- Connection management
- Ping/pong heartbeat

### 7. ML Service (Port 8000)

**Purpose**: Machine learning predictions

**Features**:
- Player rating predictions
- Match outcome predictions
- Transfer value estimation
- Performance trend analysis

### 8-12. Supporting Services

- **Live Ingestion Service**: Real-time feed ingestion
- **Notification Service**: User notifications
- **API Documentation Service**: OpenAPI/Swagger
- **Admin Service**: Admin panel

---

## Frontend Application

### Current Setup

**Tech Stack**:
- React 18.3
- TypeScript 5.5
- Vite 5.4
- TailwindCSS 3.4
- Lucide React icons

**State Management**:
- React Context API
- Custom hooks

**Key Components**:

1. **Dashboard** (`src/components/Dashboard.tsx`)
   - Overview of players, teams, matches
   - Recent activity
   - Top performers

2. **Player Database** (`src/components/PlayerDatabase.tsx`)
   - Player search and filters
   - Player cards
   - Detailed player view

3. **Match Centre** (`src/components/MatchCentre.tsx`)
   - Live matches
   - Match details
   - Event timeline

4. **ML Laboratory** (`src/components/MLLaboratory.tsx`)
   - ML algorithms
   - Datasets
   - Experiments

### Data Layer

**API Service** (`src/services/api.ts`):
```typescript
class ApiService {
  private baseUrl: string;
  private useMockData: boolean;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001/api';
    this.useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';
  }

  async getPlayers(filters?: PlayerFilters): Promise<ApiResponse<Player[]>> {
    if (this.useMockData) {
      return { success: true, data: mockPlayers };
    }
    return this.request<Player[]>('/players', { /* ... */ });
  }
}
```

**Current Status**: Uses mock data by default (`VITE_USE_MOCK_DATA=true`)

**WebSocket Hook** (`src/hooks/useWebSocket.ts`):
```typescript
export function useWebSocket() {
  const useMockWebSocket = import.meta.env.VITE_USE_MOCK_DATA === 'true';
  const activeWsService = useMockWebSocket ? mockWebSocketService : wsService;

  // Returns: subscribe, send, subscribeToMatch, etc.
}
```

**Current Status**: Uses mock WebSocket by default

---

## Integration Status

### ✅ Backend Complete

| Component | Status | Details |
|-----------|--------|---------|
| REST APIs | ✅ | 44 endpoints implemented |
| Kafka Events | ✅ | Producer + Consumer + 25 event types |
| WebSocket | ✅ | Server + Kafka bridge |
| TimescaleDB | ✅ | 4 hypertables for time-series |
| Redis | ✅ | Caching + live state |
| Monitoring | ✅ | Prometheus + structured logs |

### ⏳ Frontend Integration Pending

| Component | Status | Action Needed |
|-----------|--------|---------------|
| API Calls | ⏳ | Update baseUrl to Nginx gateway |
| WebSocket | ⏳ | Connect to real WebSocket server |
| Environment | ⏳ | Set `VITE_USE_MOCK_DATA=false` |
| API Types | ⏳ | Update TypeScript types to match backend responses |

---

## Missing Components

### 1. Frontend API Integration ⏳

**What's Missing**:
- Frontend still uses mock data
- API service needs to call real backend endpoints
- TypeScript types need to match backend response schemas

**What Needs to Be Done**:
1. Update `.env`:
   ```bash
   VITE_API_BASE_URL=http://localhost/api/v2
   VITE_USE_MOCK_DATA=false
   ```

2. Update API service to match backend endpoints:
   ```typescript
   // Old (mock)
   async getPlayers(): Promise<Player[]> {
     return mockPlayers;
   }

   // New (real)
   async getPlayers(filters?: PlayerFilters): Promise<Player[]> {
     const response = await this.request<Player[]>('/players', {
       method: 'GET',
       query: filters
     });
     return response.data;
   }
   ```

3. Update TypeScript types to match backend schemas

### 2. WebSocket Integration ⏳

**What's Missing**:
- WebSocket service not connected to real server
- Topic subscription format needs to match backend

**What Needs to Be Done**:
1. Update WebSocket service (`src/services/websocket.ts`):
   ```typescript
   class WebSocketService {
     connect() {
       this.socket = io('ws://localhost/socket.io', {
         transports: ['websocket'],
         reconnection: true
       });
     }

     subscribeToMatch(matchId: string) {
       this.send({
         type: 'subscribe',
         topic: `live.match.${matchId}`
       });
     }
   }
   ```

2. Handle backend event format:
   ```typescript
   socket.on('message', (data) => {
     // Backend sends: { type: 'match_event', event_type: 'goal', data: {...} }
     if (data.event_type === 'match.goal') {
       // Handle goal event
     }
   });
   ```

### 3. Service Endpoints Not Exposed via FastAPI ⏳

**What's Missing**:
- The endpoint files exist but aren't registered in FastAPI apps
- Services need to import and mount the routers

**What Needs to Be Done**:

Update `/services/player-service/main.py`:
```python
from api.endpoints.players import router as players_router

app = FastAPI(title="Player Service")
app.include_router(players_router)  # Add this line
```

Update `/services/team-service/main.py`:
```python
from api.endpoints.teams import router as teams_router

app = FastAPI(title="Team Service")
app.include_router(teams_router)  # Add this line
```

Update `/services/match-service/main.py`:
```python
from api.endpoints.matches import router as matches_router

app = FastAPI(title="Match Service")
app.include_router(matches_router)  # Add this line
```

### 4. Kafka Topics Not Auto-Created ⏳

**What's Missing**:
- Kafka topics need to be created before services start publishing

**What Needs to Be Done**:
```bash
# Create topics
docker-compose exec kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic player.events \
  --partitions 3 \
  --replication-factor 1

docker-compose exec kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic team.events \
  --partitions 3 \
  --replication-factor 1

docker-compose exec kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic match.events \
  --partitions 3 \
  --replication-factor 1
```

### 5. Database Initialization Scripts ⏳

**What's Missing**:
- TimescaleDB schema initialization not automatic
- Need to call `initialize_schema()` on startup

**What Needs to Be Done**:

Add to statistics service startup:
```python
# In main.py startup event
from shared.database import get_timescale_client

@app.on_event("startup")
async def startup():
    # Initialize TimescaleDB
    ts_client = await get_timescale_client()
    await ts_client.initialize_schema()
```

---

## How to Connect Frontend to Backend

### Step 1: Update Environment Variables

Edit `.env`:
```bash
# Change this
VITE_USE_MOCK_DATA=true

# To this
VITE_USE_MOCK_DATA=false

# Update API base URL
VITE_API_BASE_URL=http://localhost/api/v2

# WebSocket URL (Nginx will proxy)
VITE_WS_URL=ws://localhost/socket.io
```

### Step 2: Start Backend Services

```bash
# Start infrastructure
docker-compose up -d kafka zookeeper mongodb timescaledb redis elasticsearch

# Wait 30 seconds
sleep 30

# Start application services
docker-compose up -d player-service team-service match-service \
  statistics-service search-service websocket-server

# Start API gateway
docker-compose up -d nginx

# Verify
curl http://localhost/health
```

### Step 3: Update Frontend API Service

The API service already has the structure but needs the router registration (see Missing Components #3 above).

### Step 4: Test Integration

```bash
# Terminal 1: Start frontend
npm run dev

# Terminal 2: Test API
curl http://localhost/api/v2/players

# Terminal 3: Test WebSocket
wscat -c ws://localhost/socket.io
> {"type":"subscribe","topic":"live.matches"}
```

### Step 5: Verify Data Flow

1. Open browser: http://localhost:5173
2. Open browser console
3. Should see API calls to `http://localhost/api/v2/*`
4. Should see WebSocket connection to `ws://localhost/socket.io`
5. Check for errors in console

---

## Deployment Guide

### Local Development

```bash
# 1. Clone repository
git clone <repo>
cd scoutpro

# 2. Install frontend dependencies
npm install

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Start backend
docker-compose up -d

# 5. Start frontend
npm run dev

# 6. Open browser
open http://localhost:5173
```

### Production Deployment

1. **Build Frontend**:
   ```bash
   npm run build
   # Output: dist/
   ```

2. **Configure Nginx to Serve Frontend**:
   ```nginx
   # Add to nginx.conf
   location / {
     root /usr/share/nginx/html;
     try_files $uri $uri/ /index.html;
   }
   ```

3. **Update docker-compose.yml**:
   ```yaml
   nginx:
     volumes:
       - ./dist:/usr/share/nginx/html:ro
   ```

4. **Set Production Environment**:
   ```bash
   VITE_API_BASE_URL=https://api.scoutpro.com/api/v2
   VITE_WS_URL=wss://api.scoutpro.com/socket.io
   VITE_USE_MOCK_DATA=false
   ```

5. **Deploy**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

---

## Summary

### What's Working ✅

- Complete backend microservices architecture
- 44 REST API endpoints
- Kafka event streaming
- WebSocket real-time server
- Multi-database integration
- Monitoring & observability

### What's Needed ⏳

1. **Register API routers in FastAPI apps** (3 services)
2. **Create Kafka topics** (one-time setup)
3. **Initialize TimescaleDB schema** (automatic on first connection)
4. **Update frontend `.env`** to use real backend
5. **Update WebSocket service** to connect to real server

### Estimated Time to Complete Integration

- Register routers: **10 minutes**
- Create Kafka topics: **5 minutes**
- Update frontend config: **5 minutes**
- Testing & debugging: **30 minutes**

**Total: ~1 hour** to fully integrate frontend with backend

---

## Next Steps

1. Complete the missing router registrations
2. Create Kafka topics
3. Test backend endpoints independently
4. Update frontend configuration
5. Test full integration
6. Deploy to production

---

**Documentation maintained by**: Development Team
**Last verified**: 2025-10-05
