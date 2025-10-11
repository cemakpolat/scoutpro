# Frontend-Backend Integration Guide

## Overview

This guide explains how the ScoutPro frontend connects to the backend microservices architecture.

## Architecture

### Backend Services

The backend consists of multiple microservices running in Docker containers:

| Service | Port | Description |
|---------|------|-------------|
| **NGINX (API Gateway)** | 80 | Routes requests to appropriate microservices |
| **Player Service** | 8001 | Player data and statistics |
| **Team Service** | 8002 | Team information and analytics |
| **Match Service** | 8003 | Match data, events, and leagues |
| **Statistics Service** | 8004 | Analytics, market, and tactical data |
| **ML Service** | 8005 | Machine learning models and predictions |
| **Live Ingestion Service** | 8006 | Real-time data ingestion from external APIs |
| **Search Service** | 8007 | Full-text search functionality |
| **Notification Service** | 8008 | User notifications |
| **WebSocket Server** | 8080 | Real-time updates via WebSocket |

### Frontend API Routes

The frontend uses the following API endpoints (all routes go through NGINX on port 80):

```
Frontend Request → NGINX Gateway (port 80) → Microservice (port 800X)
```

## API Endpoint Mapping

### Player Endpoints

**Frontend**: `GET /api/players`
**NGINX Routes To**: `http://player-service:8000/players`
**Service Port**: 8001

```typescript
// Usage in frontend
import apiService from '../services/api';

const players = await apiService.getPlayers();
const player = await apiService.getPlayer(playerId);
const searchResults = await apiService.searchPlayers(query);
```

### Team Endpoints

**Frontend**: `GET /api/teams`
**NGINX Routes To**: `http://team-service:8000/teams`
**Service Port**: 8002

```typescript
const teams = await apiService.getTeams();
const team = await apiService.getTeam(teamId);
```

### Match Endpoints

**Frontend**: `GET /api/matches`, `/api/leagues`
**NGINX Routes To**: `http://match-service:8000/matches`, `/leagues`
**Service Port**: 8003

```typescript
const matches = await apiService.getMatches(filters);
const match = await apiService.getMatch(matchId);
const liveMatches = await apiService.getLiveMatches();
const leagues = await apiService.getLeagues();
```

### Analytics Endpoints

**Frontend**: `GET /api/analytics`
**NGINX Routes To**: `http://statistics-service:8000/analytics`
**Service Port**: 8004

```typescript
const analytics = await apiService.getAnalytics(type);
const playerAnalytics = await apiService.getPlayerAnalytics(playerId);
const matchAnalytics = await apiService.getMatchAnalytics(matchId);
```

### ML Endpoints

**Frontend**: `GET /api/ml`, `/api/ai`
**NGINX Routes To**: `http://ml-service:8000/ml`, `/ai`
**Service Port**: 8005

```typescript
const algorithms = await apiService.getMLAlgorithms();
const datasets = await apiService.getMLDatasets();
const experiments = await apiService.getMLExperiments();
const insights = await apiService.getAIInsights(type);
```

### Search Endpoints

**Frontend**: `GET /api/search`
**NGINX Routes To**: `http://search-service:8000/search`
**Service Port**: 8007

```typescript
import { searchService } from '../services/searchService';

const results = await searchService.search({ query, type, filters });
```

### Notification Endpoints

**Frontend**: `GET /api/notifications`
**NGINX Routes To**: `http://notification-service:8000/notifications`
**Service Port**: 8008

```typescript
const notifications = await apiService.getNotifications();
await apiService.markNotificationRead(notificationId);
```

### Market & Tactical Endpoints

**Frontend**: `GET /api/market`, `/api/tactical`
**NGINX Routes To**: `http://statistics-service:8000/market`, `/tactical`
**Service Port**: 8004

```typescript
const marketTrends = await apiService.getMarketTrends();
const predictions = await apiService.getTransferPredictions();
const patterns = await apiService.getTacticalPatterns();
```

## WebSocket Connection

**Frontend**: `ws://localhost:8080`
**Service**: WebSocket Server (Socket.io)

```typescript
import { useWebSocket } from '../hooks/useWebSocket';

const { subscribe, subscribeToMatch } = useWebSocket();

// Subscribe to match updates
subscribeToMatch(matchId);
subscribe('match_update', (data) => {
  console.log('Match update:', data);
});

// Subscribe to notifications
subscribe('notification', (notification) => {
  console.log('New notification:', notification);
});
```

