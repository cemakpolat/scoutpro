# Quick Reference - Event Enrichment API
## Fast lookup for endpoints, responses, and capabilities

---

## Endpoints at a Glance

### 1. Pass Statistics (Regional + Type Analysis)
```
GET /api/v2/events/passes/enhanced/player/{player_id}
GET /api/v2/events/passes/enhanced/team/{team_id}

Key Metrics:
- total_passes: 250 (typical)
- pass_types: long_passes, crosses, through_balls, etc.
- by_region: defensive_third, middle_third, attacking_third
- by_half: own_half, opponent_half
- set_piece_passes vs open_play_passes
- crosses_completed: completion rate
```

### 2. Shot Statistics (Location + Conversion)
```
GET /api/v2/events/shots/enhanced/player/{player_id}
GET /api/v2/events/shots/enhanced/team/{team_id}

Key Metrics:
- total_shots: 8 (typical)
- goals: conversion tracking
- by_location: inside_box vs outside_box
- by_foot: right_foot, left_foot, header
- big_chances: 3 (quality finishing)
- penalty_shots/penalty_goals
- shot_accuracy: percentage
- avg_distance_to_goal
```

### 3. Duel Statistics (Ground Duels - Success Rate)
```
GET /api/v2/events/duels/enhanced/player/{player_id}
GET /api/v2/events/duels/enhanced/team/{team_id}

Key Metrics:
- total_duels: 42 (typical)
- duels_won: 26
- duel_success_rate: 61.9% (typical)
- by_region: which third player dominates
- by_half: own_half vs opponent_half dominance
```

### 4. Tackle Statistics (Defensive Solidity)
```
GET /api/v2/events/tackles/enhanced/player/{player_id}
GET /api/v2/events/tackles/enhanced/team/{team_id}

Key Metrics:
- total_tackles: 18 (typical)
- successful_tackles: 14
- tackle_success_rate: 77.8% (typical)
- by_region: where player defends most
- by_direction: forward/backward/lateral threats
```

### 5. Ball Control Statistics (Touch Quality)
```
GET /api/v2/events/ball-control/enhanced/player/{player_id}
GET /api/v2/events/ball-control/enhanced/team/{team_id}

Key Metrics:
- total_touches: 105 (typical)
- successful_touches: 98
- touch_accuracy: 93.3% (typical)
- by_region: distribution across field
- by_half: own vs opponent half touches
- touches_in_box: attacking pressure measure
```

### 6. Foul Statistics (Discipline + Risk)
```
GET /api/v2/events/fouls/enhanced/player/{player_id}
GET /api/v2/events/fouls/enhanced/team/{team_id}

Key Metrics:
- total_fouls: 6 (typical)
- dangerous_fouls: risk level
- handball_fouls: specific infraction
- penalty_fouls: high-risk area fouls
- by_region: defensive hot spots
- in_penalty_box: red zone fouls
```

### 7. Take-On Statistics (Dribble Effectiveness)
```
GET /api/v2/events/take-ons/enhanced/player/{player_id}
GET /api/v2/events/take-ons/enhanced/team/{team_id}

Key Metrics:
- total_take_ons: 12 (typical)
- successful_take_ons: 9
- take_on_success_rate: 75.0% (typical)
- by_region: where player dribbles most
- in_own_half vs in_opponent_half
- in_box: attacking progression
```

---

## Field Zones (Spatial Reference)

```
                    ┌─────────────────────┐
                    │   ATTACKING THIRD   │
                    │    (x > 66.6)       │
                    │                     │
    ┌─ Penalty Box ─┤                     │
    │  (x>=83.3,    │                     │
    │   y:21-79)    │   ATTACKING 3RD     │
    │               │                     │
┌───┼───────────────┤   MIDDLE THIRD      │
│ D │               │   (33.3 < x ≤ 66.6)│
│ E │               │                     │
│ F │────────────────────────────────────│
│ E │               │   DEFENSIVE THIRD   │
│ N │               │   (x ≤ 33.3)        │
│ S │               │                     │
│ E │               │                     │
│   │  Defensive    │                     │
│ 3 │  Box          │                     │
│ R │ (x≤16.7,      │                     │
│ D │  y:21-79)     │                     │
└───┼───────────────┤                     │
    │               │   DEFENSIVE 3RD    │
    └─ Penalty Box ─┤                     │
                    └─────────────────────┘
```

