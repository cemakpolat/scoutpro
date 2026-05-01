# Phase 1 Event Enrichments - Implementation Guide
## Advanced Analytics & Regional Analysis

**Created:** April 2026  
**Service:** statistics-service  
**Architecture:** find() + Python enrichment (data-reliable approach)

---

## Overview

Implemented **Phase 1 enrichments** with focus on:
- **Regional spatial analysis** (thirds, halves, penalty boxes)
- **Qualifier extraction** (pass types, shot quality, foul context)
- **Context awareness** (set piece vs open play)
- **Success rate tracking** (duels, tackles, touches)

---

## Architecture Components

### 1. FieldZones (Spatial Analysis)
Divides field into regions for positional analytics:

```python
# Field Third Divisions (by x coordinate)
- 0-33.3: Defensive Third
- 33.3-66.6: Middle Third
- 66.6-100: Attacking Third

# Half Divisions
- 0-50: Own Half
- 50-100: Opponent Half

# Box Regions
- Penalty Box: x >= 83.3 AND 21.1 <= y <= 78.9
- Defensive Box: x <= 16.7 AND 21.1 <= y <= 78.9
```

**Usage:**
```python
region = zones.get_region(x_coordinate)  # Returns "attacking_third", "middle_third", etc.
half = zones.get_half(x_coordinate)      # Returns "own_half" or "opponent_half"
in_box = zones.in_box(location_dict)     # Returns True/False
```

### 2. QualifierExtractor (Opta Data Intelligence)
Maps 300+ Opta qualifier IDs to meaningful analytics:

#### Pass Qualifiers
```
ID 56:  Pass direction (F=Forward, B=Back, L/R=Lateral, S=Straight)
ID 50:  Cross indicator (presence = cross pass)
ID 1:   Long pass indicator
ID 4:   Through ball indicator
ID 155: Chipped pass indicator
ID 6:   Corner cross
ID 107: Throw-in
ID 123: Goal kick
```

#### Set Piece Qualifiers
```
ID 24:  Direct free kick
ID 25:  Indirect free kick
ID 26:  From corner
```

#### Shot Qualifiers
```
ID 87:  Big chance indicator
ID 39:  Penalty indicator
ID 355: Blocked shot
```

#### Defensive Qualifiers
```
ID 13:  Dangerous foul
ID 265: Hand foul
ID 152: Foul in penalty area (penalty foul)
```

#### Duel Qualifiers
```
ID 233: Duel distance
ID 285: Duel outcome (won/lost)
```

---

## Implemented Enrichment Functions

### 1. ENHANCED PASS STATISTICS

**Endpoint:** `GET /api/v2/events/passes/enhanced/player/{player_id}`  
**Endpoint:** `GET /api/v2/events/passes/enhanced/team/{team_id}`

**Response Structure:**
```json
{
  "total_passes": 250,
  "by_region": {
    "defensive_third": {
      "attempts": 85,
      "forward": 45,
      "backward": 30,
      "lateral": 10
    },
    "middle_third": {
      "attempts": 120,
      "forward": 70,
      "backward": 35,
      "lateral": 15
    },
    "attacking_third": {
      "attempts": 45,
      "forward": 30,
      "backward": 5,
      "lateral": 10
    }
  },
  "by_half": {
    "own_half": {"attempts": 140},
    "opponent_half": {"attempts": 110}
  },
  "pass_types": {
    "long_passes": 35,
    "through_balls": 8,
    "crosses": 12,
    "corner_crosses": 3,
    "chipped_passes": 5,
    "throw_ins": 4,
    "goal_kicks": 2
  },
  "set_piece_passes": 12,
  "open_play_passes": 238,
  "passes_in_box": 8,
  "passes_into_box": 15,
  "crosses_completed": 6,
  "open_play_completion": 95.2
}
```

**Analytics Insight:**
- Track pass progression by field region
- Identify set piece vs open play distribution
- Measure crossing efficiency
- Analyze pass directions by zone (defensive vs attacking patterns)

---

### 2. ENHANCED SHOT STATISTICS

