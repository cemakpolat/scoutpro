# ScoutPro Services Functions Audit

**Date**: May 6, 2026  
**Purpose**: Comprehensive inventory of all functions in analytics, statistics, player, team, and match services, plus shared utilities for parsing and batch operations. This document helps identify missing functions for recalculating player, team, and match statistics from event data.

---

## 1. ANALYTICS SERVICE

**Location**: `services/analytics-service/`

### 1.1 API Endpoints (`api/endpoints/analytics.py`)

#### Dashboard Endpoints
- `GET /api/v2/analytics/dashboard/overview` → `get_overview_dashboard(season)`
- `GET /api/v2/analytics/dashboard/team/{team_id}` → `get_team_dashboard(team_id, season)`
- `GET /api/v2/analytics/dashboard/player/{player_id}` → `get_player_dashboard(player_id, season)`

#### Trends & Rankings
- `GET /api/v2/analytics/trends/league` → `get_league_trends(competition, metric, period)`
- `GET /api/v2/analytics/rankings/players` → `get_player_rankings(metric, position, limit)`
- `GET /api/v2/analytics/rankings/teams` → `get_team_rankings(competition, metric, limit)`

#### Advanced Metrics
- `GET /api/v2/analytics/advanced-metrics/{match_id}` → `get_advanced_metrics(match_id, time_bucket)`
- `GET /api/v2/analytics/match/{match_id}/player/{player_id}/stats` → `get_match_player_stats(match_id, player_id)`

#### Insights
- `GET /api/v2/analytics/insights/team/{team_id}` → `get_team_insights(team_id)`
- `GET /api/v2/analytics/insights/player/{player_id}` → `get_player_insights(player_id)`
- `GET /api/v2/analytics/insights/player/{player_id}/sequences` → `get_player_sequence_insights(player_id)`
- `POST /api/v2/analytics/insights/players/sequences` → `get_player_sequence_coverage(player_ids)`

#### Comparison
- `GET /api/v2/analytics/comparison/players` → `compare_players(player_ids, metrics)`
- `POST /api/v2/analytics/comparison/players` → `compare_players_post(request)`
- `GET /api/v2/analytics/comparison/teams` → `compare_teams(team_ids, metrics)`
- `POST /api/v2/analytics/comparison/teams` → `compare_teams_post(request)`

#### Network & Tactical
- `GET /api/v2/analytics/pass-network/{match_id}` → `get_pass_network(match_id)`
- `GET /api/v2/analytics/tactical/{match_id}` → `get_tactical_metrics(match_id)`
- `GET /api/v2/analytics/sequences/{match_id}` → `get_sequence_insights(match_id)`

#### Multi-Match & Spatial Analysis
- `POST /api/v2/analytics/multi-match` → `get_multi_match_analytics(match_ids)`
- `GET /api/v2/analytics/player/{player_id}/shots-map` → `get_player_shot_map(player_id, last_n)`
- `GET /api/v2/analytics/player/{player_id}/heat-map` → `get_player_heat_map(player_id, event_type, last_n)`
- `GET /api/v2/analytics/player/{player_id}/pass-map` → `get_player_pass_map(player_id, last_n)`

### 1.2 Analytics Handler (`services/analytics_handler.py`)

#### Internal Handler Methods
- `get_overview(season)` - Loads players, matches, teams from dependent services
- `get_team_dashboard(team_id, season)` - Fetches from statistics service
- `get_player_dashboard(player_id, season)` - Fetches from statistics service
- `get_league_trends(competition, metric, period)` - Trends from statistics service
- `get_player_rankings(metric, position, limit)` - Rankings from statistics service
- `get_team_rankings(competition, metric, limit)` - Rankings from statistics service
- `get_advanced_metrics(match_id, time_bucket)` - From MatchProjectionBuilder
- `get_team_insights(team_id)` - From statistics service
- `get_player_insights(player_id)` - From statistics service
- `get_player_sequence_insights(player_id, match_limit=6)` - Builds sequences from events
- `get_player_sequence_coverage(player_ids)` - Batch sequence analysis
- `compare_players(player_ids, metrics)` - From statistics service
- `compare_teams(team_ids, metrics)` - From statistics service
- `get_pass_network(match_id)` - MatchProjectionBuilder.build_pass_network()
- `get_tactical_metrics(match_id)` - MatchProjectionBuilder.build_tactical_snapshot()
- `get_sequence_insights(match_id)` - MatchProjectionBuilder.build_sequence_summary()
- `get_multi_match_analytics(match_ids)` - Aggregates across multiple matches
- `get_player_shot_map(player_id, last_n_matches)` - Spatial analysis from events
- `get_player_heat_map(player_id, event_type, last_n_matches)` - Event locations
- `get_player_pass_map(player_id, last_n_matches)` - Pass locations from events
- `get_match_player_stats(match_id, player_id)` - Per-match player aggregation

