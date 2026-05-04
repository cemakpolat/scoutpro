# ScoutPro — Getting Started Guide

Advanced football scouting analytics platform. This guide covers everything you need to run, log in to, and stop ScoutPro on a local development machine.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Quick Start (Recommended)](#2-quick-start-recommended)
3. [First-Time Login](#3-first-time-login)
4. [Service URLs & Ports](#4-service-urls--ports)
5. [Credentials Reference](#5-credentials-reference)
6. [Starting the System](#6-starting-the-system)
7. [Stopping the System](#7-stopping-the-system)
8. [Data Overview](#8-data-overview)
9. [Scripts Reference](#9-scripts-reference)
10. [Common Troubleshooting](#10-common-troubleshooting)

---

## 1. Prerequisites

| Tool | Minimum Version | Check |
|------|-----------------|-------|
| Docker Desktop | 24.x | `docker --version` |
| Docker Compose | v2.x (bundled) | `docker compose version` |
| Node.js | 18.x | `node --version` |
| npm | 9.x | `npm --version` |
| Python | 3.11+ | `python3 --version` |

> **macOS:** Docker Desktop for Mac includes both Docker and Docker Compose.  
> Ensure Docker Desktop is **running** before executing any script.

---

## 2. Quick Start (Recommended)

```bash
# Clone and enter the repository
git clone <repo-url> scoutpro
cd scoutpro

# Start MongoDB (Docker) + API Gateway (Node) + Frontend (Vite)
./start-dev.sh
```

On **first run** the script automatically seeds the database with sample players, teams, and matches.

Open your browser at **http://localhost:5173** and log in with the credentials in [Section 3](#3-first-time-login).

---

## 3. First-Time Login

| Role | Email | Password |
|------|-------|----------|
| Administrator | `admin@scoutpro.com` | `admin123` |

After login you will land on the **Players** page. From there you can:

- Search and filter players by position, nationality, age, and statistics
- Compare players side-by-side
- View match events, heatmaps, and tactical overlays
- Generate and export PDF scouting reports

> To create additional users, log in as admin, navigate to **Settings → User Management**, and invite new accounts.

---

## 4. Service URLs & Ports

### End-User Interfaces

| Service | URL | Notes |
|---------|-----|-------|
| **Frontend** | http://localhost:5173 | Vite dev server (dev mode) |
| **Frontend** (production) | http://localhost:80 | Served via Nginx (full Docker stack) |
| **API Gateway** | http://localhost:3001/api | REST API entry point |
| **Health Check** | http://localhost:3001/health | Returns `{"status":"ok"}` |
| **WebSocket** | ws://localhost:3001/ws | Live match events |

### Microservices (internal, for debugging)

| Service | Port | Description |
|---------|------|-------------|
| player-service | 28001 | Player profiles, statistics |
| team-service | 28002 | Squad management |
| match-service | 28003 | Match events, lineups |
| statistics-service | 28004 | Aggregated stats |
| ml-service | 28005 | ML models, predictions |
| live-ingestion-service | 28006 | Real-time data ingestion |
| search-service | 28007 | Elasticsearch-backed search |
| notification-service | 28008 | Alerts and push notifications |
| report-service | 28009 | PDF scouting reports |
| export-service | 28010 | Data export (CSV, JSON) |
| video-service | 28011 | Video clip management |
| analytics-service | 28012 | Advanced analytics |
| websocket-server | 28080 | WebSocket bridge |

### Infrastructure UIs

| Tool | URL | Notes |
|------|-----|-------|
| **Kafka UI** | http://localhost:28090 | Browse topics and messages |
| **MinIO Console** | http://localhost:9001 | Object storage browser |
| **MLflow UI** | http://localhost:5000 | Experiment tracking |
| **Elasticsearch** | http://localhost:9200 | Search engine API |
| **Mongo (via port)** | localhost:27017 | Use any MongoDB client |
| **TimescaleDB** | localhost:5432 | PostgreSQL-compatible |
| **Redis** | localhost:6379 | Cache / pub-sub |

---

## 5. Credentials Reference

### Application

| Resource | Username / Key | Password / Value |
|----------|---------------|-----------------|
| App Admin | `admin@scoutpro.com` | `admin123` |

### Infrastructure (development defaults — do not use in production)

| Resource | Username | Password |
|----------|----------|----------|
| MongoDB | `root` | `scoutpro123` |
| MongoDB database | — | `scoutpro` |
| Redis | — | `scoutpro123` |
| TimescaleDB | `scoutpro` | `scoutpro123` |
| MinIO | `minioadmin` | `minioadmin123` |
| Kafka | no auth (dev) | — |

### Optional external providers (set in `.env`)

```bash
OPTA_API_KEY=<your_opta_key>
OPTA_WEBSOCKET_URL=<wss://opta-live-url>
STATSBOMB_API_KEY=<your_statsbomb_key>
SENDGRID_API_KEY=<your_sendgrid_key>
FIREBASE_CREDENTIALS=<json_blob>
```

> Without these keys the system runs in **offline/local mode** using the sample data in `data/`. See [Section 8](#8-data-overview).

---

## 6. Starting the System

Three ways to start ScoutPro, from simplest to most complete:

### Option A — Development Mode (fastest, recommended for daily work)

```bash
./start-dev.sh
```

Starts: MongoDB (Docker container) + API Gateway (Node.js process) + Frontend (Vite dev server).

**First-run options:**

```bash
./start-dev.sh --seed    # Force re-seed the database
./start-dev.sh --reset   # Full reset: remove containers, reinstall deps, reseed
```

### Option B — Local Mode with `.env` file

```bash
# 1. Copy the template and fill in your keys
cp .env.backend.example .env
nano .env   # or use your editor

# 2. Start
./start-local.sh
```

This script additionally creates required directories and `init-scripts/` if missing.

### Option C — Full Docker Stack (all services including microservices)

```bash
# Start all services (infrastructure + all microservices + frontend via Nginx)
docker-compose up -d

# Or start only infrastructure + gateway for a lighter stack
docker-compose up -d mongo redis kafka zookeeper api-gateway

# Check running containers
docker-compose ps

# View logs for a specific service
docker-compose logs -f api-gateway
docker-compose logs -f player-service
```

### Option D — Mock Data Provider (offline / no external API keys)

If you want to run the system without connecting to real Opta or StatsBomb servers, start the local provider server mock:

```bash
cd providers/data-provider-mock
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 7000 --reload
```

> **Docker note:** when running via the full Docker Compose stack, the data-provider is accessible from the host at `http://localhost:17000` (mapped from internal port 7000). Other containers reach it at `http://data-provider:7000`.

Or via Docker Compose with the data profile:

```bash
docker-compose -f docker-compose.yml -f docker-compose.data.yml up -d
```

The mock server exposes the same feed endpoints as the real providers, reading from `data/opta/` and `data/statsbomb/`. See [DATA_PROVIDER_MOCK.md](../03-development/DATA_PROVIDER_MOCK.md) for API reference.

### Option E — Initial Data Seeding (Recommended for New Setup)

When deploying the system on a new machine, use the **data seeder** to automatically load all sample data:

```bash
./seed-data.sh
```

This one-command operation:
1. ✅ Starts the required infrastructure (MongoDB, Kafka, TimescaleDB, Redis, Zookeeper, data-provider mock)
2. ✅ Parses all local Opta feeds (F1, F9, F24, F40) and StatsBomb events from the `data/` folder
3. ✅ Normalizes and ingests data through the full pipeline: Kafka → MongoDB/TimescaleDB
4. ✅ Enriches player records with biometrics (height, weight, nationality)
5. ✅ Links team names and player names to matches and events
6. ✅ Auto-removes the seeder container when complete

**Typical execution time:** 5–15 minutes (depending on machine specs).

**After seeding completes**, start the full system:

```bash
docker compose up -d
```

Then open http://localhost:5173 in your browser.

#### Seeding Options

```bash
# Skip Docker image rebuild (use cached image if available)
./seed-data.sh --no-build

# Manual steps (if you prefer to control each phase)
docker compose up -d zookeeper kafka mongo timescaledb redis data-provider
docker compose -f docker-compose.yml -f docker-compose.seed.yml run --rm data-seeder
```

#### Verify Data Was Loaded

```bash
# Connect to MongoDB and check counts
docker exec scoutpro-mongo mongosh -u root -p scoutpro123 --authenticationDatabase admin \
  --eval 'db = db.getSiblingDB("scoutpro"); print(JSON.stringify({
    players: db.players.countDocuments(),
    teams: db.teams.countDocuments(),
    matches: db.matches.countDocuments(),
    match_events: db.match_events.countDocuments(),
    player_statistics: db.player_statistics.countDocuments(),
    events_with_player_names: db.match_events.countDocuments({"player_name": {"$ne": null}})
  }))'

# Expected output (Turkish Süper Lig, competition 115, season 2019/2020):
# { players: 571, teams: 18, matches: 306, match_events: 96688,
#   player_statistics: 376, events_with_player_names: ~85000 }
```

#### Post-Seeding: StatsBomb Enrichment

After seeding, trigger the StatsBomb enrichment to add advanced metrics (xG, OBV) to players
from the Samsunspor vs Beşiktaş match:

```bash
# Requires the full stack to be running (docker-compose up -d)
curl -X POST http://localhost/api/players/enrich/statsbomb
# Returns: {"matched": N, "updated": N, "unmatched": N, "errors": []}
```

#### If Enrichment Scripts Fail (Troubleshooting)

If the seeder exits successfully but player statistics or player names are missing, run the
enrichment scripts manually inside a running container:

```bash
# Copy scripts into data-sync-service container
docker cp scripts/enrich_f40.py scoutpro-data-sync-service:/tmp/enrich_f40.py
docker cp scripts/enrich_matches_and_events.py scoutpro-data-sync-service:/tmp/enrich_matches_and_events.py
docker cp data/opta/2019/f40_115_2019 scoutpro-data-sync-service:/tmp/f40_115_2019

# Run F40 biometric enrichment (preferred_foot, height, birth_date)
docker exec -e F40_PATH=/tmp/f40_115_2019 scoutpro-data-sync-service python3 /tmp/enrich_f40.py

# Run event and statistics enrichment (player names on events, goal/pass aggregation)
docker exec -e MONGO_URI="mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin" \
  scoutpro-data-sync-service python3 /tmp/enrich_matches_and_events.py
```

---

## 7. Stopping the System

### Development Mode (Option A / B)

Press **Ctrl+C** in the terminal running the startup script. This stops the API Gateway and frontend dev server.

MongoDB keeps running in Docker. To stop it as well:

```bash
docker-compose down          # Stop and remove containers (data preserved in volumes)
docker-compose down -v       # Stop AND delete all data volumes (full reset)
```

### Full Docker Stack (Option C)

```bash
docker-compose down          # Stop all containers, keep data
docker-compose down -v       # Stop all containers, delete all data
```

### Stop individual services

```bash
docker-compose stop api-gateway
docker-compose stop mongo redis
```

### Kill stale processes on ports (if a process didn't shut down cleanly)

```bash
# Kill whatever is running on the API Gateway port
lsof -ti:3001 | xargs kill -9

# Kill whatever is running on the frontend port  
lsof -ti:5173 | xargs kill -9
```

---

## 8. Data Overview

The `data/` folder contains local match data that the system can use without external API keys.

```
data/
├── opta/
│   ├── f24_115_2017_935592          # F24 match events — season 2017 (single match)
│   └── 2019/
│       ├── f1_115_2019              # F1 squads (team lineups for Turkish Super Lig)
│       ├── f9_115_2019              # F9 squads-latest (all teams, full season)
│       ├── f24_115_2019_108xxxx     # F24 event files (~300 matches, full season)
│       └── f40_115_2019             # F40 fixtures & results
└── statsbomb/
    └── Samsunspor_Besiktas_3946949.csv   # StatsBomb event data (single match)
```

**Dataset context:** Turkish Süper Lig, competition ID `115`, season `2019` (2019/2020).  
This is real match data — all player IDs, event coordinates, and timestamps are authentic.

### Feed type reference

| Feed | Content | Format |
|------|---------|--------|
| **F1** | Squad list per team | XML / JSON |
| **F9** | Full squads (all teams) at a point in time | XML / JSON |
| **F24** | All in-match events (passes, shots, tackles…) per match | XML / JSON |
| **F40** | Fixtures and results for the competition | XML / JSON |
| **StatsBomb events** | Fine-grained event data with OBV, xG, tracking | CSV / JSON |

---

## 9. Scripts Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `./seed-data.sh` | **[NEW]** Full data seeding in one command (recommended for new setup) | `./seed-data.sh [--no-build]` |
| `./start-dev.sh` | Start MongoDB + API Gateway + Frontend (dev) | `./start-dev.sh [--seed] [--reset]` |
| `./start-local.sh` | Start with `.env` configuration | `./start-local.sh` |
| `./test-opta-integration.sh` | Smoke-test Opta data ingestion | `./test-opta-integration.sh` |
| `scripts/start-backend.sh` | Start backend services only | `./scripts/start-backend.sh` |
| `scripts/create-kafka-topics.sh` | Create required Kafka topics | `./scripts/create-kafka-topics.sh` |
| `scripts/ingest_real_data.py` | Ingest local Opta/StatsBomb files into MongoDB | `python3 scripts/ingest_real_data.py` |
| `scripts/gateway_smoke.py` | HTTP smoke-test all API Gateway routes | `python3 scripts/gateway_smoke.py` |

### Database seeding (manual)

```bash
cd services/api-gateway
node src/seed.js
```

### Ingesting local Opta data

```bash
# Ingest all available data files into MongoDB
python3 scripts/ingest_real_data.py

# Test that the Opta feed integration works end-to-end
./test-opta-integration.sh
```

---

## 10. Common Troubleshooting

### "MongoDB not ready after 30s"

```bash
# Check if Docker is running
docker info

# Check MongoDB container logs
docker logs scoutpro-mongo

# Restart just MongoDB
docker-compose restart mongo
```

### Port already in use

```bash
# Find what's on port 3001
lsof -i :3001
# Kill it
lsof -ti:3001 | xargs kill -9
```

### API returns 401 Unauthorized

Your JWT token has expired. Log out and log back in.  
Tokens are signed with `JWT_SECRET=scoutpro-secret-key-2025` (dev only).

### Frontend shows "Cannot connect to API"

1. Confirm the API Gateway is running: `curl http://localhost:3001/health`
2. Check that `VITE_API_URL` in `frontend/.env.local` points to `http://localhost:3001/api`

### Kafka / microservices not starting

```bash
# Kafka requires Zookeeper to be healthy first
docker-compose up -d zookeeper
docker-compose logs -f zookeeper  # wait for "binding to port 2181"
docker-compose up -d kafka
```

### Full reset

```bash
# Stop everything and wipe all data volumes
docker-compose down -v

# Restart fresh with a re-seed
./start-dev.sh --reset
```

---

*For architecture details see [docs/02-architecture/OVERVIEW.md](../02-architecture/OVERVIEW.md).*  
*For implementation guidance see [docs/03-development/IMPLEMENTATION_GUIDE.md](../03-development/IMPLEMENTATION_GUIDE.md).*
