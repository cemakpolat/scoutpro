# ScoutPro — Simple Start/Stop/Seed Guide

**Get ScoutPro running with three simple commands.**

---

## Prerequisites

Before you start, ensure you have:

```bash
# Check Docker is installed and running
docker --version
docker ps

# Check Node.js is installed  
node --version
npm --version
```

If Docker isn't running, **start Docker Desktop** (macOS) or your Docker service.

---

## 🚀 Start the System (30 seconds)

Open terminal in the project root and run:

```bash
./manage.sh start
```

This starts:
- ✅ MongoDB (database)
- ✅ Kafka (event streaming)
- ✅ API Gateway (REST API on port 3001)
- ✅ All 25+ microservices
- ✅ Frontend support

Wait for all containers to be healthy (green). Then proceed to seeding.

---

## 🌱 Seed Your Data (5-10 minutes)

Load all Opta and StatsBomb data (teams, players, matches, events) and compute statistics:

```bash
./manage.sh seed
```

**What this does (4 phases):**
1. Loads 18 teams from the schedule file (F1)
2. Loads 571 players from squad lists (F40)
3. Loads 306 matches from the schedule (F1)
4. **Ingests ~437,000 Opta match events** from 306 F24 files (one event per action)
5. **Ingests StatsBomb events** from CSV files in `data/statsbomb/` (appended to `match_events`)
6. **Computes player statistics** from all events (passes, shots, tackles, etc. per match)
7. **Computes team statistics** from all events (possession, shots, etc. per match)

Expected final counts:
```
teams:                 18 ✅
players:               571 ✅
matches:               306 ✅
match_events:          ~437,000+ ✅  (Opta F24 + StatsBomb combined)
player_statistics:     ~7,200 ✅
team_statistics:       ~516 ✅
```

**Time estimate:** 30–60 minutes depending on machine speed (437k events to ingest).

---

## 🎯 Access the System

### Frontend (UI)
```
http://localhost:80
```
Log in with:
- Email: `admin@scoutpro.com`
- Password: `admin123`

### REST API
```
http://localhost:3001/api/players
http://localhost:3001/api/teams
http://localhost:3001/api/matches
```

### Check Service Health
```bash
./manage.sh status
```

Shows container health, database document counts, and API endpoint status.

---

## 🛑 Stop the System

### Graceful Stop (keep data)
```bash
./manage.sh stop
```

This stops all containers but **preserves all data** (teams, players, events, etc.).

### Full Reset (delete everything)
```bash
./manage.sh clean
```

**Warning:** This deletes all volumes. You'll need to run `./manage.sh seed` again.

---

## 📊 Verify Data Was Loaded

After seeding completes, check the database directly:

```bash
docker-compose exec -T mongo mongosh 'mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin' --eval \
  'db.teams.countDocuments({}) && db.players.countDocuments({}) && db.matches.countDocuments({}) && db.match_events.countDocuments({})'
```

Expected output:
```
18       # teams
571      # players  
306      # matches
~437000  # match_events (~1,430 events per match)
```

---

## 🔍 What is Statistics Aggregation?

The seed process computes **player and team statistics from raw match events**:

- **Player stats per match:** Passes, shots, tackles, interceptions, etc.
- **Team stats per match:** Possession %, shots on target, fouls, etc.

These statistics are:
- Automatically computed during `./manage.sh seed`
- Stored in MongoDB collections: `player_statistics` and `team_statistics`
- Used by the frontend to display player cards and match summaries
- Queryable via REST API endpoints

**Why separate?** Raw events can number in millions. Statistics provide efficient pre-computed summaries.

---

## ❓ Common Questions

### Q: Do I need API keys to run the system?
**A:** No. The system runs entirely offline with local Opta data in the `data/` folder.

Optional: Add external API keys (Opta, StatsBomb, Firebase, SendGrid) in `.env` for live data/enrichment.

### Q: Can I restart and keep the data?
**A:** Yes.
- `./manage.sh stop` → `./manage.sh start` preserves all data
- Use `./manage.sh clean` only if you want to fully reset

### Q: How do I inspect the database?
**A:** MongoDB is on `localhost:27017`. Connect with:
```bash
mongosh 'mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin'
```

### Q: Frontend not responding?
**A:** Check container health:
```bash
./manage.sh status
```

If frontend shows `WARN`, restart it:
```bash
docker-compose restart
./manage.sh start
```

---

## 📚 Next Steps

- **View match details:** http://localhost:5173 → Teams → Select a team → View matches
- **Check API responses:** `curl http://localhost:3001/api/players?limit=1`
- **Monitor events:** Open Kafka UI at http://localhost:28090 (advanced)
- **Read full docs:** See `docs/02-architecture/` for system design