**Endpoint:** `GET /api/v2/events/shots/enhanced/player/{player_id}`  
**Endpoint:** `GET /api/v2/events/shots/enhanced/team/{team_id}`

**Response Structure:**
```json
{
  "total_shots": 8,
  "goals": 2,
  "shots_on_target": 4,
  "shots_off_target": 3,
  "blocked_shots": 1,
  "by_location": {
    "inside_box": 6,
    "outside_box": 2,
    "inside_box_goals": 2,
    "outside_box_goals": 0
  },
  "by_foot": {
    "right_foot": 5,
    "left_foot": 2,
    "header": 1,
    "other": 0
  },
  "big_chances": 3,
  "big_chance_conversion": 66.7,
  "penalty_shots": 1,
  "penalty_goals": 1,
  "avg_distance_to_goal": 28.5,
  "shot_accuracy": 25.0
}
```

**Analytics Insight:**
- Conversion rates by location (box vs outside)
- Big chance efficiency (quality finishing indicator)
- Shooting accuracy (shots on target %)
- Penalty prowess
- Shot distribution by foot/head

---

### 3. ENHANCED DUEL STATISTICS

**Endpoint:** `GET /api/v2/events/duels/enhanced/player/{player_id}`  
**Endpoint:** `GET /api/v2/events/duels/enhanced/team/{team_id}`

**Response Structure:**
```json
{
  "total_duels": 42,
  "duels_won": 26,
  "duels_lost": 16,
  "duel_success_rate": 61.9,
  "by_region": {
    "defensive_third": 18,
    "middle_third": 16,
    "attacking_third": 8
  },
  "by_half": {
    "own_half": 22,
    "opponent_half": 20
  }
}
```

**Analytics Insight:**
- Duel dominance metric
- Regional duel distribution (where player wins most)
- Defensive vs attacking duel performance
- Physical capability assessment

---

### 4. ENHANCED TACKLE STATISTICS

**Endpoint:** `GET /api/v2/events/tackles/enhanced/player/{player_id}`  
**Endpoint:** `GET /api/v2/events/tackles/enhanced/team/{team_id}`

**Response Structure:**
```json
{
  "total_tackles": 18,
  "successful_tackles": 14,
  "tackle_success_rate": 77.8,
  "by_region": {
    "defensive_third": 12,
    "middle_third": 5,
    "attacking_third": 1
  },
  "by_direction": {
    "forward": 10,
    "backward": 5,
    "lateral": 3
  }
}
```

**Analytics Insight:**
- Defensive solidity (tackle success rate)
- Positional breakdown (concentration in defensive third)
- Tackle timing (forward/backward indicates anticipation vs recovery)

---

### 5. ENHANCED BALL CONTROL STATISTICS

**Endpoint:** `GET /api/v2/events/ball-control/enhanced/player/{player_id}`  
**Endpoint:** `GET /api/v2/events/ball-control/enhanced/team/{team_id}`

**Response Structure:**
```json
{
  "total_touches": 105,
  "successful_touches": 98,
  "touch_accuracy": 93.3,
  "by_region": {
    "defensive_third": 35,
    "middle_third": 45,
    "attacking_third": 25
  },
  "by_half": {
    "own_half": 55,
    "opponent_half": 50
  },
  "touches_in_box": 3
}
```

**Analytics Insight:**
- Touch consistency/control (accuracy %)
- Involvement by zone (where most active)
- Box presence (attacking intent)
- Ball security

---

### 6. ENHANCED FOUL STATISTICS

**Endpoint:** `GET /api/v2/events/fouls/enhanced/player/{player_id}`  
**Endpoint:** `GET /api/v2/events/fouls/enhanced/team/{team_id}`

**Response Structure:**
```json
{
  "total_fouls": 6,
  "dangerous_fouls": 1,
  "handball_fouls": 0,
  "penalty_fouls": 1,
  "by_region": {
    "defensive_third": 4,
    "middle_third": 1,
    "attacking_third": 1
  },
  "in_penalty_box": 1
}
```

**Analytics Insight:**
- Discipline assessment (total fouls + type breakdown)
- Risk analysis (fouls in penalty area)
- Defensive style (where fouls committed most)
- Tactical awareness (dangerous vs non-dangerous)