#### Helper Methods Used in Analytics Handler
- `_build_sequences(events, match, include_event_refs)` - Constructs possession sequences
- `_build_team_sequence_summary(team_id, team_name, sequences, rapid_regains)`
- `_player_event_candidates(player_id, player)` - Identifies player identifier variants
- `_identifier_variants(candidate)` - Normalizes player name variants
- `_event_matches_player(event, candidate_identifiers)` - Checks if event matches player
- `_get_recent_player_matches(player_id, player, limit)`
- `_match_team_context(match)` - Extracts home/away team info
- `_score_sequence(sequence)` - Ranks sequences by quality
- `_enrich_players_with_details(players)` - Calls player service
- `_enrich_matches_with_team_names(matches)` - Calls team service
- `_player_metrics(player, stats)` - Computes player-level metrics
- `_team_metrics(team, stats, matches, team_id)` - Computes team-level metrics
- `_team_form(matches, team_id)` - Last 5 match form
- `_team_goals(match, team_id)` - Extract team goals from match
- `_filter_matches(matches, competition)` - Filter by competition
- `_trend_label(match, period)` - Format trends by period
- `_compute_average_goals(matches)` - Calculate avg goals per match
- `_get_events_from_mongodb(match_id)` - Fetch match events from MongoDB
- `_get_json(url, params)` - HTTP client for service calls
- `_extract_list(payload, key)` - Extract array from response
- `_unwrap_data(payload)` - Unwrap API response
- `_to_int(value)` - Type conversion
- `_pass_accuracy(stats)` - Extract pass accuracy
- `_derive_age(birth_date)` - Calculate age from birthdate
- `_get_cached(cache_dict, key)` - Cache retrieval
- `_set_cache(cache_dict, key, value, ttl)` - Cache storage
- `_round_average(total, count)` - Helper for averages
- `_sort_matches(matches)` - Sort by date
- `_parse_date(date_str)` - Parse date strings

---

## 2. STATISTICS SERVICE

**Location**: `services/statistics-service/`

### 2.1 API Endpoints (`api/statistics.py`)

- `GET /api/v2/statistics/player/{player_id}` → `get_player_statistics(player_id, competition_id, season_id, per_90)`
- `GET /api/v2/statistics/team/{team_id}` → `get_team_statistics(team_id, competition_id, season_id)`
- `GET /api/v2/statistics/rankings/players` → `get_player_rankings(stat_name, position, competition_id, limit)`
- `GET /api/v2/statistics/rankings/teams` → `get_team_rankings(stat_name, competition_id, limit)`
- `POST /api/v2/statistics/compare/players` → `compare_players(player_ids, stat_categories)`
- `GET /api/v2/statistics/aggregate/player/{player_id}` → `aggregate_player_stats(player_id, start_date, end_date)`
- `GET /api/v2/statistics/match/{match_id}` → `get_match_statistics(match_id)`
- `GET /api/v2/statistics/match/{match_id}/advanced-metrics` → `get_match_advanced_metrics(match_id, time_bucket)`

### 2.2 Statistics Service (`services/statistics_service.py`)

