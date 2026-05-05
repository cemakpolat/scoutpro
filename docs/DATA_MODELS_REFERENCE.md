# ScoutPro Data Models Reference

## Overview
ScoutPro uses a unified data model that unifies data from multiple providers (Opta, StatsBomb, etc.) under a single ScoutPro ID system. The architecture maintains backward compatibility by storing both canonical ScoutPro IDs and provider-specific IDs.

---

## 1. PLAYER MODEL

### Data Structure
```json
{
  "success": true,
  "data": {
    "id": "5558184549703700944",
    "provider_ids": {
      "opta": "51521"
    },
    "opta_uid": "p51521",
    "name": "Mustapha Yatabare",
    "first_name": "Mustapha",
    "last_name": "Yatabare",
    "position": "Striker",
    "detailed_position": null,
    "age": 38,
    "nationality": "France",
    "club": "Sivasspor",
    "height": "183",
    "weight": "78",
    "shirt_number": 9,
    "preferred_foot": "right",
    "birth_date": "1986-01-26",
    "team_name": "Sivasspor",
    "team_id": "9100682411166030939",
    "statsbomb_enrichment": null
  },
  "message": "Player retrieved successfully"
}
```

### Fields Description
| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `id` | string (64-bit) | **Canonical ScoutPro ID** - provider-agnostic, unique globally | System Generated |
| `provider_ids` | object | Maps provider → their ID (e.g., `{opta: "51521"}`) | Opta F40, StatsBomb, etc. |
| `opta_uid` | string | Legacy Opta unique ID with prefix (e.g., `p51521`) | Opta F40 |
| `name` | string | Full player name | Opta F40 |
| `first_name` | string | Given name | Opta F40 |
| `last_name` | string | Surname | Opta F40 |
| `position` | string | Standardized position (GK, DF, MF, FW) | Opta F40 |
| `detailed_position` | string | More specific position (e.g., LW, RB, CDM) | Opta F40 |
| `age` | integer | Current age | Calculated from birth_date |
| `nationality` | string | Primary nationality | Opta F40 |
| `club` | string | Current club name | Opta F40 |
| `height` | string | Height in cm | Opta F40 |
| `weight` | string | Weight in kg | Opta F40 |
| `shirt_number` | integer | Squad number | Opta F40 |
| `preferred_foot` | string | "left", "right", or "both" | Opta F40 |
| `birth_date` | string (ISO 8601) | Date of birth | Opta F40 |
| `team_name` | string | Name of current team | Opta F40 |
| `team_id` | string (64-bit) | **Canonical ScoutPro Team ID** | System Generated |
| `statsbomb_enrichment` | object | Advanced StatsBomb metrics (xG, OBV, etc.) | StatsBomb |

### API Endpoints
- **GET** `/api/v2/players/:id` - Get single player
- **GET** `/api/v2/players?limit=50&offset=0` - List players

---

## 2. TEAM MODEL

### Data Structure
```json
{
  "success": true,
  "data": {
    "id": "t2137",
    "name": "Sivasspor",
    "short_name": null,
    "country": null,
    "founded": null,
    "stadium": null,
    "capacity": null,
    "manager": null
  },
  "message": "Team retrieved successfully"
}
```

### Fields Description
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | **Canonical ScoutPro Team ID** (format: `t<numeric_id>`) |
| `name` | string | Official team name |
| `short_name` | string | Abbreviated name (e.g., "SIV") |
| `country` | string | Home country |
| `founded` | integer | Year founded |
| `stadium` | string | Home stadium name |
| `capacity` | integer | Stadium capacity |
| `manager` | string | Current manager name |

### API Endpoints
- **GET** `/api/v2/teams/:id` - Get single team
- **GET** `/api/v2/teams?limit=50&offset=0` - List teams

---

## 3. MATCH MODEL