---

### 7. ENHANCED TAKE-ON STATISTICS

**Endpoint:** `GET /api/v2/events/take-ons/enhanced/player/{player_id}`  
**Endpoint:** `GET /api/v2/events/take-ons/enhanced/team/{team_id}`

**Response Structure:**
```json
{
  "total_take_ons": 12,
  "successful_take_ons": 9,
  "take_on_success_rate": 75.0,
  "by_region": {
    "defensive_third": 2,
    "middle_third": 4,
    "attacking_third": 6
  },
  "in_own_half": 2,
  "in_opponent_half": 10,
  "in_box": 1,
  "into_box": 0
}
```

**Analytics Insight:**
- Dribbling effectiveness (success rate)
- Risk profile (takes place mostly in attacking third)
- Threat creation (dribbles into box)
- Playmaking style (how much player uses ball progression via dribbles)

---

## Data Flow Architecture

```
Raw MongoDB Events
    ↓
[find()] - Retrieve matching documents
    ↓
Python Processing
    ├─ FieldZones: Regional categorization
    ├─ QualifierExtractor: Opta data enrichment
    ├─ Success tracking: is_successful flag analysis
    └─ Aggregation: Count/sum/rate calculations
    ↓
Statistics Dict
    ↓
[Redis Cache] 300s TTL
    ↓
API Response
```

**Advantages:**
- ✅ Guaranteed data access (no aggregation issues)
- ✅ Flexible enrichment logic (easy to add new calculations)
- ✅ Debuggable Python code (vs MongoDB pipeline syntax)
- ✅ Extensible patterns (add new zones, qualifiers, metrics)

---

## Integration with Frontend

### Analytics Lab Usage

The enhanced endpoints provide rich data for visualization:

```javascript
// Fetch player pass analysis
const passData = await fetch(`/api/v2/events/passes/enhanced/player/45230`)
const passes = await passData.json()

// Build regional heatmap
const regional = {
  defensive: passes.by_region.defensive_third.attempts,
  middle: passes.by_region.middle_third.attempts,
  attacking: passes.by_region.attacking_third.attempts
}

// Display pass type distribution
const passTypes = {
  long_passes: passes.pass_types.long_passes,
  through_balls: passes.pass_types.through_balls,
  crosses: passes.pass_types.crosses
}

// Calculate efficiency metrics
const efficiency = {
  set_piece_pct: (passes.set_piece_passes / passes.total_passes) * 100,
  open_play_pct: (passes.open_play_passes / passes.total_passes) * 100
}
```

---

## Performance Characteristics

### Caching Strategy
- **TTL:** 300 seconds (5 minutes)
- **Key Pattern:** `event:{type}:enhanced:{player_id}:{team_id}:{competition_id}:{season_id}`
- **Hit Rate:** Estimated 70-80% for repeated views in Analytics Lab

### Database Query Performance
- **Find() Operation:** O(n) on indexed filters (player_id, team_id, type_name)
- **Python Processing:** O(n) single pass through documents
- **Total Time:** ~50-200ms for 100-500 events per query

### Optimization Opportunities
1. **Batch processing:** Aggregate multiple players at once
2. **Materialized views:** Pre-compute daily aggregations
3. **Streaming:** Update stats in real-time via Kafka
4. **Search indexing:** Index pre-computed stats in search-service for discovery

---

## Next Steps

### Phase 2 (Context Awareness)
- [ ] Event sequence linking (dribble → shot → goal)
- [ ] Assist/key pass tracking
- [ ] Pressure effectiveness analysis
- [ ] Recovery → possession outcome linkage
- [ ] Transition metrics (fast break detection)

### Phase 3 (Advanced Intelligence)
- [ ] Heat map generation (density maps by position)
- [ ] Composite performance indices (scoring system)
- [ ] Expected metrics integration (xG, xA from ml-service)
- [ ] Player similarity clustering (role-based)

### Phase 4 (ML Features)
- [ ] Feature engineering for xG/xA models
- [ ] Time-series statistics (form trending)
- [ ] Positional benchmarking
- [ ] Player rating aggregation