#### Core Methods
- `get_player_statistics(player_id, competition_id, season_id, per_90)` - With caching
- `get_team_statistics(team_id, competition_id, season_id)` - With caching
- `get_player_rankings(stat_name, position, competition_id, limit)` - Rankings with cache
- `get_team_rankings(stat_name, competition_id, limit)` - Rankings with cache
- `compare_players(player_ids, stat_categories)` - Comparison with cache
- `aggregate_player_stats(player_id, start_date, end_date)` - Time-range aggregation
- `get_match_statistics(match_id)` - Match-level aggregation
- `get_match_advanced_metrics(match_id, time_bucket)` - Time-bucketed metrics
- `get_match_tactical_snapshot(match_id)` - From MatchProjectionBuilder
- `get_match_pass_network(match_id)` - From MatchProjectionBuilder
- `get_match_sequence_summary(match_id)` - From MatchProjectionBuilder
- `rebuild_match_projections(match_id, competition_id, season_id)` - Batch rebuild

### 2.3 Batch Aggregator (`services/batch_aggregator.py`)

**Purpose**: Event-based statistics aggregation, provider-agnostic

#### Public Entry Point
- `run(match_id, competition_id, season_id)` - Full aggregation pipeline

#### Player Statistics Aggregation
- `_aggregate_player_stats(events)` - Groups events by (player_id, match_id)
- `_empty_player_stat()` - Initializes empty stat record
- `_update_type_bucket(bucket, type_name, is_ok, event)` - Updates metrics based on event type
- `_upsert_player_stats(player_stats)` - Writes to MongoDB

**Player Statistics Calculated**:
```
- total_events
- passes / passes_successful
- crosses / crosses_successful
- shots / shots_on_target
- goals
- tackles / tackles_successful
- interceptions
- clearances
- aerials / aerials_won
- fouls_committed
- yellow_cards / red_cards
- ball_recoveries
- progressive_passes
- entered_final_third / entered_box
- total_xg
- high_regains
- minutes_played
```

#### Team Statistics Aggregation
- `_aggregate_team_stats(events)` - Groups events by (team_id, match_id)
- `_empty_team_stat()` - Initializes empty team stat record
- `_upsert_team_stats(team_stats)` - Writes to MongoDB

**Team Statistics Calculated**:
```
- total_events
- passes / passes_successful
- crosses / crosses_successful
- shots / shots_on_target
- goals
- tackles / tackles_successful
- interceptions
- clearances
- aerials / aerials_won
- fouls_committed
- yellow_cards / red_cards
- ball_recoveries
- possession_percentage
- progressive_passes
- pass_accuracy
```

#### Match Projections Aggregation
- `_aggregate_match_projections(match_id, events)` - Builds match-level views
- `_upsert_match_projections(match_id, projections)` - Writes all match-level collections

**Match Collections Generated**:
1. `match_statistics` - Box scores, timeline
2. `match_tactical_snapshot` - PPDA, possession zones, pressing
3. `match_pass_network` - Directed pass graph
4. `match_sequence_summary` - Possession sequences

#### Helper Methods
- `_find_match_doc(match_id)` - Flexible match ID lookup
- `_resolve_scoutpro_match_id(match_doc, events)` - ID normalization
- `_append_identifier_variants(string_values, numeric_values, value, prefix)` - ID variants

**Event Type Buckets Used**:
```
_PASS_TYPES = {"pass", "cross", "offside_pass", "corner_taken"}
_SHOT_TYPES = {"shot", "miss", "post", "attempt_saved", "goal", "blocked_shot"}
_TACKLE_TYPES = {"tackle"}
_INTERCEPTION_TYPES = {"interception"}
_CLEARANCE_TYPES = {"clearance"}
_DUEL_TYPES = {"duel", "aerial"}
_FOUL_TYPES = {"foul"}
_CARD_TYPES = {"card"}
_RECOVERY_TYPES = {"ball_recovery", "recovery"}
```

### 2.4 Match Projection Builder (`services/match_projection_builder.py`)

**Purpose**: Builds advanced match-level projections from event streams

#### Advanced Metrics (`build_advanced_metrics`)
- Time-bucketed event aggregation (default 5min buckets)
- Per-minute possession, pass completion, shot intensity
- Pressure metrics over time
- xG accumulation timeline

#### Tactical Snapshot (`build_tactical_snapshot`)
- **PPDA** (Passes Per Defensive Action) per team
- **Possession by zone**: defensive/middle/attacking thirds
- **Pressing intensity**: high/medium/low
- **Defensive events timeline**

