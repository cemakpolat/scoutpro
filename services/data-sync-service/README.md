# Data Sync Service

Multi-provider data synchronization service for ScoutPro.

## Overview

The Data Sync Service orchestrates synchronization of football data from multiple providers (Opta, StatsBomb, Wyscout, etc.) into a unified canonical format.

### Features

- **Multi-provider support**: Sync data from Opta, StatsBomb, Wyscout, and more
- **Entity resolution**: Automatically match players, teams, and matches across providers
- **Conflict detection**: Log and resolve conflicts between provider data
- **Quality enrichment**: Add completeness scores and quality metadata
- **Scheduled syncs**: Run sync jobs periodically (realtime, hourly, daily, weekly)
- **Bulk operations**: Optimized for high-volume data (events)

## Architecture

```
Data Sync Service
├── sync/
│   ├── base_syncer.py       # Abstract sync workflow
│   ├── player_syncer.py     # Player synchronization
│   ├── team_syncer.py       # Team synchronization
│   ├── match_syncer.py      # Match synchronization
│   ├── event_syncer.py      # Event synchronization (high volume)
│   └── sync_scheduler.py    # Job scheduling and orchestration
└── main.py                  # Service entry point
```

### Sync Workflow

For each entity type (Player, Team, Match, Event):

1. **Fetch** - Retrieve data from provider API
2. **Map** - Transform to canonical format using provider mapper
3. **Resolve** - Match entities with existing canonical data
4. **Merge** - Combine data from multiple providers using merge strategies
5. **Enrich** - Add quality metadata and completeness scores
6. **Store** - Save to canonical repository (MongoDB)

## Usage

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all sync jobs once
python main.py --once

# Run specific provider
python main.py --once --provider opta --competition 8

# Run in daemon mode (continuous)
python main.py --daemon
```

### Run Specific Job

```bash
# Sync teams from Opta
python main.py --job opta_teams --competition 8 --season 2023

# Sync players from StatsBomb
python main.py --job statsbomb_players --competition 55

# Sync match events
python main.py --job opta_events --match g2187923
```

### Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--once` | Run all jobs once and exit | `python main.py --once` |
| `--daemon` | Run in daemon mode (continuous) | `python main.py --daemon` |
| `--job` | Run specific job | `--job opta_teams` |
| `--provider` | Provider name | `--provider opta` |
| `--competition` | Competition ID | `--competition 8` |
| `--season` | Season ID | `--season 2023` |
| `--match` | Match ID (for events) | `--match g2187923` |

## Configuration

### Provider Configuration

Edit `shared/config/providers.yaml` to configure provider priorities and settings:

```yaml
provider_priority:
  global:
    - opta
    - statsbomb
    - wyscout

providers:
  opta:
    db_name: statsfabrik
    db_host: localhost
    db_port: 27017
    competition_id: "8"
    season_id: "2023"
```

### Merge Rules

Edit `shared/config/merge_rules.yaml` to configure field-level merge strategies:

```yaml
merge_rules:
  player:
    name:
      strategy: prefer_primary
      primary_provider: opta
    birth_date:
      strategy: prefer_non_null
      log_if_mismatch: true
```

## Programmatic Usage

```python
from sync import PlayerSyncer, SyncScheduler, SyncFrequency

# Sync players once
syncer = PlayerSyncer(
    provider='opta',
    config={'competition_id': '8', 'season_id': '2023'}
)
result = await syncer.sync()
print(f"Synced {result.entities_created} players")

# Schedule periodic syncs
scheduler = SyncScheduler()

scheduler.add_job(
    name='opta_teams',
    syncer_class=TeamSyncer,
    provider='opta',
    config={'competition_id': '8'},
    frequency=SyncFrequency.DAILY
)

await scheduler.start()
```

## Sync Frequencies

- **REALTIME** - Every minute (for live match events)
- **FREQUENT** - Every 15 minutes
- **HOURLY** - Every hour
- **DAILY** - Once per day (2:00 AM)
- **WEEKLY** - Once per week (Monday 2:00 AM)
- **MANUAL** - Only on demand

## Monitoring

### Get Scheduler Status

```python
status = scheduler.get_status()

print(f"Total jobs: {status['total_jobs']}")
print(f"Enabled: {status['enabled_jobs']}")

for job in status['jobs']:
    print(f"{job['name']}: {job['run_count']} runs")
    if job['last_result']:
        print(f"  Last: {job['last_result']['status']}")
```

### Sync Results

Each sync operation returns a `SyncResult` with statistics:

```python
result = await syncer.sync()

print(f"Status: {result.status}")
print(f"Fetched: {result.entities_fetched}")
print(f"Created: {result.entities_created}")
print(f"Updated: {result.entities_updated}")
print(f"Merged: {result.entities_merged}")
print(f"Conflicts: {result.conflicts_detected}")
print(f"Duration: {result.duration_seconds}s")
```

## Entity Resolution

Entity resolution matches entities across providers using:

- **PlayerResolver**: Name similarity, birth date, position
- **TeamResolver**: Name normalization ('Liverpool' vs 'Liverpool FC')
- **MatchResolver**: Team IDs + date + score

Confidence thresholds and similarity algorithms are configurable in the resolver classes.

## Conflict Detection

Conflicts are logged to MongoDB (`data_conflicts` collection) for analysis:

```python
from shared.merger import ConflictDetector

detector = ConflictDetector()
stats = detector.get_conflict_stats(
    entity_type='player',
    field_name='birth_date'
)

print(f"Total conflicts: {stats['total_conflicts']}")
print(f"By severity: {stats['by_severity']}")
```

## Performance Optimization

### Event Sync

Events are high-volume data. Optimizations:

- Bulk upsert operations
- Replace strategy (delete old events, insert new)
- No individual entity resolution (too many events)
- Indexed queries by match_id

### Repository Indexes

All repositories have optimized indexes:

- Provider ID lookups
- Common filter fields (position, nationality, competition)
- Compound indexes for frequent queries

## Troubleshooting

### Common Issues

**1. MongoDB Connection Failed**
```bash
# Check MongoDB is running
docker-compose ps mongo

# Check connection settings in config
mongo_uri: mongodb://localhost:27017
```

**2. Import Errors**
```bash
# Ensure parent directories are in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/scoutpro"
```

**3. Provider API Errors**
```bash
# Check provider configuration
# Verify API credentials and endpoints
# Check provider connector logs
```

## Development

### Adding a New Provider

1. **Implement adapters** in `shared/adapters/<provider>/`:
   - `<provider>_mapper.py` - Data transformation
   - `<provider>_connector.py` - API client
   - `<provider>_taxonomy.py` - Event type mapping

2. **Register in factory** (`shared/adapters/factory.py`)

3. **Add sync jobs** to scheduler

See `docs/ADDING_NEW_PROVIDER.md` for detailed guide.

### Running Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests (requires MongoDB)
pytest tests/integration/

# Specific test
pytest tests/unit/test_player_syncer.py
```

## Docker Deployment

```bash
# Build image
docker build -t scoutpro-data-sync .

# Run service
docker run -d \
  --name data-sync \
  -e MONGO_URI=mongodb://mongo:27017 \
  -e PROVIDER=opta \
  scoutpro-data-sync

# Run with docker-compose
docker-compose up data-sync-service
```

## License

Part of the ScoutPro project.