### Data Structure
```json
{
  "success": true,
  "data": {
    "id": "g1081277",
    "home_team_id": "6780335221349570185",
    "away_team_id": "4876448671545579524",
    "home_team_name": "Yeni Malatyaspor",
    "away_team_name": "Gaziantep",
    "home_score": 2,
    "away_score": 1,
    "date": "2020-07-26 16:00:00",
    "status": "finished",
    "match_day": 1,
    "competition_id": "115",
    "season_id": "2019",
    "venue": "Malatya Stadium",
    "competition": "Super Lig"
  },
  "message": "Retrieved 1 matches"
}
```

### Fields Description
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique match identifier |
| `home_team_id` | string | **Canonical ScoutPro Home Team ID** |
| `away_team_id` | string | **Canonical ScoutPro Away Team ID** |
| `home_team_name` | string | Home team name |
| `away_team_name` | string | Away team name |
| `home_score` | integer | Goals scored by home team |
| `away_score` | integer | Goals scored by away team |
| `date` | string (ISO datetime) | Match date and time |
| `status` | string | `"scheduled"`, `"live"`, `"finished"`, `"postponed"`, `"cancelled"` |
| `match_day` | integer | Round/matchday number in competition |
| `competition_id` | string | Competition identifier |
| `season_id` | string | Season year (e.g., "2019") |
| `venue` | string | Stadium name |
| `competition` | string | Competition name (e.g., "Super Lig") |

### API Endpoints
- **GET** `/api/v2/matches/:id` - Get single match (if detail endpoint exists)
- **GET** `/api/v2/matches?limit=50&offset=0&status=finished` - List matches

---

## 4. STATISTICS MODEL

### 4a. Player Statistics (Season Aggregate)

```json
{
  "success": true,
  "data": {
    "player_id": "5558184549703700944",
    "player_name": "Mustapha Yatabare",
    "stats": {
      "matches_played": 27,
      "team_id": "9100682411166030939",
      "opta_team_id": "2137",
      "scoutpro_player_id": "5558184549703700944",
      "scoutpro_team_id": "9100682411166030939",
      "competition_id": "115",
      "season_id": "2019",
      "passes": 633,
      "passes_successful": 353,
      "crosses": 0,
      "shots": 82,
      "shots_on_target": 38,
      "goals": 12,
      "assists": 0,
      "tackles": 14,
      "interceptions": 8,
      "clearances": 26,
      "fouls_committed": 61,
      "yellow_cards": 5,
      "red_cards": 0,
      "ball_recoveries": 0,
      "aerials": 0,
      "aerials_won": 0,
      "total_xg": 0.0,
      "high_regains": 0,
      "pass_accuracy": 55.77,
      "data_source": "player_statistics_aggregate"
    }
  }
}
```

**Purpose**: Aggregate season statistics across all matches a player participated in.

| Stat | Description |
|------|-------------|
| `matches_played` / `appearances` | Total appearances in season |
| `passes` | Total successful passes |
| `passes_successful` | Completed passes |
| `pass_accuracy` | Percentage of successful passes |
| `shots` / `total_shots` | Total shot attempts |
| `shots_on_target` | Shots on target |
| `goals` | Goals scored |
| `assists` / `goal_assist` | Assists provided |
| `tackles` / `total_tackles` | Tackles made |
| `interceptions` / `total_interceptions` | Interceptions |
| `clearances` / `total_clearances` | Defensive clearances |
| `fouls_committed` | Fouls committed by player |
| `yellow_cards` | Yellow cards received |
| `red_cards` | Red cards received |
| `aerials` / `aerial_duels` | Total aerial challenges |
| `aerials_won` | Won aerial duels |
| `ball_recoveries` | Regains of possession |

### API Endpoints
- **GET** `/api/v2/statistics/player/:player_id` - Get player season stats
- **GET** `/api/v2/player/:player_id/statistics` - Alternative endpoint

---

### 4b. Team Statistics (Season Aggregate)