#### Pass Network (`build_pass_network`)
- Directed graph: player nodes with pass edges
- Edge weights = number of completed passes
- Node size = pass share within team
- Per-team possession percentage

#### Sequence Summary (`build_sequence_summary`)
- Possession sequences with metadata
- Rapid regain index
- Top sequences by score
- Team sequence summaries

#### Sequence Building (`_build_sequences`)
- Identifies possession boundaries
- Tracks sequence actions, duration, territory
- Marks: direct attacks, box entries, final third entries
- Flags: sustained pressure, rapid regains
- End states: shot, goal, turnover

#### Helper Methods for Sequences
- `_is_actionable_sequence_event(event)` - Determines if event continues sequence
- `_territory_lane(location)` - Maps (x,y) to defensive/middle/attacking zone
- `_create_sequence(event, match_context)` - Initializes new sequence
- `_finalize_sequence(sequence)` - Completes sequence data
- `_build_rapid_regain_index(sequences)` - Indexes rapid regains
- `_score_sequence(sequence)` - Quality scoring for top sequences
- `_normalize_coordinate(value, axis)` - Standardizes pitch coordinates
- `_to_location(location)` - Parses location dict
- `_event_location(event)` - Extracts event coordinates
- `_get_qualifier_end_location(event)` - End position from qualifiers
- `_sequence_start_location(event)` - Sequence start position
- `_sequence_end_location(event)` - Sequence end position
- `_sequence_action_location(event)` - Action within sequence
- `_sequence_event_timestamp(event)` - Event timestamp

#### Timeline Rebucketing (`rebucket_timeline`)
- Converts 1-minute timeline to N-minute buckets
- Aggregates events across buckets
- Recomputes minute-level stats

#### Type Conversions
- `_to_float(value, default)` - Safe float conversion
- `_to_int(value, default)` - Safe int conversion
- `_optional_number(value)` - Optional numeric conversion
- `_event_type(event)` - Extract event type name
- `_match_team_context(match)` - Team info extraction
- `_round_average(total, count)` - Safe average calculation
- `_is_shot_like(event)` - Identifies shot-type events
- `_is_direct_play_event(event)` - Identifies direct play

### 2.5 Event Aggregator (`services/event_aggregator.py`)

**Purpose**: Event-type-specific aggregation using MongoDB pipelines

#### Pass Event Aggregation (`get_pass_statistics`)
- Total pass attempts
- Forward / backward / lateral breakdown
- Cross count
- Pass length average
- Per-90 metrics if requested

#### Aerial Duel Aggregation (`get_aerial_statistics`)
- Total duels
- Won / lost counts
- Win percentage
- Won in attacking half
- Won in defensive half

#### Further Event Types (Pattern shown)
- Shot events (shots on target, xG)
- Tackle events (successful tackles, tackle success %)
- Interception events
- Clearance events
- Foul events
- Card events (yellow/red)
- Ball recovery events
- Duel events

#### Cache Management
- Redis-backed caching (5-minute TTL)
- Per-player/team/competition/season keys

### 2.6 xG Model (`services/xg_model.py`)

#### Prediction Methods
- `predict(x, y, body_part, shot_type)` - Returns xG value (0.0-1.0)
- `is_ready()` - Check if model is trained

#### Feature Engineering (`_features`)
- Pitch position (x, y)
- Body part type (foot/head/other)
- Shot type (open play/penalty/free kick)

#### Training (`_train`)
- Trains on historical shot data from events
- Uses sklearn logistic regression

---

## 3. PLAYER SERVICE

**Location**: `services/player-service/`

### 3.1 API Endpoints

- `GET /api/v2/players/{player_id}` - Get single player
- `GET /api/v2/players` - List all players
- `GET /api/v2/players/search` - Search by name
- `GET /api/v2/players/{player_id}/statistics` - Get player stats

### 3.2 Player Service (`services/player_service.py`)

#### Core Methods
- `get_player(player_id)` - Single player with caching
- `list_players(filters, limit)` - List with filter support
- `search_players(query, limit)` - Full-text search
- `get_player_statistics(player_id, stat_type, per_90)` - Player stats
- `create_player(player)` - Create new player record
- `update_player(player_id, player)` - Update player record