---

## Opta Qualifier Meanings (Common)

| ID | Type | Usage | Example |
|---|---|---|---|
| 56 | Direction | Pass direction | "F" = Forward pass |
| 50 | Type | Cross indicator | Present = Cross pass |
| 1 | Type | Long pass | Present = Long distance |
| 4 | Type | Through ball | Present = Splitting defense |
| 155 | Type | Chipped pass | Present = Lofted pass |
| 87 | Shot | Big chance | Present = High quality shot |
| 39 | Shot | Penalty | Present = Penalty kick |
| 13 | Foul | Dangerous | Present = Reckless foul |
| 265 | Foul | Hand foul | Present = Handball |
| 152 | Foul | Penalty foul | Present = Foul in box |
| 233 | Duel | Distance | Numeric = Distance in duel |
| 285 | Duel | Outcome | Value = Won/lost indicator |

---

## Response Format (All Endpoints)

```json
{
  "success": true,
  "data": {
    // Event-type specific enrichments
    "total_X": number,
    "success_rate": percentage,
    "by_region": {
      "defensive_third": number,
      "middle_third": number,
      "attacking_third": number
    },
    "by_half": {
      "own_half": number,
      "opponent_half": number
    }
    // ... additional metrics per event type
  },
  "message": "Enhanced statistics retrieved successfully",
  "meta": null
}
```

---

## Quick Examples

### Get Player Pass Analysis
```bash
curl http://localhost:28004/api/v2/events/passes/enhanced/player/45230 | python3 -m json.tool
```

### Get Team Shot Statistics
```bash
curl http://localhost:28004/api/v2/events/shots/enhanced/team/2137 | python3 -m json.tool
```

### Filter by Season
```bash
curl "http://localhost:28004/api/v2/events/tackles/enhanced/player/45230?season_id=2019" | python3 -m json.tool
```

### Get All Defensive Metrics
```bash
# Duels
curl http://localhost:28004/api/v2/events/duels/enhanced/player/45230

# Tackles
curl http://localhost:28004/api/v2/events/tackles/enhanced/player/45230

# Fouls
curl http://localhost:28004/api/v2/events/fouls/enhanced/player/45230
```

---

## Metric Interpretations

### Success Rates
```
90%+ : World class (elite performers)
80-90% : Very good (starting XI quality)
70-80% : Solid (reliable performers)
60-70% : Average (league typical)
50-60% : Below average (struggling)
```

### Intensity Metrics (per 90)
```
10+ : Very high intensity (pressing/running)
5-10 : High intensity (active player)
3-5 : Moderate intensity (balanced role)
1-3 : Low intensity (defensive/positional)
```

### Regional Concentration
```
>60% in one region : Positionally fixed (full-back, striker)
40-60% in two regions : Flexible role (midfielder, winger)
Even 33% distribution : Box-to-box player (versatile)
```

---

## Common Questions Answered

**Q: Why does player X have low pass completion?**
A: Check `by_region` and `set_piece_passes` - may be making difficult passes or many set pieces.

**Q: How do I know if a player is a good shooter?**
A: Look at `big_chance_conversion` % and `shot_accuracy` %, not just goal count.

**Q: Does this player tackle well?**
A: Check `tackle_success_rate` - 75%+ is excellent, combined with `by_region` to understand defensive focus.

**Q: Which players are most involved in dribbling?**
A: Query `take-ons/enhanced/team` and look for highest `total_take_ons` with high success rate.

**Q: How to find dangerous passers?**
A: Look for high `crosses`, `through_balls`, and `key_passes` (Phase 2 feature).

