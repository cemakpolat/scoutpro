# 🎯 ScoutPro - Football Analytics & Scouting Platform

ScoutPro is a comprehensive microservices-based platform for **football (soccer) analysis, player scouting, and team intelligence**. It integrates data from multiple sources (Opta Sports, StatsBomb), provides advanced player similarity analysis, and delivers real-time match insights through an interactive dashboard.

## 🚀 Quick Start (3 Commands)

### Prerequisites
- **Docker & Docker Compose** installed
- At least 8GB RAM available
- Ports 80, 3001, 27017 accessible

### Start the System

```bash
# 1. Start all infrastructure and services
./manage.sh start

# 2. Load data from sample providers (Opta, StatsBomb)
./manage.sh seed

# 3. Open in browser
open http://localhost
```

**That's it!** The system will be ready in ~5-10 minutes.

## 📊 System Overview

### What Does ScoutPro Do?

1. **Data Ingestion** - Fetches football data from multiple providers (Opta API mock, StatsBomb CSVs)
2. **Data Processing** - Parses, normalizes, and enriches event-level data
3. **Analytics Engine** - Computes player/team statistics, performance metrics
4. **ML Features** - Generates embeddings for player similarity searches
5. **Real-time Dashboard** - Interactive UI for exploring players, teams, matches, and AI-powered insights

### Key Features

- 🔍 **Player Scout** - Find similar players using ML-based similarity search
- 📊 **Match Analytics** - Detailed event-level analysis (passes, shots, tackles, etc.)
- 👥 **Team Intelligence** - Squad composition, formation analysis, performance tracking
- 📈 **Statistics Dashboard** - Aggregated stats across competitions and seasons
- 🔗 **Multi-source Data** - Integrate Opta, StatsBomb, and custom data feeds
- ⚡ **Real-time Updates** - WebSocket-powered live notifications and updates

## 🏗️ Architecture

### High-Level Flow

```
Data Sources (Opta/StatsBomb)
         ↓
    data-provider (Mock HTTP API)
         ↓
    data-sync-service (Parse & normalize)
         ↓
    Kafka (Event stream)
         ↓
    Microservices (Player, Team, Match, Stats, ML)
         ↓
    MongoDB (Persistent storage)
         ↓
    API Gateway (REST + WebSocket)
         ↓
    React Frontend (Dashboard)
```

### Key Services

| Service | Port | Purpose |
|---------|------|---------|
| **nginx** | 80 | Reverse proxy, frontend serving |
| **api-gateway** | 3001 | REST API & WebSocket hub |
| **player-service** | 8001 | Player profiles, stats, enrichment |
| **team-service** | 8002 | Team management, formations |
| **match-service** | 8003 | Match data, events, timeline |
| **statistics-service** | 8004 | Aggregated stats computation |
| **ml-service** | 8012 | ML features, similarity models |
| **data-sync-service** | 28015 | Data ingestion pipeline |
| **websocket-server** | 8080 | Real-time notifications |

### Data Layer

- **MongoDB** (27017) - Primary data store (players, teams, matches, events)
- **Redis** (6379) - Caching & sessions
- **Kafka** (9092) - Event streaming between services
- **TimescaleDB** (5432) - Time-series analytics *(optional)*
- **Elasticsearch** (9200) - Full-text search *(optional)*

## 📋 Common Tasks

### Start/Stop Services

```bash
./manage.sh start          # Start minimal stack (fastest)
./manage.sh start --full   # Start all services including analytics
./manage.sh stop           # Gracefully stop (preserves data)
./manage.sh clean          # Remove all data & start fresh
./manage.sh restart        # Stop + start
```

### View System Status

```bash
./manage.sh status         # Check container health & data counts
./manage.sh logs           # Tail all service logs
./manage.sh logs api-gateway  # Tail specific service logs
```

### Data Management

```bash
./manage.sh seed           # Load sample data (teams, players, matches, events)
./manage.sh validate       # Run end-to-end integration checks
```