#### Cache Keys
- `player:{player_id}` - Individual player (300s TTL)
- `players:list:v2:{filters}:{limit}` - Filtered lists
- `players:search:v2:{query}:{limit}` - Search results (150s TTL)
- `player:stats:{player_id}:{stat_type}:{per_90}` - Player stats (150s TTL)

#### Event Publishing
- Publishes `player.created` events to Kafka
- Publishes `player.updated` events to Kafka

#### Cache Invalidation
- `_invalidate_list_cache()` - Clears all list caches on create/update

---

## 4. TEAM SERVICE

**Location**: `services/team-service/`

### 4.1 API Endpoints

- `GET /api/v2/teams/{team_id}` - Get single team
- `GET /api/v2/teams` - List all teams
- `GET /api/v2/teams/search` - Search by name
- `GET /api/v2/teams/{team_id}/squad` - Get team squad

### 4.2 Team Service (`services/team_service.py`)

#### Core Methods
- `get_team(team_id)` - Single team with caching
- `list_teams(filters, limit)` - List with filters
- `search_teams(query, limit)` - Full-text search
- `get_squad(team_id)` - Team squad list with caching
- `create_team(team)` - Create new team
- `update_team(team_id, team)` - Update team

#### Cache Keys
- `team:{team_id}` - Individual team (600s TTL)
- `teams:list:{filters}:{limit}` - Filtered lists
- `teams:search:{query}:{limit}` - Search results (300s TTL)
- `team:squad:{team_id}` - Squad roster (300s TTL)

#### Event Publishing
- Publishes `team.created` events to Kafka
- Publishes `team.updated` events to Kafka

#### Cache Invalidation
- `_invalidate_list_cache()` - Clears all list caches

---

## 5. MATCH SERVICE

**Location**: `services/match-service/`

### 5.1 API Endpoints

- `GET /api/v2/matches/{match_id}` - Get single match
- `GET /api/v2/matches` - List all matches
- `GET /api/v2/matches/team/{team_id}` - Get team matches
- `GET /api/v2/matches/{match_id}/events` - Get match events
- `GET /api/v2/matches/date-range` - Filter by date range
- `GET /api/v2/matches/live` - Get live matches

### 5.2 Match Service (`services/match_service.py`)

#### Core Methods
- `get_match(match_id)` - Single match with intelligent caching
- `list_matches(filters, limit)` - List with filters
- `get_team_matches(team_id, limit)` - Team's recent matches
- `get_matches_by_date_range(start_date, end_date, limit)` - Date-filtered
- `get_live_matches()` - Currently live matches (no cache)
- `get_match_events(match_id)` - All events for a match
- `create_match(match)` - Create new match
- `update_match(match_id, match)` - Update match

#### Cache Keys
- `match:{match_id}` - Individual match (60s TTL, 30s for live)
- `matches:list:{filters}:{limit}` - Filtered lists
- `matches:team:{team_id}:{limit}` - Team matches
- `match:events:{match_id}` - Match events (30s TTL)

#### Smart Caching
- `_is_stale_cached_match(match_data)` - Invalidates stale live match snapshots
  - Checks: missing team IDs on live matches
  - Checks: missing team names on live matches

#### Event Publishing
- Publishes `match.created` events to Kafka
- Publishes `match.updated` events to Kafka

---

## 6. SHARED UTILITIES & ADAPTERS

**Location**: `services/shared/`

### 6.1 Parsers (`adapters/`)

#### Base Parser Interface (`adapters/base/base_parser.py`)

**Match Parsing**:
- `parse_match(raw_data)` - Single match from raw format
- `parse_matches(raw_data)` - Multiple matches

**Event Parsing**:
- `parse_events(raw_data)` - Event list from raw format
- `parse_event(raw_data)` - Single event

**Player Parsing**:
- `parse_player(raw_data)` - Single player (optional)
- `parse_players(raw_data)` - Player list (optional)

**Team Parsing**:
- `parse_team(raw_data)` - Single team (optional)
- `parse_teams(raw_data)` - Team list (optional)

**Lineup Parsing**:
- `parse_lineups(raw_data)` - Home/away lineup

#### Opta Parser (`adapters/opta/opta_parser.py`)