## Configuration

### Environment Variables

#### Frontend (.env)

```env
# API Configuration
VITE_API_BASE_URL=http://localhost/api
VITE_WS_URL=ws://localhost:8080
VITE_USE_MOCK_DATA=false
VITE_AUTH_ENABLED=false
```

#### Backend (.env.backend.example)

```env
# External API Keys
OPTA_API_KEY=your_opta_api_key_here
STATSBOMB_API_KEY=your_statsbomb_api_key_here
WYSCOUT_API_KEY=your_wyscout_api_key_here

# Database Credentials
MONGODB_ROOT_USERNAME=root
MONGODB_ROOT_PASSWORD=scoutpro123
POSTGRES_USER=scoutpro
POSTGRES_PASSWORD=scoutpro123
REDIS_PASSWORD=scoutpro123
```

## Setup Instructions

### Option 1: Full Stack (Docker)

**Best for**: Production-like environment, testing full system

```bash
# 1. Copy environment files
cp .env.example .env
cp .env.backend.example .env.backend

# 2. Start all backend services
docker-compose up -d

# 3. Wait for services to be healthy (check with docker ps)
docker-compose ps

# 4. Update frontend .env
# Set VITE_USE_MOCK_DATA=false
# Set VITE_API_BASE_URL=http://localhost/api

# 5. Start frontend
npm run dev

# 6. Access application
# Frontend: http://localhost:5173
# API Gateway: http://localhost
# Grafana: http://localhost:3000
# Kafka UI: http://localhost:8090
```

### Option 2: Frontend Only (Mock Data)

**Best for**: UI development, no backend needed

```bash
# 1. Update .env
# Set VITE_USE_MOCK_DATA=true

# 2. Start frontend
npm run dev

# All API calls will use mock data
```

### Option 3: Hybrid (Frontend + Selected Services)

**Best for**: Developing specific features

```bash
# 1. Start only needed services
docker-compose up -d player-service team-service mongo redis

# 2. Update .env
# Set VITE_USE_MOCK_DATA=false

# 3. Start frontend
npm run dev

# Mock data will be used for services that aren't running
```

## NGINX Configuration

The NGINX gateway (`nginx/nginx.conf`) handles:

1. **Request Routing**: Routes `/api/*` to appropriate microservices
2. **CORS**: Handles cross-origin requests
3. **Rate Limiting**: Protects services from abuse
4. **WebSocket Proxying**: Routes WebSocket connections
5. **Load Balancing**: Can distribute load across service instances

### Key NGINX Routes

```nginx
# Frontend-compatible v1 API
location /api/players { proxy_pass http://player-service/players; }
location /api/teams { proxy_pass http://team-service/teams; }
location /api/matches { proxy_pass http://match-service/matches; }
location /api/ml { proxy_pass http://ml-service/ml; }
location /api/analytics { proxy_pass http://statistics-service/analytics; }

# WebSocket
location /socket.io {
    proxy_pass http://websocket-server;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## Data Flow

### Typical API Request Flow

```
1. Frontend Component
   └─> apiService.getPlayers()

2. API Service (src/services/api.ts)
   └─> fetch('http://localhost/api/players')

3. NGINX Gateway (port 80)
   └─> Receives request
   └─> Routes to http://player-service:8000/players

4. Player Service (port 8001)
   └─> Queries MongoDB
   └─> Returns JSON response

5. NGINX Gateway
   └─> Adds CORS headers
   └─> Returns response to frontend

6. API Service
   └─> Parses response
   └─> Returns data or fallback to mock data

7. Frontend Component
   └─> Updates UI with data
```

### WebSocket Real-Time Flow

```
1. Frontend Component
   └─> useWebSocket()

2. WebSocket Hook
   └─> Connects to ws://localhost:8080

3. WebSocket Server
   └─> Establishes connection
   └─> Subscribes to Kafka topics

4. Kafka Event
   └─> match_update event published

5. WebSocket Server
   └─> Receives from Kafka
   └─> Broadcasts to connected clients

6. Frontend Component
   └─> Receives update
   └─> Updates UI in real-time