```json
{
  "success": true,
  "data": {
    "team_id": "9100682411166030939",
    "opta_team_id": "2137",
    "team_name": "Sivasspor",
    "matches_played": 29,
    "passes": 12582,
    "passes_successful": 9348,
    "shots": 1557,
    "goals": 51,
    "tackles": 458,
    "interceptions": 322,
    "clearances": 514,
    "fouls": 804,
    "yellow_cards": 98,
    "red_cards": 2,
    "pass_accuracy": 74.3,
    "data_source": "team_statistics_aggregate"
  }
}
```

**Purpose**: Aggregate season statistics for an entire team.

### API Endpoints
- **GET** `/api/v2/statistics/team/:team_id` - Get team season stats

---

### 4c. Match Statistics (Box Score + Timeline)

```json
{
  "success": true,
  "data": {
    "match_id": "1080974",
    "home_team_id": "5259723502838043962",
    "away_team_id": "9100682411166030939",
    "opta_home_team_id": "378",
    "opta_away_team_id": "2137",
    "home_team_name": "Besiktas",
    "away_team_name": "Sivasspor",
    "home_goals": 0,
    "away_goals": 3,
    "home_passes": 643,
    "away_passes": 400,
    "home_pass_accuracy": 75.2,
    "away_pass_accuracy": 68.5,
    "home_corners": 12,
    "away_corners": 5,
    "home_tackles": 68,
    "away_tackles": 45,
    "home_interceptions": 42,
    "away_interceptions": 31,
    "home_clearances": 89,
    "away_clearances": 56,
    "home_fouls": 18,
    "away_fouls": 22,
    "home_yellow_cards": 3,
    "away_yellow_cards": 2,
    "home_red_cards": 0,
    "away_red_cards": 0,
    "goal_events": [
      {
        "minute": 34,
        "player": "Sinan Gümüş",
        "team": "Sivasspor",
        "type": "open_play"
      },
      {
        "minute": 67,
        "player": "Olarenwaju Kayode",
        "team": "Sivasspor",
        "type": "open_play"
      },
      {
        "minute": 89,
        "player": "Robson de Souza",
        "team": "Sivasspor",
        "type": "open_play"
      }
    ],
    "yellow_card_events": [...],
    "red_card_events": [],
    "substitution_events": [...],
    "total_events": 2847,
    "first_half_end": 2341,
    "match_end": 2847
  }
}
```

**Purpose**: Per-match box score (possession, shots, passes, etc.) plus event timeline (goals, cards, subs).

### API Endpoints
- **GET** `/api/v2/statistics/match/:match_id` - Get match box score and timeline

---

## 5. ANALYTICS MODEL

### Definition
**Analytics** are derived insights built from statistics:
- **Time-series trends** (rolling averages, form metrics)
- **Comparative rankings** (percentile vs. peers)
- **Predictive models** (injury risk, performance decay)
- **Tactical patterns** (pass network, heat maps)
- **Advanced metrics** (xG, xA, progressive actions)

### Architecture
```
Raw Events (F1, F24) 
    ↓
Statistics (Aggregated by player/team/match)
    ↓
Analytics (Derived insights)
    ↓
Frontend Dashboards (Visualizations)
```

### Types of Analytics
1. **Player Form Analysis**
   - Last 5/10 match averages
   - Trend indicators (↑ improving, ↓ declining)
   - Consistency score

2. **Competitive Rankings**
   - Position-group percentiles (e.g., "Strikers in Top 5 Leagues")
   - Market value correlation
   - Scout rating comparisons

3. **Match Tactical Analysis**
   - Pass network visualization
   - Heat maps (touch maps)
   - Pressing intensity map
   - Expected goals (xG) timeline

4. **Team Dynamics**
   - Formation detection
   - Player role clustering
   - Set-piece patterns

5. **Predictive Analytics** (ML-Service)
   - Player injury probability
   - Performance trajectory
   - Market transfer probability
   - Contract renewal likelihood

### Analytics Service Integration
- **Service**: `ml-service` (port 28008)
- **Capabilities**: Model training, ranking generation, trend analysis
- **Consumer**: `AnalyticsDashboard` component

---

## 6. DATABASE SCHEMA SUMMARY