- `parse_events(raw_data: Dict)` - Routes to OptaEventFactory
- `_normalize_event(raw_event, match_id)` - Flattens XML attributes
- `_normalize_qualifiers(qualifiers)` - Extracts Opta qualifiers
  - Maps qualifier IDs to standardized format
  - Handles "@attributes" XML structure

#### StatsBomb Parser (`adapters/statsbomb/statsbomb_parser.py`)

- `parse_events(raw_events: List[Dict])` - Routes to StatsbombMapper
  - Each event mapped through mapper
  - Returns Pydantic models as dicts

### 6.2 Event Factories (`adapters/opta/taxonomies/`)

#### OptaEventFactory
- `create_event(normalized_event)` - Maps Opta F24 taxonomy
- Routes to domain entities via taxonomy

#### StatsbombMapper (`adapters/statsbomb/statsbomb_mapper.py`)
- `map_event(raw_event)` - Maps StatsBomb JSON to domain entities

### 6.3 Adapters Factory (`adapters/factory.py`)

**Provider Registration & Loading**:
- `get_mapper(provider)` - Returns provider-specific mapper
- `get_connector(provider)` - Returns data connector
- `get_parser(provider)` - Returns event parser
- `get_provider_priority(competition_id)` - Returns provider preference
- `get_supported_providers()` - List all providers
- `is_provider_supported(provider)` - Check availability
- `register_provider(provider, config)` - Register new provider

**Configuration & Caching**:
- `_load_config(config_path)` - Load provider configs
- `_load_class(module_path, class_name)` - Dynamic class loading
- `clear_cache()` - Clear loader cache

#### Factory Helper (`get_factory(config_path)`)
- Singleton factory instance

### 6.4 Data Merging (`merger/`)

#### Event Merger (`merger/event_merger.py`)
- Merges events from multiple providers for same match
- Resolves duplicates across providers

#### Match Merger (`merger/match_merger.py`)
- Consolidates match metadata from multiple sources
- Handles conflicting data

#### Player Merger (`merger/player_merger.py`)
- Merges player records across providers
- Maintains provider cross-references

#### Team Merger (`merger/team_merger.py`)
- Merges team records across providers

#### Conflict Detector (`merger/conflict_detector.py`)
- Identifies conflicting data across sources

#### Base Merger (`merger/base_merger.py`)
- Abstract interface for all merger types

#### Merge Strategies (`merger/strategies/`)
- Strategy pattern implementations for conflict resolution

### 6.5 Position Standardization (`utilities/position_mapper.py`)

#### Position Mapping
- `standardize(raw_position)` - Converts provider positions to standard format
- `_fuzzy_match(raw_position)` - Fuzzy matching for position names
- `get_all_mappings()` - Returns all position mappings

#### Position Classification
- `is_goalkeeper(raw_position)` - Boolean check
- `is_defender(raw_position)` - Boolean check
- `is_midfielder(raw_position)` - Boolean check
- `is_forward(raw_position)` - Boolean check

#### Helper Function
- `standardize_position(raw_position)` - Module-level standardization

### 6.6 Data Quality (`quality/`)

#### Quality Enricher (`quality/quality_enricher.py`)
- Validates event data
- Enriches with quality flags
- Handles missing/invalid data

### 6.7 Domain Models (`domain/`)

#### Base Entity Models
- `BaseEventInfo` - Common event attributes
- `BasePlayerInfo` - Common player attributes
- `BaseTeamInfo` - Common team attributes
- `BaseMatchInfo` - Common match attributes

#### Pydantic Models (`models/base.py`)
- `Player` - Player data model
- `Team` - Team data model
- `Match` - Match data model
- `PlayerStatistics` - Statistics model
- `TeamStatistics` - Team stats model
- `APIResponse` - Standard response wrapper

---

## 7. BATCH OPERATIONS & DATA SYNC

### 7.1 Batch Processing Scripts

**Located in**: `scripts/`

#### Ingestion & Aggregation
- `batch_01_ingestion.sh` - Ingest raw provider data
- `batch_02_train_models.sh` - Train ML models (xG, etc.)
- `batch_03_medallion_pipeline.sh` - Medallion architecture processing

