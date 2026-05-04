# ScoutPro Operations & Statistics Aggregation

Guide to understanding statistics aggregation and system operations.

---

## What is Statistics Aggregation?

**Statistics aggregation** is the process of computing **summarized performance metrics** from raw match events.

### Raw Events vs. Statistics

**Raw Events** (match_events collection)
- Every single action in a match (99,897+ documents)
- Examples: Pass #5248 at minute 23 → successful, 15m pass to player X
- Granular but high-volume
- Used for: Advanced analytics, replays, detailed event analysis

**Statistics** (player_statistics, team_statistics collections)
- Pre-computed summaries per player per match
- Examples: Player scored 2 goals, made 45 passes, 38 were successful
- Compact and indexed for fast queries
- Used for: Player cards, scouting reports, leaderboards, comparisons

### Why Aggregate?

| Aspect | Raw Events | Statistics |
|--------|-----------|------------|
| Documents | 99,897+ | ~2,000 |
| Query speed | Slower (scans all events) | Fast (direct lookup) |
| Use case | Advanced analysis | UI, reports, summaries |
| Freshness | Immediate (as events arrive) | Periodically computed |

### Example

**Raw events for Player "Cenk Gönen" in match vs. Beşiktaş:**
```json
[
  {"id": "ev_1", "player_id": "p45230", "type": "pass", "minute": 5, "is_successful": true},
  {"id": "ev_2", "player_id": "p45230", "type": "pass", "minute": 7, "is_successful": true},
  {"id": "ev_3", "player_id": "p45230", "type": "tackle", "minute": 12, "is_successful": true},
  ... (total 87 events)
]
```

**Aggregated statistic for same player/match:**
```json
{
  "player_id": "p45230",
  "match_id": "ma_xyz",
  "passes": 68,
  "passes_successful": 61,
  "passes_accuracy": 89.7,
  "tackles": 4,
  "tackles_won": 3,
  "goals": 0,
  "shots": 2,
  "minutes_played": 90
}
```

---

## Statistics Computation Workflow

### Step 1: Raw Events Arrive

```
F24 files → OptaBatchSeeder → match_events (MongoDB)
```

Each event has:
- Event ID, type (pass, shot, tackle, etc.)
- Player ID, team ID, match ID
- Success/outcome
- Positions, qualifiers, timestamps
- ScoutPro IDs

### Step 2: Statistics Aggregation Runs

```
match_events → BatchAggregator → player_statistics, team_statistics
```

For each (player_id, match_id) pair:
1. Find all events for that player in that match
2. Count by event type
3. Sum successful/unsuccessful
4. Calculate percentages (e.g., pass accuracy)
5. Store in MongoDB

### Step 3: Statistics Available for Queries

```
player_statistics ← API ← Frontend
                 ← Reports
                 ← Analytics
```

---

## When Statistics Aggregation Runs

### Automatic (During Seeding)

```bash
./manage.sh seed
```

**Phase 3** automatically computes statistics after events are loaded.

```
Phase 1: Load teams, players, matches
Phase 2: Load 99,897 match events from F24
Phase 3: Compute player_statistics + team_statistics ← BatchAggregator
```

### Manual (On Demand)

If events are added after initial seeding:

```bash
# Trigger aggregation for all events
docker-compose exec -T statistics-service python3 - <<'EOF'
from services.batch_aggregator import BatchAggregator

agg = BatchAggregator(
    mongo_uri='mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin',
    db_name='scoutpro'
)

result = agg.run()  # Process all events
print(f"Aggregated: {result['player_docs']} player docs, {result['team_docs']} team docs")

agg.close()
EOF
```

### For a Specific Match

```bash
# Aggregate only events from one match
docker-compose exec -T statistics-service python3 - <<'EOF'
from services.batch_aggregator import BatchAggregator

agg = BatchAggregator()
result = agg.run(match_id="sp_ma_12345")  # Only this match
print(f"Match aggregated: {result}")

agg.close()
EOF
```

---

## Statistics Available in the System

### Player Statistics (player_statistics collection)