### Collections

| Collection | Purpose | Key Fields |
|------------|---------|-----------|
| `players` | Player master data | `id`, `provider_ids`, `name`, `position` |
| `teams` | Team master data | `id`, `provider_ids`, `name`, `country` |
| `matches` | Match metadata | `id`, `home_team_id`, `away_team_id`, `date`, `status` |
| `match_events` | Raw event data (F1, F24) | `match_id`, `type_name`, `player_id`, `min`, `sec` |
| `player_statistics` | Per-match player stats | `match_id`, `player_id`, `goals`, `passes`, ... |
| `team_statistics` | Per-match team stats | `match_id`, `team_id`, `goals`, `passes`, ... |
| `match_statistics` | Per-match box score + timeline | `match_id`, `home_goals`, `away_goals`, `goal_events` |

### ID Formats

| Type | Format | Example | Origin |
|------|--------|---------|--------|
| **Player** | 64-bit string | `5558184549703700944` | UUID5 from `opta:<uid>` |
| **Team** | Prefixed string | `t2137` or string ID | UUID5, prefixed `t` |
| **Match** | String | `g1081277` or `1080974` | Opta match ID, `g` prefix |
| **Opta Provider** | Short numeric | `51521` (player), `2137` (team) | Original Opta ID |

---

## 7. KEY DESIGN PRINCIPLES

### 1. **Provider Agnostic**
- All primary keys use **ScoutPro IDs** (64-bit strings)
- Provider IDs stored in `provider_ids` map for reference
- Allows seamless integration of future providers (StatsBomb, Wyscout, etc.)

### 2. **Backward Compatibility**
- Legacy Opta IDs (`p51521`, `t2137`) available in `opta_uid`, `opta_*_id` fields
- Existing queries can still use Opta IDs via resolution layer
- Deprecation path for external consumers

### 3. **Data Hierarchy**
```
Raw Events → Statistics → Analytics → UI
```

- **Raw**: F1/F24 event streams
- **Statistics**: Season/match aggregates
- **Analytics**: Derived insights (trends, rankings)
- **UI**: Dashboards, reports, comparisons

### 4. **Immutability for Core Records**
- Player, team, match records are immutable (create new versions)
- Statistics are recalculated from raw events when pipeline runs
- Analytics are regenerated on schedule or on-demand

---

## 8. PAGINATION & FILTERING

### Standard Query Parameters
```
GET /api/v2/players?limit=50&offset=0&position=Striker&nationality=France&club=Sivasspor
```

| Param | Type | Default | Max |
|-------|------|---------|-----|
| `limit` | integer | 50 | 500 |
| `offset` | integer | 0 | — |
| `sort` | string | `name` | `name`, `position`, `age` |
| `order` | string | `asc` | `asc`, `desc` |

### Match Filters
```
GET /api/v2/matches?status=finished&season_id=2019&competition_id=115&limit=100
```

---

## 9. RESPONSE FORMAT

All API responses follow this envelope:

```json
{
  "success": true,
  "data": { ... },
  "message": "Human-readable description",
  "meta": {
    "page": 1,
    "limit": 50,
    "total": 1234,
    "timestamp": "2025-10-28T17:30:00Z"
  }
}
```

On error:
```json
{
  "success": false,
  "error": {
    "code": "PLAYER_NOT_FOUND",
    "message": "Player with ID 'xyz' not found",
    "details": {}
  }
}
```

---

## 10. MIGRATION CHECKLIST FOR NEW PROVIDERS

When adding a new data provider (e.g., StatsBomb, Wyscout):

- [ ] Define player mapping algorithm (name, position, birth_date)
- [ ] Define team mapping algorithm (name, country, found date)
- [ ] Store provider IDs in `provider_ids` map
- [ ] Implement conflict detection (if same player in two providers)
- [ ] Add merge strategy (which provider takes precedence)
- [ ] Update statistics pipeline to ingest new event types
- [ ] Add data quality metrics
- [ ] Create validation tests

