# ScoutPro - Architecture Overview

**Last Updated**: 2025-10-11

---

## 🏗️ **System Architecture**

ScoutPro uses a **microservices architecture** with event-driven communication via Kafka.

### **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│              React Frontend (Port 5173)                      │
│  Dashboard | Players | Teams | Matches | ML Lab             │
└────────────────────┬────────────────────────────────────────┘
                     │
         HTTP REST   │   WebSocket
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│          Nginx API Gateway (Port 80)                        │
│  • Rate limiting: 100 req/s                                 │
│  • CORS enabled                                             │
│  • Routes: /api/* → services                               │
│  • WebSocket: ws://localhost:8080                          │
└──┬──────────┬──────────┬──────────┬──────────┬─────────────┘
   │          │          │          │          │
   ↓          ↓          ↓          ↓          ↓
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
│Player  │ │Team    │ │Match   │ │Stats   │ │WebSocket │
│:8001   │ │:8002   │ │:8003   │ │:8004   │ │:8080     │
└───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └────┬─────┘
    │          │          │          │           │
    └──────────┴──────────┴──────────┴───────────┘
                     │
                     ↓
            ┌────────────────┐
            │ Kafka (:9092)  │
            │  Event Bus     │
            └────────────────┘
                     │
    ┌────────────────┼────────────────┬──────────┐
    ↓                ↓                ↓          ↓
┌─────────┐    ┌──────────┐    ┌─────────┐  ┌────────┐
│MongoDB  │    │TimescaleDB│    │Redis    │  │Elastic │
│:27017   │    │:5432      │    │:6379    │  │:9200   │
└─────────┘    └──────────┘    └─────────┘  └────────┘
```

---

## 📦 **Service Inventory**

### **Frontend**
- **Technology**: React 18.3 + TypeScript + Vite
- **Port**: 5173
- **Features**: 20+ components, mock data system, WebSocket integration

### **Backend Services** (9 Implemented)

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **Player Service** | 8001 | Player data & statistics | ⚠️ Needs fixes |
| **Team Service** | 8002 | Team data & squad management | ⚠️ Needs fixes |
| **Match Service** | 8003 | Match data & events | ⚠️ Not running |
| **Statistics Service** | 8004 | Stats aggregation & time-series | 🔴 Blocked |
| **ML Service** | 8005 | ML predictions & models | 🔴 Not started |
| **Search Service** | 8007 | Elasticsearch full-text search | ⚠️ Needs fixes |
| **Notification Service** | 8008 | User notifications | 🔴 Dependency issues |
| **WebSocket Server** | 8080 | Real-time updates | 🔴 Dependency issues |
| **Live Ingestion** | 8006 | Data ingestion from Opta/Stats | 🔴 Not started |

### **Missing Services** (Not Implemented)

| Service | Planned Port | Purpose | Priority |
|---------|--------------|---------|----------|
| **Report Service** | 8009 | PDF/Excel generation | Medium |
| **Export Service** | 8010 | CSV/JSON exports | Medium |
| **Video Service** | 8011 | Video analysis | Low |
| **Analytics Service** | 8012 | BI dashboards | Low |

---

## 🗄️ **Data Storage**

### **MongoDB** (Port 27017)
- **Purpose**: Primary data store
- **Collections**: Players, Teams, Matches, Events
- **Status**: ✅ Running & Healthy

### **TimescaleDB** (Port 5432)
- **Purpose**: Time-series statistics
- **Tables**: player_stats_timeseries, match_events, team_stats
- **Status**: 🔴 Port conflict - not running

### **Redis** (Port 6379)
- **Purpose**: Caching & session storage
- **Usage**: Player cache (5min TTL), Match state, Rate limiting
- **Status**: ✅ Running & Healthy

### **Elasticsearch** (Port 9200)
- **Purpose**: Full-text search
- **Indices**: players, teams, matches
- **Status**: ✅ Running & Healthy

---

## 🔄 **Event-Driven Architecture**

### **Kafka Event Bus** (Port 9092)

**30+ Event Topics**:

**Core Events**:
- `player.events` - Player CRUD operations
- `team.events` - Team updates
- `match.events` - Match data changes

**Live Events**:
- `match.live.updates` - Real-time match updates
- `match.goal.scored` - Goal events
- `match.substitution` - Substitution events

**Analytics Events**:
- `statistics.calculated` - Stats aggregations
- `ml.predictions` - ML model outputs
- `search.index.update` - Search index sync

### **Event Flow Example**

```
1. Match Service publishes: match.goal.scored
   ↓
2. Kafka distributes to:
   - Statistics Service → Updates aggregations
   - Search Service → Updates Elasticsearch
   - WebSocket Server → Broadcasts to clients
   - Notification Service → Sends alerts
   ↓
3. Frontend receives real-time update via WebSocket
```

---

## 🌐 **API Gateway (NGINX)**

### **Routing Rules**

```nginx
/api/players/*      → Player Service (8001)
/api/teams/*        → Team Service (8002)
/api/matches/*      → Match Service (8003)
/api/statistics/*   → Statistics Service (8004)
/api/ml/*           → ML Service (8005)
/api/search/*       → Search Service (8007)
ws://*/socket.io    → WebSocket Server (8080)
```

### **Features**
- Rate limiting: 100 requests/second
- CORS enabled for frontend
- Load balancing (when scaled)
- Health check aggregation
- SSL/TLS ready (commented out for dev)

---

## 🔐 **Authentication** (Planned)

**Current Status**: Disabled (`VITE_AUTH_ENABLED=false`)

**Planned Architecture**:
- JWT tokens
- OAuth2 integration
- Role-based access control (RBAC)
- API key management for external services

---

## 📊 **Monitoring Stack**

### **Metrics** (Prometheus - Port 9090)
- Service health metrics
- Request rates & latencies
- Error rates
- Business metrics (active matches, player queries)

### **Visualization** (Grafana - Port 3000)
- Service dashboards
- System health overview
- Custom business metrics
- **Status**: 🔴 Currently restarting

### **Tracing** (Jaeger - Port 16686)
- Distributed request tracing
- Service dependency mapping
- Performance bottleneck identification
- **Status**: 🔴 Not running

### **Log Aggregation** (ELK Stack)
- Centralized logging
- Log search & analysis
- **Status**: Partially configured

---

## 🚀 **Deployment Architecture**

### **Current: Docker Compose** (Development)
- Single-host deployment
- All services on one machine
- Suitable for development & testing

### **Planned: Kubernetes** (Production)
- Multi-node cluster
- Auto-scaling
- High availability
- Blue-green deployments
- **Status**: Infrastructure templates created, not deployed

---

## 📐 **Design Patterns Used**

1. **Microservices** - Independent, scalable services
2. **Event-Driven** - Asynchronous communication via Kafka
3. **CQRS** - Separate read/write models
4. **API Gateway** - Single entry point (NGINX)
5. **Service Discovery** - Docker DNS
6. **Circuit Breaker** - Fault tolerance in service clients
7. **Cache-Aside** - Redis caching strategy
8. **Repository Pattern** - Data access abstraction
9. **Pub-Sub** - WebSocket topic subscriptions

---

## 🔧 **Technology Stack**

### **Frontend**
- React 18.3
- TypeScript 5.5
- Vite 5.4
- TailwindCSS 3.4
- Recharts (visualizations)
- Socket.IO (WebSocket)

### **Backend**
- FastAPI 0.104+ (Python 3.11+)
- MongoDB 7.0 + MongoEngine
- Redis 7.0
- Kafka 7.5.0
- TimescaleDB (PostgreSQL 15)
- Elasticsearch 8.11

### **Infrastructure**
- Docker + Docker Compose
- NGINX (API Gateway)
- Prometheus + Grafana
- Jaeger
- Kafka UI

---

## 📈 **Scalability Considerations**

### **Horizontal Scaling**
- Each microservice can be scaled independently
- Kafka partitions for parallel processing
- Redis cluster for distributed caching
- MongoDB replica sets

### **Vertical Scaling**
- Increase resources per service
- Optimize queries
- Add caching layers

### **Current Limits** (Single Host)
- ~1000 concurrent users
- ~100 requests/second
- Real-time support for ~50 simultaneous matches

### **Scaled Limits** (Kubernetes Cluster)
- ~100,000 concurrent users
- ~10,000 requests/second
- Real-time support for 1000+ simultaneous matches

---

## 🎯 **Architecture Decisions**

### **Why Microservices?**
- **Scalability**: Scale individual services based on load
- **Isolation**: Failures contained to single services
- **Flexibility**: Use best tool for each job
- **Development**: Teams can work independently

### **Why Kafka?**
- **Throughput**: Handles 100,000+ events/second
- **Reliability**: Event persistence and replay
- **Decoupling**: Services don't need direct connections
- **Stream Processing**: Real-time analytics possible

### **Why Multiple Databases?**
- **MongoDB**: Flexible schema for changing data
- **TimescaleDB**: Optimized for time-series queries
- **Redis**: Sub-millisecond caching
- **Elasticsearch**: Full-text search capabilities

---

## 📚 **Further Reading**

- [Quick Start Guide](../01-getting-started/QUICK_START.md)
- [Implementation Guide](../03-development/IMPLEMENTATION_GUIDE.md)
- [Integration Guide](../04-integration/FRONTEND_BACKEND_INTEGRATION.md)
- [Current Status](../07-status/CURRENT_STATUS.md)
- [Roadmap](../07-status/ROADMAP.md)

---

**For detailed architectural specifications, see archived documents in `docs/archive/`**
