# ScoutPro Management Commands

Complete reference for `manage.sh` — the central command to control ScoutPro.

---

## Overview

`manage.sh` is a unified management script for starting, stopping, seeding, and inspecting the ScoutPro system.

```bash
./manage.sh <command> [options]
```

---

## Commands

### `start` — Start All Services

Starts the full ScoutPro stack (all Docker containers).

```bash
./manage.sh start
```

**What it does:**
- Starts MongoDB, Kafka, TimescaleDB, Redis, Zookeeper
- Starts API Gateway and all 25+ microservices
- Returns when all services are healthy

**Expected output:**
```
✅ All services started and healthy
```

**Time:** 30-60 seconds

---

### `stop` — Stop All Services

Stops all running containers **without deleting data**.

```bash
./manage.sh stop
```

**What it does:**
- Gracefully stops all containers
- Preserves all database volumes and data
- Allows you to restart with `./manage.sh start` later

**You can restart later:**
```bash
./manage.sh start
```

Data will still be there.

---

### `clean` — Full Reset (Delete Everything)

**⚠️ WARNING:** This deletes all data. Use only if you want to start fresh.

```bash
./manage.sh clean
```

**What it does:**
- Stops all containers
- Deletes all Docker volumes (teams, players, events, etc.)
- Removes containers

**To get data back:**
```bash
./manage.sh start
./manage.sh seed
```

---

### `seed` — Load All Data + Compute Statistics

**This is the main data ingestion command.**

```bash
./manage.sh seed
```

**What it does:**
1. **Phase 1 — Load Foundational Data** (teams, players, matches)
   - Parses F1 file (schedule) → 18 teams, 306 matches
   - Parses F40 file (squad lists) → 571 players
   - Assigns canonical ScoutProId to each entity

2. **Phase 2 — Load Match Events** (99,897 individual match events)
   - Parses all 306 F24 files (match event records)
   - Each file contains all actions from one match (passes, shots, fouls, etc.)
   - Assigns ScoutProId to each event
   - Stores raw and enriched event data

3. **Phase 3 — Compute Statistics**
   - Aggregates events into player statistics (passes, shots, tackles per match)
   - Aggregates events into team statistics (possession, shots, fouls per match)
   - Stores computed stats in MongoDB for fast queries

**Expected output:**
```
teams:                 18
players:               571
matches:               306
match_events:          99,897
player_statistics:     ~1,600
team_statistics:       ~500
```

**Time:** 5-15 minutes (depends on machine CPU/disk speed)

**Important:** Run this **after** `./manage.sh start`.

---

### `status` — Show System Status

Displays container health, database counts, API endpoints, and ScoutProId coverage.

```bash
./manage.sh status
```

**Shows:**
- ✅ / ⚠️ Container health (all 25+ services)
- 📊 MongoDB collection counts (teams, players, events, etc.)
- 🆔 ScoutProId coverage (% of entities with IDs)
- 🌐 API endpoint status (ports responding)

**Example output:**
```
Container health:
NAME                     STATUS              
scoutpro-api-gateway    Up 5 minutes (healthy)
scoutpro-mongo          Up 5 minutes (healthy)
...

MongoDB data counts:
  players:              571
  teams:                18
  matches:              306
  match_events:         99897
  player_statistics:    1648
  team_statistics:      0

Service endpoints:
[  OK  ] api-gateway (port 3001)
[ WARN ] frontend (port 5173) not responding
```

---

### `validate` — Check Data Integrity

Validates that data was loaded correctly (ScoutProId coverage, event counts, etc.).

```bash
./manage.sh validate
```

**Checks:**
- All teams have scoutpro_id
- All players have scoutpro_id
- All matches have scoutpro_id
- Events have proper structure and IDs
- Statistics were computed

**Returns exit code 0 if all checks pass.**

---

### `logs` — View Service Logs

Show real-time logs from a service.

```bash
./manage.sh logs <service-name>
```

**Examples:**
```bash
./manage.sh logs api-gateway       # API Gateway logs
./manage.sh logs mongo             # MongoDB logs
./manage.sh logs data-sync-service # Data sync logs
./manage.sh logs statistics-service # Statistics aggregation logs
```

**To tail (follow) logs:**
```bash
./manage.sh logs api-gateway --tail=50
```

---

### `restart` — Restart All Services

Stops and restarts all containers (preserves data).

```bash
./manage.sh restart
```

Equivalent to:
```bash
./manage.sh stop
./manage.sh start
```

---

## Complete Workflow Examples

### Example 1: Fresh System Setup
```bash
./manage.sh start        # Start services (wait ~1 min)
./manage.sh seed         # Load data + compute stats (wait ~5-10 min)
./manage.sh status       # Verify everything loaded
```

Then access: http://localhost:5173

### Example 2: Restart After Shutdown
```bash
./manage.sh stop         # Stop services
# ... do other things ...
./manage.sh start        # Start services (data still there)
./manage.sh status       # Verify services are healthy
```

### Example 3: Full Reset
```bash
./manage.sh clean        # ⚠️ Delete everything
./manage.sh start        # Start empty system
./manage.sh seed         # Reload fresh data
./manage.sh status       # Verify
```

### Example 4: Debugging a Specific Service
```bash
./manage.sh status       # Check if service is unhealthy
./manage.sh logs <service-name>  # View its logs
./manage.sh restart      # Try restarting
./manage.sh status       # Verify it's back
```

---

## Return Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Command completed ✅ |
| 1 | Failure | Check error message, see logs |
| 127 | Command not found | Check spelling of command |

---

## Environment Variables

Control behavior with environment variables:

```bash
# Set data root (default: ./data/opta/2019)
DATA_ROOT=/path/to/data ./manage.sh seed

# Set MongoDB URI (default: mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin)
MONGODB_URL=mongodb://... ./manage.sh seed

# Set log level (default: INFO)
LOG_LEVEL=DEBUG ./manage.sh seed
```

---

## Troubleshooting

### Services not starting?
```bash
./manage.sh status    # Check which service failed
./manage.sh logs <service-name>  # See why it failed
```

### Data not loaded?
```bash
./manage.sh seed      # Re-run seeding
./manage.sh status    # Verify counts
```

### Need a full reset?
```bash
./manage.sh clean     # Delete everything
./manage.sh start     # Start fresh
./manage.sh seed      # Load data again
```

### Port already in use?
```bash
# Kill whatever is on port 3001 (API Gateway)
lsof -ti:3001 | xargs kill -9

# Restart
./manage.sh start
```

---

## Next Steps

- **Access frontend:** http://localhost:5173
- **Query API:** `curl http://localhost:3001/api/players`
- **Check data:** `./manage.sh status`
- **Read full docs:** See `docs/01-getting-started/QUICK_START_SIMPLE.md`
