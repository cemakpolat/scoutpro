# Scout Pro Event Architecture & Evaluation System

## Overview

Events are the **foundation of all analytics** in Scout Pro. Every action that occurs during a match—passes, shots, tackles, aerial duels, etc.—is captured as an event. These events are then evaluated to compute comprehensive player, team, and match statistics used for scouting, analysis, and machine learning.

## Data Sources

### Opta Sports
- **Event Type**: F24 (detailed match events)
- **Format**: XML with event records containing:
  - `typeID`: Numeric event classification (1=Pass, 7=Tackle, 44=Aerial, etc.)
  - `outcome`: 0/1 (unsuccessful/successful)
  - Location (x, y coordinates 0-100)
  - Player/Team identifiers
  - Qualifiers (event modifiers like "Head", "Through Ball", etc.)

### StatsBomb
- **Event Type**: JSON events from StatsBomb API/data
- **Format**: Event objects with:
  - `type_name`: String event type (pass, shot, tackle, duel, etc.)
  - `location`: [x, y] coordinates
  - `end_location`: Destination (for passes, carries)
  - Provider metadata
  - Success/failure indicators

Both normalized into MongoDB `match_events` collection with consistent schema:
```json
{
  "event_id": "unique_id",
  "matchID": 1080974,
  "player_id": 51948,
  "team_id": 2137,
  "type_name": "pass",
  "provider": "opta" | "statsbomb",
  "location": {"x": 50, "y": 40},
  "end_location": {"x": 60, "y": 35},
  "is_successful": true,
  "is_goal": false,
  "minute": 25,
  "period": 1,
  "qualifiers": [...],
  "raw_event": {...}
}
```

## Event Evaluation Pipeline

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAW EVENTS (18,235)                      │
│  ┌──────────────────────┬──────────────────────┐            │
│  │   Opta F24 Events    │  StatsBomb Events    │            │
│  │      (15,113)        │      (3,122)         │            │
│  └──────────────────────┴──────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│          UNIFIED EVENT EVALUATOR (unified_event_evaluator.py)│
│                                                              │
│  Routes events based on type_name and provider:             │
│  - Pass evaluator: Completion rate, distance, direction     │
│  - Shot evaluator: On-target rate, location, xG             │
│  - Tackle evaluator: Success rate, position                 │
│  - Aerial evaluator: Win rate, location                     │
│  - Duel/Interception/Clearance/Recovery evaluators          │
│                                                              │
│  Computes:                                                   │
│  - Event counts by type                                      │
│  - Success rates                                             │
│  - Location heatmaps                                         │
│  - Distance metrics                                          │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│        PLAYER-MATCH EVENT AGGREGATIONS (305 docs)            │
│ ┌────────────────────────┬────────────────────────┐          │
│ │ unified_player_events_ │ unified_player_events_ │          │
│ │      opta (271)        │      statsbomb (34)    │          │
│ │                        │                        │          │
│ │ {player_id: 51948,     │ {player_id: 12498,     │          │
│ │  match_id: 1080974,    │  match_id: 3946949,    │          │
│ │  event_count: 45,      │  event_count: 97,      │          │
│ │  metrics: {            │  metrics: {            │          │
│ │    passes_total: 28,   │    passes_total: 23,   │          │
│ │    passes_successful:21│    tackles_total: 2    │          │
│ │    tackles_total: 3    │  },                    │          │
│ │  },                    │  pass_accuracy: 87.5%  │          │
│ │  pass_accuracy: 75%    │ }                      │          │
│ │ }                      │                        │          │
│ └────────────────────────┴────────────────────────┘          │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│        PLAYER CAREER STATISTICS (277 unified docs)           │
│                                                              │
│ {_id: 51948,                                                 │
│  opta_events: 45,                                            │
│  statsbomb_events: 0,                                        │
│  total_passes: 28,                                           │
│  successful_passes: 21,                                      │
│  pass_accuracy: 75.0,                                        │
│  total_shots: 3,                                             │
│  goals: 1,                                                   │
│  tackles: 3,                                                 │
│  interceptions: 2,                                           │
│  clearances: 1,                                              │
│  recoveries: 4,                                              │
│  last_updated: ISODate                                       │
│ }                                                            │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│            API GATEWAY ENDPOINTS                             │
│  /api/players/:id/detailed-stats                             │
│  /api/players/stats/leaders/passes                           │
│  /api/players/stats/leaders/aerials                          │
│  /api/players/stats/leaders/shooting                         │
│  /api/players/:id/match-stats/:matchId                       │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│            FRONTEND COMPONENTS                               │
│  PerformanceTracker - Display real player metrics            │
│  ScoutingDashboard - Top performers by events               │
│  PlayerComparison - Compare players' event statistics        │
│  TacticalAnalyzer - Match tactical patterns from events      │
└──────────────────────────────────────────────────────────────┘
```

### Event Types Supported

#### Pass Events
- Total passes, successful/unsuccessful
- Forward vs. backward
- Pass distance
- Pass accuracy: `successful_passes / total_passes * 100`

#### Shot Events
- Total shots, on-target, goals
- Shot location (heatmap)
- Shot efficiency: `goals / total_shots * 100`

#### Tackle Events
- Total tackles, successful/unsuccessful
- Tackle success rate

#### Aerial Events (Opta & StatsBomb)
- **Opta**: typeID=44, outcome 0=lost, 1=won
- **StatsBomb**: type_name "aerial" (won) vs "aerial lost" (lost)
- Aerial duels won/lost
- Success rate: `duels_won / total_duels * 100`
- Location-based aerial zones

#### Duel Events (StatsBomb)
- Duel success rate
- Duel locations

#### Defensive Events
- Interceptions
- Clearances
- Ball recoveries
- Fouls committed

### Metric Computation

**Pass Accuracy** (Example)
```
Player ID 51948 in Match 1080974:
  Passes: 28 total
  Successful: 21
  Accuracy: 21/28 * 100 = 75.0%