```

## Error Handling

The frontend implements graceful degradation:

```typescript
// All API calls have fallback to mock data
async getPlayers(filters) {
  if (this.useMockData) {
    return { success: true, data: mockPlayers };
  }

  const response = await this.request('/players');

  // Fallback to mock if API fails
  if (!response.success) {
    return {
      success: true,
      data: mockPlayers,
      meta: { source: 'mock-fallback' }
    };
  }

  return response;
}
```

## Troubleshooting

### Issue: "Network request failed"

**Cause**: Backend services not running or wrong URL

**Solution**:
```bash
# Check if services are running
docker-compose ps

# Check NGINX logs
docker-compose logs nginx

# Verify frontend .env
cat .env | grep VITE_API_BASE_URL
# Should be: http://localhost/api
```

### Issue: "CORS error"

**Cause**: CORS headers not properly configured

**Solution**:
```bash
# Check NGINX CORS configuration
grep -A 5 "CORS Headers" nginx/nginx.conf

# Restart NGINX
docker-compose restart nginx
```

### Issue: "WebSocket connection failed"

**Cause**: WebSocket server not running or wrong URL

**Solution**:
```bash
# Check WebSocket server
docker-compose logs websocket-server

# Verify frontend .env
cat .env | grep VITE_WS_URL
# Should be: ws://localhost:8080

# Test WebSocket endpoint
curl http://localhost:8080/health
```

### Issue: "Empty data returned"

**Cause**: Database not initialized or no data

**Solution**:
```bash
# Check database
docker-compose exec mongo mongosh -u root -p scoutpro123

# Enable mock data temporarily
# In .env: VITE_USE_MOCK_DATA=true
```

## Testing the Integration

### 1. Health Check

```bash
# Check NGINX gateway
curl http://localhost/health

# Check individual services
curl http://localhost:8001/health  # Player service
curl http://localhost:8002/health  # Team service
curl http://localhost:8003/health  # Match service
```

### 2. API Test

```bash
# Test through NGINX gateway
curl http://localhost/api/players

# Test WebSocket
wscat -c ws://localhost:8080
```

### 3. Frontend Integration Test

```typescript
// In browser console (http://localhost:5173)
import apiService from './services/api';

// Test API call
const response = await apiService.getPlayers();
console.log('API Response:', response);

// Check data source
console.log('Data source:', response.meta?.source);
// Should be 'api' if backend is running
// Will be 'mock' or 'mock-fallback' if using mock data
```

## Performance Optimization

### Caching

Redis is used for caching at multiple levels:

```
Frontend → NGINX → Service → Redis Cache → Database
```

### Rate Limiting

NGINX implements rate limiting:
- API endpoints: 100 requests/second
- ML endpoints: 50 requests/second (due to higher computational cost)
- WebSocket: 50 connections/second

### Connection Pooling

Each microservice maintains connection pools to:
- MongoDB
- PostgreSQL/TimescaleDB
- Redis
- Kafka

## Monitoring

### Service Health

```bash
# View all service health
docker-compose ps

# View service logs
docker-compose logs -f player-service
docker-compose logs -f nginx
```

### Metrics & Dashboards

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Jaeger Tracing**: http://localhost:16686
- **Kafka UI**: http://localhost:8090

## API Versioning

The system supports two API versions:

1. **v1 (Frontend)**: `/api/players`, `/api/teams`, etc.
   - Used by the React frontend
   - Routes through NGINX to microservices

2. **v2 (Backend)**: `/api/v2/players`, `/api/v2/teams`, etc.
   - Used for direct microservice communication
   - May have different schemas or features

## Security Considerations

### Production Checklist

- [ ] Enable HTTPS in NGINX
- [ ] Set strong passwords in `.env.backend`
- [ ] Enable JWT authentication (`VITE_AUTH_ENABLED=true`)
- [ ] Configure proper CORS origins (not `*`)
- [ ] Set up API rate limiting per user
- [ ] Enable database authentication
- [ ] Use secrets management (not plain text .env)
- [ ] Set up firewall rules
- [ ] Enable service-to-service authentication

## Next Steps

1. **Start Backend**: `docker-compose up -d`
2. **Configure Frontend**: Update `.env` with `VITE_USE_MOCK_DATA=false`
3. **Develop Features**: Use real backend API
4. **Monitor**: Check Grafana dashboards
5. **Deploy**: Follow production security checklist

## Support

For issues or questions:
- Check logs: `docker-compose logs <service-name>`
- Review NGINX config: `nginx/nginx.conf`
- Check environment: `.env` and `.env.backend`
- Refer to: `SYSTEM_DOCUMENTATION.md`, `BACKEND_ARCHITECTURE.md`