### Development

```bash
./manage.sh build          # Rebuild all Docker images from scratch
./manage.sh build api-gateway  # Rebuild specific service
```

## 🔗 Important URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost | Main dashboard |
| **API Gateway** | http://localhost:3001 | REST API (see OpenAPI spec at `/api/docs`) |
| **Grafana** | http://localhost:3000 | Monitoring dashboards *(optional)* |
| **Data Provider** | http://localhost:17000/api/feeds | Mock Opta API endpoint |

## 📚 Detailed Documentation

For in-depth guides, see the [`docs/`](docs/) directory:

- **[Getting Started](docs/01-getting-started/)** - Setup & quick reference
- **[Architecture](docs/02-architecture/)** - System design & data flow
- **[Development](docs/03-development/)** - Building services, manage.sh reference
- **[Integration](docs/04-integration/)** - Frontend-backend integration
- **[Status & Roadmap](docs/07-status/)** - What's working, what's planned

## 🛠️ Troubleshooting

### System won't start

```bash
# Check if Docker is running
docker info

# Check logs
./manage.sh logs

# Rebuild from scratch
./manage.sh clean
./manage.sh start
```

### Port already in use

```bash
# Find what's using port 80/3001/27017
lsof -i :80
lsof -i :3001
lsof -i :27017

# Or just clean and restart
./manage.sh clean
./manage.sh start
```

### Data didn't seed properly

```bash
# Check data-sync-service logs
./manage.sh logs data-sync-service

# Re-run seed
./manage.sh seed
```

### Frontend not loading

```bash
# Restart nginx
docker-compose restart nginx

# Check frontend build
ls -la frontend/dist/

# Rebuild if needed
docker-compose build nginx
```

## 📖 Environment Configuration

Default values (can be overridden via `.env` file):

```bash
# MongoDB
MONGO_ROOT_PASSWORD=scoutpro123
MONGODB_URL=mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin

# Data Pipeline
COMPETITION_ID=115          # Premier League ID
SEASON_ID=2019

# API Keys (if using real providers)
OPTA_API_KEY=<your-key>
STATSBOMB_API_KEY=<your-key>

# Service URLs
DATA_SYNC_URL=http://localhost:28015
```

## 🚀 Deployment

For production deployments, see:
- **[Kubernetes Guide](docs/05-deployment/)** - Container orchestration
- **[Docker Compose Reference](docs/03-development/MANAGE_COMMANDS.md)** - Service configuration

## 📝 Architecture Decisions

ScoutPro uses:
- **Microservices** - Independent, scalable services
- **Event-driven** - Kafka for asynchronous communication
- **MongoDB** - Flexible schema for football data
- **React + TypeScript** - Modern, type-safe frontend
- **Docker Compose** - Simple local development & easy deployment

## 🔄 Development Workflow

```bash
# 1. Make changes to a service
vim services/api-gateway/src/index.js

# 2. Rebuild the image
./manage.sh build api-gateway

# 3. Restart the service
docker-compose restart api-gateway

# 4. Check logs
./manage.sh logs api-gateway
```

For hot-reload during development, services with `volumes:` mounted in docker-compose.yml will auto-reload.

## 📊 Data Pipeline

The `./manage.sh seed` command runs a 4-phase pipeline:

1. **Phase 1** - Load teams, players, matches (Opta F1/F40 files)
2. **Phase 2** - Load match events (Opta F24 files)
3. **Phase 3** - Load match events (StatsBomb CSV files)
4. **Phase 4** - Compute aggregated statistics (player/team performance)

Sample data location: `./data/opta/` and `./data/statsbomb/`

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes and test: `./manage.sh validate`
3. Push and open a PR
4. Ensure CI passes and get review approval

## 📄 License

[Your License Here]

## 🆘 Support

- 📖 Check the [docs/](docs/) folder for detailed guides
- 🐛 File issues with clear reproduction steps
- 💬 Check existing issues before creating new ones

---

**Happy scouting! ⚽**