Per player per match:
- `passes` — Total pass attempts
- `passes_successful` — Passes that reached a teammate
- `pass_accuracy` — Percentage successful
- `crosses` — Crosses attempted
- `crosses_successful` — Successful crosses
- `shots` — Shot attempts
- `shots_on_target` — Shots on goal
- `goals` — Goals scored
- `tackles` — Tackle attempts
- `tackles_successful` — Tackles won
- `interceptions` — Interceptions
- `clearances` — Clearances
- `aerials` — Aerial duels
- `aerials_won` — Aerials won
- `fouls_committed` — Fouls
- `cards_yellow` — Yellow cards
- `cards_red` — Red cards
- `ball_recoveries` — Possessions regained
- `minutes_played` — Minutes on pitch

### Team Statistics (team_statistics collection)

Per team per match:
- `passes` — Team passing stats
- `passes_accurate` — Passing accuracy
- `shots` — Team shots
- `shots_on_target` — Shots on goal
- `possession` — Ball possession %
- `fouls_committed` — Team fouls
- `tackles` — Team tackles
- `interceptions` — Team interceptions
- `corners` — Corner kicks
- `crosses` — Team crosses
- `goals_for` — Goals scored
- `goals_against` — Goals conceded

---

## Monitoring Statistics Aggregation

### Check Document Counts

```bash
./manage.sh status
```

Look for:
```
MongoDB data counts:
  player_statistics:     1648      # Should match ~(players × matches)
  team_statistics:       612       # Should match ~(teams × matches)
```

### Verify Aggregation Worked

```bash
# Query a player's stats
docker-compose exec -T mongo mongosh 'mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin' \
  --eval 'db.player_statistics.findOne({}, {player_id: 1, passes: 1, goals: 1})'
```

Expected output:
```json
{
  "_id": ObjectId("..."),
  "player_id": "sp_pl_...",
  "passes": 45,
  "goals": 0
}
```

### Check for Errors

View statistics service logs:
```bash
./manage.sh logs statistics-service
```

Look for:
```
✅ BatchAggregator: wrote 1648 player docs, 612 team docs
```

Or error messages if aggregation failed.

---

## Troubleshooting Statistics

### Statistics Count is 0

**Problem:** `player_statistics` and `team_statistics` are empty after seeding.

**Solution:**
1. Check if events were loaded:
   ```bash
   ./manage.sh status  # Check match_events count
   ```
   
2. If events exist, manually trigger aggregation:
   ```bash
   docker-compose exec -T statistics-service python3 - <<'EOF'
   from services.batch_aggregator import BatchAggregator
   agg = BatchAggregator()
   result = agg.run()
   print(result)
   agg.close()
   EOF
   ```

3. Check for errors in logs:
   ```bash
   ./manage.sh logs statistics-service | grep -i error
   ```

### Stats Look Incorrect

**Problem:** Player stats don't match expected values.

**Solution:**
1. Verify raw events are correct:
   ```bash
   docker-compose exec -T mongo mongosh 'mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin' \
     --eval 'db.match_events.find({player_id: "sp_pl_..."}).count()'
   ```

2. Check event type categorization (passes, shots, etc.)
3. Examine a sample event to see structure:
   ```bash
   docker-compose exec -T mongo mongosh 'mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin' \
     --eval 'db.match_events.findOne({type_name: "pass"})'
   ```

---

## Performance Notes

### Aggregation Time

For ~100,000 events:
- **Single aggregation run:** 30-120 seconds (depends on CPU/disk)
- **Incremental updates:** Faster if only new matches are aggregated

### Optimization Tips

1. **Run aggregation during off-hours** if you have large datasets
2. **Aggregate per-match** if you're streaming live events:
   ```bash
   agg.run(match_id="sp_ma_xyz")  # Just one match
   ```
3. **Use batch aggregation** during data loads (automatic with `./manage.sh seed`)

---

## Next Steps

- Learn more: See [MANAGE_COMMANDS.md](MANAGE_COMMANDS.md) for `./manage.sh seed`
- Check data: `./manage.sh status`
- Query API: `curl http://localhost:3001/api/players?limit=1`
- Read architecture: `docs/02-architecture/`