#### Kafka Management
- `create-kafka-topics.sh` - Initialize Kafka topics

#### Data Synchronization
- `migrate_scoutpro_ids.py` - Normalize ScoutPro IDs
- `re_import_f40_positions.py` - Re-import position data

#### Testing
- `gateway_smoke.py` - API gateway smoke tests

### 7.2 Data Sync Service

**Location**: `services/data-sync-service/`

#### Projected Read Models
- `read_model_projector.py` - Projects events into:
  - `match_events` collection (normalized by shared parsers)
  - Provider-agnostic schema

#### Batch Sync Integration
- Triggers `BatchAggregator.run()` after sync completes
- Populates statistics collections

---

## 8. MISSING FUNCTIONS CHECKLIST

### 8.1 Player Statistics (Currently Missing)
- [ ] Fouls per match
- [ ] Distance covered per match
- [ ] Top speed per match
- [ ] Possession percentage
- [ ] Progressive pass percentage
- [ ] Key passes
- [ ] Chance conversion rate
- [ ] Shot accuracy
- [ ] Dribbles completed
- [ ] Dribble success rate
- [ ] Tackles success rate
- [ ] Interception rate
- [ ] Aerial duel win rate
- [ ] Pressures applied
- [ ] Pressure success rate
- [ ] Blocks
- [ ] Ball recovery percentage

### 8.2 Team Statistics (Currently Missing)
- [ ] Expected goals (xG) for/against
- [ ] Shot accuracy %
- [ ] Possession average
- [ ] Pass completion %
- [ ] Progressive passes per match
- [ ] Tackles per match
- [ ] Pressing intensity (quantified)
- [ ] Set piece effectiveness
- [ ] Counter-attack success rate
- [ ] Build-up play success rate
- [ ] Defensive line depth
- [ ] Average pass length
- [ ] Through balls
- [ ] Press resistance
- [ ] Recovery time
- [ ] Territory control timeline
- [ ] High turnovers

### 8.3 Match Statistics (Currently Missing)
- [ ] Expected goals (xG) timeline
- [ ] Shot map with xG values
- [ ] Progressive pass heatmaps
- [ ] Pressing heatmaps
- [ ] Defensive action heatmaps
- [ ] Ball progression by thirds
- [ ] Set pieces breakdown
- [ ] Counter-attacks breakdown
- [ ] Long ball percentage
- [ ] Ground duel distribution
- [ ] Aerial duel distribution
- [ ] Fouls by zone
- [ ] Offside traps
- [ ] Offside counts

### 8.4 Predictive/ML Functions (Missing)
- [ ] Player form trajectory
- [ ] Injury risk prediction
- [ ] Transfer likelihood
- [ ] Performance ceiling estimate
- [ ] Optimal position recommendation
- [ ] Style/role classification
- [ ] Team chemistry metrics
- [ ] Fatigue index
- [ ] Match outcome probability
- [ ] Goal probability by minute

### 8.5 Comparison/Analysis Functions (Missing)
- [ ] Player similarity matching
- [ ] Team style clustering
- [ ] Peer group generation (player comparisons)
- [ ] Performance vs expected
- [ ] Historical trending
- [ ] Positional comparisons
- [ ] Cross-league comparisons

---

## 9. RECALCULATION STRATEGY FOR MISSING FUNCTIONS

### Phase 1: Core Statistics from Events
```
For each match_id in database:
  1. Load all normalized events from match_events collection
  2. Run BatchAggregator._aggregate_player_stats(events)
     → Populates: passes, shots, tackles, aerials, fouls, cards, etc.
  3. Run BatchAggregator._aggregate_team_stats(events)
     → Populates: team-level aggregates
  4. Run BatchAggregator._aggregate_match_projections(match_id, events)
     → Generates: match_statistics, tactical_snapshot, pass_network, sequences
  5. Run MatchProjectionBuilder methods for advanced metrics
```

### Phase 2: Event-Type-Specific Statistics
```
For each event type (pass, aerial, shot, duel, etc.):
  1. Use EventAggregator.get_*_statistics()
  2. Apply MongoDB aggregation pipelines
  3. Store in event_statistics collection
```