```

**Aerial Success Rate**
```
Player ID 51948 across all matches:
  Aerial Duels: 15 total
  Won: 9
  Success Rate: 9/15 * 100 = 60.0%
```

**Shot Efficiency**
```
Top Shooters (from leader endpoints):
  Player A: 3 goals / 8 shots = 37.5%
  Player B: 2 goals / 12 shots = 16.7%
```

## Integration Points

### 1. Data Ingestion
- Opta F24 files → Data Provider Mock → MongoDB `match_events`
- StatsBomb JSON → Data Provider Mock → MongoDB `match_events`
- All events normalized to common schema

### 2. Event Evaluation
```python
# Run periodically (e.g., after each match ingested)
from scripts.unified_event_evaluator import UnifiedEventEvaluator

evaluator = UnifiedEventEvaluator()
evaluator.process_all_events('both')  # Process Opta + StatsBomb
evaluator.close()
```

Creates/updates:
- `unified_player_events_opta` (271 documents)
- `unified_player_events_statsbomb` (34 documents)
- `unified_player_career_stats` (277 documents)

### 3. API Exposure
**New endpoints in API Gateway**:
```javascript
GET /api/players/:id/detailed-stats → Career statistics
GET /api/players/:id/match-stats/:matchId → Match breakdown
GET /api/players/stats/leaders/passes → Leaderboard
GET /api/players/stats/leaders/aerials → Leaderboard
GET /api/players/stats/leaders/shooting → Leaderboard
```

### 4. Frontend Display
**PerformanceTracker.tsx**:
```typescript
// Fetches unified event-based statistics
const stats = await apiService.getPlayerDetailedStats(playerId);
// Displays: passes, pass accuracy, shots, goals, tackles, aerials, etc.
```

## Current Status

| Provider | Events | Players | Coverage |
|----------|--------|---------|----------|
| **Opta F24** | 15,113 | 271 | 98.6% |
| **StatsBomb** | 3,122 | 34 | 1.4% |
| **Combined** | 18,235 | 277 | 100% |

## Machine Learning Integration

Events feed into:
1. **xG Models**: Shot location + player history → expected goals
2. **Player Rating Models**: Event frequency + efficiency → overall rating
3. **Team Tactics**: Pass patterns + locations → formation detection
4. **Injury Risk**: Player event load + intensity → fatigue/injury probability
5. **Transfer Value**: Event-based performance → market value estimation

## Next Steps

1. **Opta Coverage**: Enhance F24 event parsing for additional qualifiers
2. **StatsBomb Expansion**: Ingest more StatsBomb matches into the system
3. **Real-time Evaluation**: Trigger event evaluation as matches progress
4. **Advanced Metrics**: Add xG, progressive passes, PPDA, possession recovery zones
5. **Cross-provider Validation**: Verify Opta vs StatsBomb event consistency
6. **Complementary Strategy**: Implement match-level primary assignment and field-level merge rules when overlaps occur

## Multi-Provider Data Strategy

**See [MULTI_PROVIDER_STRATEGY.md](MULTI_PROVIDER_STRATEGY.md) for detailed architecture**

### Quick Reference

**Current State**:
- 10 Opta matches (15,113 events)
- 1 StatsBomb match (3,122 events)
- 0 overlapping matches (clean separation)

**Provider Hierarchy**:
1. **Primary**: Opta (baseline player/match statistics)
2. **Complementary**: StatsBomb (tactical enrichment, gap-fill)

**Field Merge Rules**:
- `passes_total`, `tackles`, `shots`, `goals` → Use Primary (Opta)
- `pressure_events`, `ball_recovery`, `carries` → Use Complementary only (StatsBomb)
- `interceptions`, `clearances` → Combine safely (non-conflicting)
- **Never double-count** the same event metric across providers

**Future Overlaps**:
When a match is covered by multiple providers, automatically:
1. Score providers by event count (40%) + temporal coverage (35%) + player diversity (25%)
2. Assign primary based on score + hierarchy
3. Use complementary for exclusive events only
4. Flag discrepancies >20% for manual review