**Q: Is this player fouling too much?**
A: Check `total_fouls` per match and `by_region` concentration. `dangerous_fouls` indicates recklessness.

---

## Performance Tips

### Cache Behavior
- First request: 50-200ms (MongoDB query + Python processing)
- Subsequent requests (within 5 min): <5ms (Redis cache hit)
- Tip: Browse player profiles to build cache, then analysis loads instantly

### Query Optimization
- Querying team data faster than individual player
- Filter by `season_id` to reduce data volume
- Plan: use team aggregations for overview, player for detail

### Best Practices
1. Cache player data when loading profile
2. Use team queries for squad overviews
3. Combine with player table for context
4. Store results in frontend for UI responsiveness

---

## Integration Notes

### With Analytics Lab
```javascript
// Fetch and display player stats
const stats = await fetch(`/api/v2/events/passes/enhanced/player/${playerId}`)
  .then(r => r.json())

// Build pass region chart
const regional = [
  { name: 'Defensive 3rd', value: stats.data.by_region.defensive_third.attempts },
  { name: 'Middle 3rd', value: stats.data.by_region.middle_third.attempts },
  { name: 'Attacking 3rd', value: stats.data.by_region.attacking_third.attempts }
]

// Render pie chart
renderChart('passRegions', regional)
```

### With Player Profile
```javascript
// Display on player card
const stats = await fetchStats(playerId, 'tackles')
card.innerHTML = `
  <div class="tackle-stats">
    <span>${stats.data.total_tackles} tackles</span>
    <span>${stats.data.tackle_success_rate.toFixed(1)}% success</span>
  </div>
`
```

---

## Data Freshness

- **Cache Duration:** 5 minutes (events change as matches progress)
- **Update Frequency:** Real-time from live data ingestion
- **Staleness:** Max 5 minutes old (acceptable for analytics)
- **Use Case:** Better suited for post-match analysis than live commentary

---

## Current Limitations

❌ **Not Yet Supported:**
- Expected goals (xG) - Phase 3 with ml-service
- Heat maps - Phase 3 requires visualization layer
- Expected assists (xA) - Phase 3 with ml-service
- Event sequences (pass→shot→goal) - Phase 2 coming
- Per-90 normalization - Phase 2 requires lineup data
- Position benchmarks - Phase 3 requires position clustering

✅ **Currently Working:**
- Raw event aggregations
- Regional analysis
- Success/accuracy rates
- Qualifier extraction
- Type classification
- Basic context (set piece vs open play)

---

## Debugging

### Check Service Status
```bash
curl http://localhost:28004/health
```

### View Service Logs
```bash
docker logs scoutpro-statistics-service --tail 50
```

### Test Database Connection
```bash
curl http://localhost:28004/api/v2/events/passes/enhanced/team/2137
# Should return pass stats if DB working
```

### Check Cache
```bash
docker exec scoutpro-redis redis-cli -a scoutpro123
> KEYS event:*
> GET event:pass:enhanced:45230:2137:None:None
```

---

## Related Services

- **match-service:** Provides match context (teams, dates, opponents)
- **player-service:** Provides player details (names, positions, teams)
- **ml-service:** Provides xG, xA models (Phase 3 integration)
- **search-service:** Indexes event stats for discovery (Phase 2)
- **api-gateway:** Proxies these endpoints to frontend

---

## Next Phase (Phase 2) - Coming Soon

```
New Event Types:
├─ Ball Recovery (92 records) - Transition analysis
├─ Interception (228 records) - Defensive intelligence
├─ Clearance (398 records) - Pressure measurement
├─ Goalkeeper (133 records) - Shot stopping
└─ Pressure (239 records) - Defensive intensity

New Capabilities:
├─ Event sequence linking (pass → shot → goal)
├─ Assist & key pass tracking
├─ Transition efficiency metrics
├─ Pressure effectiveness analysis
└─ Expected metric integration (xG, xA)

Timeline: 2-3 weeks
```

---

**Save this reference for quick endpoint lookups, metric interpretations, and integration patterns.**