### Phase 3: Advanced Metrics from Sequences
```
From possession sequences (built by MatchProjectionBuilder):
  1. Calculate average sequence length
  2. Count ball progressions
  3. Analyze sequence endings (goal/shot/turnover)
  4. Build sequence-based player ratings
  5. Territory progression metrics
```

### Phase 4: ML-Based Predictions
```
For xG predictions:
  1. Use XGModel.predict(x, y, body_part, shot_type)
  2. Aggregate per-player xG per match
  3. Calculate cumulative xG per season

For other predictions (TBD):
  1. Implement missing prediction models
  2. Train on historical event data
  3. Generate predictions per player/team/match
```

### Phase 5: Derived Analytics
```
For statistics currently missing:
  1. Calculate per-90 versions of all stats
  2. Generate percentiles by position/competition
  3. Build peer groups for player comparisons
  4. Create form curves (rolling averages)
  5. Generate trend charts
```

---

## 10. DATA FLOW DIAGRAM

```
Raw Provider Data (Opta F24, StatsBomb JSON)
    ↓
Parser (OptaParser / StatsbombParser)
    ↓
Normalized Events (match_events collection)
    ↓
BatchAggregator.run()
    ├→ _aggregate_player_stats() → player_statistics collection
    ├→ _aggregate_team_stats() → team_statistics collection
    └→ _aggregate_match_projections()
        ├→ match_statistics
        ├→ match_tactical_snapshot
        ├→ match_pass_network
        └→ match_sequence_summary
    ↓
EventAggregator (type-specific aggregations)
    ├→ get_pass_statistics()
    ├→ get_aerial_statistics()
    ├→ get_shot_statistics()
    └→ ... (other event types)
    ↓
MatchProjectionBuilder (advanced metrics)
    ├→ build_advanced_metrics() (time-bucketed)
    ├→ build_tactical_snapshot() (PPDA, zones)
    ├→ build_pass_network() (directed graph)
    └→ build_sequence_summary() (possession chains)
    ↓
Analytics Service (consumer)
    ├→ get_player_dashboard()
    ├→ get_team_dashboard()
    ├→ get_player_sequence_insights()
    ├→ compare_players()
    └→ compare_teams()
    ↓
API Response to Frontend
```

---

## 11. INTEGRATION NOTES

### Service Dependencies
- **Analytics Service** depends on:
  - Statistics Service (rankings, dashboards)
  - Player Service (enrichment)
  - Team Service (enrichment)
  - Match Service (match data)
  - MongoDB (event data)

- **Statistics Service** depends on:
  - Player Service (player details)
  - Team Service (team details)
  - Match Service (match details)
  - MongoDB (events, statistics)
  - Redis (caching)
  - Kafka (event publishing)

- **Batch Aggregator** depends on:
  - MongoDB (match_events collection)
  - MatchProjectionBuilder (advanced metrics)

### Cache TTLs
- Live match data: 30 seconds
- Recent match data: 60 seconds
- Player data: 300 seconds (5 minutes)
- Team data: 600 seconds (10 minutes)
- Rankings: 360 seconds (6 minutes)
- Event aggregations: 300 seconds (5 minutes)

### Event Type Categorization
```
_PASS_TYPES = {"pass", "cross", "offside_pass", "corner_taken"}
_SHOT_TYPES = {"shot", "miss", "post", "attempt_saved", "goal", "blocked_shot"}
_TACKLE_TYPES = {"tackle"}
_INTERCEPTION_TYPES = {"interception"}
_CLEARANCE_TYPES = {"clearance"}
_DUEL_TYPES = {"duel", "aerial"}
_FOUL_TYPES = {"foul"}
_CARD_TYPES = {"card"}
_RECOVERY_TYPES = {"ball_recovery", "recovery"}
```

---

## 12. TESTING & VALIDATION

### Unit Tests Needed For
- Each event type aggregation
- Sequence building logic
- Pass network construction
- Tactical snapshot calculations
- Position standardization
- ID normalization across providers

### Integration Tests Needed For
- Full batch aggregation pipeline
- Cross-provider event merging
- Statistics service rankings
- Analytics dashboard loading
- Cache invalidation patterns

---

**Document Status**: Complete inventory as of May 6, 2026  
**Last Updated**: May 6, 2026