---

## Testing Queries

### Test Pass Enrichments
```bash
# Player pass analysis
curl http://localhost:28004/api/v2/events/passes/enhanced/player/45230

# Team pass analysis  
curl http://localhost:28004/api/v2/events/passes/enhanced/team/2137

# Expected response: Regional breakdown with 250+ passes
```

### Test Shot Enrichments
```bash
# Player shooting analysis
curl http://localhost:28004/api/v2/events/shots/enhanced/player/45230

# Team shooting analysis
curl http://localhost:28004/api/v2/events/shots/enhanced/team/2137

# Expected response: Location analysis, big chances, conversion rates
```

### Test Defensive Enrichments
```bash
# Player duel/tackle analysis
curl http://localhost:28004/api/v2/events/duels/enhanced/player/45230
curl http://localhost:28004/api/v2/events/tackles/enhanced/player/45230

# Team defensive analysis
curl http://localhost:28004/api/v2/events/duels/enhanced/team/2137
curl http://localhost:28004/api/v2/events/tackles/enhanced/team/2137

# Expected response: Success rates, regional breakdown
```

---

## Qualifier Reference (Extended)

| Qualifier ID | Category | Meaning | Usage |
|---|---|---|---|
| 56 | Direction | F=Forward, B=Back, L=Left, R=Right, S=Straight | Pass direction analysis |
| 50 | Type | Cross indicator | Cross identification |
| 1 | Type | Long pass | Long ball tracking |
| 4 | Type | Through ball | Creative pass metrics |
| 155 | Type | Chipped pass | Pass style breakdown |
| 6 | Type | Corner cross | Set piece analysis |
| 107 | Type | Throw-in | Restart tracking |
| 123 | Type | Goal kick | Set play identification |
| 24 | Set Piece | Direct free kick | Free kick metrics |
| 25 | Set Piece | Indirect free kick | Free kick metrics |
| 26 | Set Piece | From corner | Corner efficiency |
| 87 | Shot | Big chance | Finishing quality |
| 39 | Shot | Penalty | Penalty tracking |
| 355 | Shot | Blocked | Defensive action |
| 13 | Foul | Dangerous foul | Discipline analysis |
| 265 | Foul | Hand foul | Handball tracking |
| 152 | Foul | Penalty foul | Box fouls |
| 233 | Duel | Distance | Duel intensity |
| 285 | Duel | Outcome | Duel success |

---

## Code Examples

### Get Pass Statistics for a Player
```python
player_id = "45230"
team_id = None

aggregator = EnhancedEventAggregator(db_client, redis_client)
stats = await aggregator.get_pass_statistics_enhanced(
    player_id=player_id,
    team_id=team_id
)

# Stats now contains:
# - Regional breakdown (which third most active)
# - Pass types (crosses, through balls, long passes)
# - Context (set piece vs open play)
# - Efficiency metrics
```

### Get Duel Statistics for a Team
```python
team_id = "2137"

stats = await aggregator.get_duel_statistics_enhanced(
    team_id=team_id
)

# Stats now contains:
# - Total duels and success rate
# - Regional concentration
# - Half-based analysis
```

### Extract Qualifier Information
```python
from services.event_aggregator_enhanced import QualifierExtractor

extractor = QualifierExtractor()
qualifiers = {"56": "F", "50": "1", "24": "1"}

direction = extractor.get_pass_direction(qualifiers)  # "forward"
pass_types = extractor.get_all_pass_types(qualifiers)  # ["forward", "cross", "free_kick_direct"]
is_cross = extractor.has_qualifier(qualifiers, "50")   # True
```

---

## Summary

Phase 1 enrichments enable:
1. **Spatial Analytics** - Where players are active and successful
2. **Qualifier Intelligence** - What types of actions they take
3. **Context Awareness** - Set piece vs open play patterns
4. **Performance Metrics** - Success rates and efficiency
5. **Scalable Architecture** - Easy to add more enrichments

This foundation supports Phase 2-4 advanced analytics and ML integration.
