# Data Provider Mock — Developer Reference

The `data-provider-mock` provider server is a lightweight FastAPI web server that **replicates the HTTP API of Opta and StatsBomb** using local files from `data/`.  
Use it so every part of the ScoutPro backend works in fully offline mode — no API keys needed.

---

## Why it exists

ScoutPro's microservices (player-service, live-ingestion-service, data-sync-service …) call external data providers at runtime.  
In development you rarely want to burn real API quota or depend on network access.  
The mock solves this by:

1. Serving the same URL paths and response formats as the real providers.
2. Reading files you already have in `data/opta/` and `data/statsbomb/`.
3. Letting you swap the provider URL with a single environment variable.

---

## Quick start (local Python)

```bash
cd providers/data-provider-mock
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 7000 --reload
```

Open **http://localhost:17000/docs** for the interactive Swagger UI.

---

## Quick start (Docker)

```bash
# Start only infrastructure + mock provider
docker-compose -f docker-compose.data.yml up -d data-provider-mock

# Or start the full data stack (Mongo, Redis, Kafka, MinIO + mock)
docker-compose -f docker-compose.data.yml up -d
```

---

## Connecting services to the mock

Override these environment variables when starting a service:

| Variable | Value for mock |
|----------|----------------|
| `OPTA_BASE_URL` | `http://localhost:17000` |
| `STATSBOMB_BASE_URL` | `http://localhost:17000` |

Inside Docker Compose use the service name instead of `localhost`:

```yaml
environment:
  - OPTA_BASE_URL=http://data-provider-mock:7000
  - STATSBOMB_BASE_URL=http://data-provider-mock:7000
```

---

## API Reference

### Health & Discovery

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Returns `{"status":"ok"}` |
| GET | `/api/feeds` | Catalogue of all data on disk (competitions, matches, file counts) |

### Opta Feeds

Opta responses preserve the source format. JSON fixtures stay JSON and XML feeds stay XML.

| Method | Path | Feed | Description |
|--------|------|------|-------------|
| GET | `/api/football/f1/{competition_id}/{season_id}` | F1 | Season schedule and results |
| GET | `/api/football/f9/{competition_id}/{season_id}` | F9 | Match summary, lineups, and stats |
| GET | `/api/football/f40/{competition_id}/{season_id}` | F40 | Squad lists and player profiles |
| GET | `/api/football/f24/{competition_id}/{season_id}/{match_id}` | F24 | Match events (passes, shots…) |
| GET | `/api/football/matches/{competition_id}/{season_id}` | — | JSON list of all available match IDs |

**Example requests** (Turkish Super Lig 2019/2020, competition_id=115, season_id=2019):

```bash
# Match summary
curl http://localhost:17000/api/football/f9/115/2019

# Squad list
curl http://localhost:17000/api/football/f40/115/2019

# Events for match 1080974
curl http://localhost:17000/api/football/f24/115/2019/1080974

# Discover available match IDs
curl http://localhost:17000/api/football/matches/115/2019
```

### StatsBomb Feeds

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/statsbomb/matches` | List all available StatsBomb match files |
| GET | `/api/statsbomb/events/{match_id}` | All events for a match as JSON |
| GET | `/api/statsbomb/events/{match_id}/csv` | Raw StatsBomb CSV download |

**Example requests**:

```bash
# List available matches
curl http://localhost:17000/api/statsbomb/matches

# Events for Samsunspor vs Beşiktaş (match 3946949)
curl http://localhost:17000/api/statsbomb/events/3946949

# Raw CSV
curl http://localhost:17000/api/statsbomb/events/3946949/csv -o match.csv
```

---

## Available data

| Source | Competition | Season | Content |
|--------|-------------|--------|---------|
| Opta F1 | Turkish Süper Lig (115) | 2019 | Fixtures and results |
| Opta F9 | Turkish Süper Lig (115) | 2019 | Match summary |
| Opta F24 | Turkish Süper Lig (115) | 2019 | ~300 match event files |
| Opta F40 | Turkish Süper Lig (115) | 2019 | Squad lists |
| Opta F24 | Turkish Süper Lig (115) | 2017 | 1 match (935592) |
| StatsBomb | Samsunspor vs Beşiktaş | 2019 | Single match events CSV |

---

## File layout

```
providers/data-provider-mock/
├── main.py                   # FastAPI app factory & middleware
├── config.py                 # DATA_ROOT resolution, defaults
├── requirements.txt
├── Dockerfile
├── api/
│   ├── __init__.py
│   ├── opta.py               # Opta feed endpoints
│   ├── statsbomb.py          # StatsBomb feed endpoints
│   └── admin.py              # /health, /feeds discovery
└── loaders/
    ├── __init__.py
    ├── opta_loader.py         # File resolution & in-memory cache
    └── statsbomb_loader.py    # CSV parsing & in-memory cache
```

---

## Extending with new data

1. **Add Opta files** — drop any file named `f{N}_{competition_id}_{season_id}[_{match_id}]` into `data/opta/` or `data/opta/{season_id}/`. The service discovers them automatically.

2. **Add StatsBomb files** — drop any `*.csv` into `data/statsbomb/`. Name format: `{HomeTeam}_{AwayTeam}_{match_id}.csv`. The match_id is extracted from the last underscore segment.

3. **Add a new feed type (e.g. F7, F30)** — add a new route in `api/opta.py` following the same pattern as `get_f1` / `get_f9`.

---

## Architecture decision record

### Why FastAPI?

All Python services and provider servers in ScoutPro use FastAPI. Using the same stack means the mock can be added to `docker-compose.data.yml` without introducing new technology, and the interactive `/docs` UI comes for free.

### Why serve raw XML instead of parsing to JSON?

The downstream services already contain Opta XML parsers (see `services/shared/adapters/opta/`). Serving raw XML means we do not need to duplicate or reverse-engineer that parsing logic in the mock. Services that already work with the real Opta API work unchanged.

### Why `lru_cache`?

Opta F24 files can be several MB each. Caching after the first load prevents repeated disk I/O during development sessions where the same match is requested many times (e.g. by the frontend's live-event polling).
