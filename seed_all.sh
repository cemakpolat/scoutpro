#!/usr/bin/env bash
# ----------------------------------------------------------------
# seed_all.sh  —  ScoutPro first-setup data loader
#
# Runs inside the data-seeder container.  Sequence:
#   1. Wait for MongoDB, TimescaleDB, Redis, Kafka, data-provider
#   2. python main.py --once  (data-sync-service: all providers/feeds)
#   3. python /scripts/enrich_f40.py
#   4. python /scripts/enrich_matches_and_events.py
# ----------------------------------------------------------------
set -euo pipefail

# ── Helpers ──────────────────────────────────────────────────────

wait_for_tcp() {
  local label="$1" host="$2" port="$3" timeout="${4:-60}"
  echo "[seed] Waiting for $label ($host:$port) ..."
  local elapsed=0
  until nc -z "$host" "$port" 2>/dev/null; do
    if [[ $elapsed -ge $timeout ]]; then
      echo "[seed] ERROR: $label did not become available within ${timeout}s"
      exit 1
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  echo "[seed] $label is reachable."
}

wait_for_http() {
  local label="$1" url="$2" timeout="${3:-60}"
  echo "[seed] Waiting for $label ($url) ..."
  local elapsed=0
  until curl -sf "$url" > /dev/null 2>&1; do
    if [[ $elapsed -ge $timeout ]]; then
      echo "[seed] ERROR: $label did not respond within ${timeout}s"
      exit 1
    fi
    sleep 3
    elapsed=$((elapsed + 3))
  done
  echo "[seed] $label is healthy."
}

wait_for_mongo() {
  local timeout="${1:-90}"
  echo "[seed] Waiting for MongoDB ..."
  local elapsed=0
  until python - <<'PYEOF' 2>/dev/null
import os, sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
try:
    url = os.environ.get(
        "MONGODB_URL",
        "mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin"
    )
    c = MongoClient(url, serverSelectionTimeoutMS=2000)
    c.admin.command("ping")
    sys.exit(0)
except Exception:
    sys.exit(1)
PYEOF
  do
    if [[ $elapsed -ge $timeout ]]; then
      echo "[seed] ERROR: MongoDB did not become available within ${timeout}s"
      exit 1
    fi
    sleep 3
    elapsed=$((elapsed + 3))
  done
  echo "[seed] MongoDB is ready."
}

# ── Infrastructure readiness ──────────────────────────────────────

MONGO_HOST="${MONGODB_HOST:-mongo}"
MONGO_PORT="${MONGODB_PORT:-27017}"
TIMESCALE_HOST="${TIMESCALEDB_HOST:-timescaledb}"
TIMESCALE_PORT="${TIMESCALEDB_PORT:-5432}"
REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"
KAFKA_HOST=$(echo "${KAFKA_BOOTSTRAP_SERVERS:-kafka:9092}" | cut -d: -f1)
KAFKA_PORT=$(echo "${KAFKA_BOOTSTRAP_SERVERS:-kafka:9092}" | cut -d: -f2)
DATA_PROVIDER_URL="${OPTA_BASE_URL:-http://data-provider:7000}"

wait_for_tcp  "MongoDB"      "$MONGO_HOST"     "$MONGO_PORT"     90
wait_for_tcp  "TimescaleDB"  "$TIMESCALE_HOST" "$TIMESCALE_PORT" 90
wait_for_tcp  "Redis"        "$REDIS_HOST"     "$REDIS_PORT"     60
wait_for_tcp  "Kafka"        "$KAFKA_HOST"     "$KAFKA_PORT"     120
wait_for_http "data-provider" "${DATA_PROVIDER_URL}/api/health"  90
wait_for_mongo 90

# Extra buffer so Kafka topics and consumers are fully initialised
echo "[seed] Infrastructure ready. Giving Kafka 5 s to stabilise ..."
sleep 5

# ── Phase 1: full data sync (all feeds, all providers) ───────────

echo ""
echo "======================================================================"
echo "[seed] Phase 1/3 — running data-sync-service --once"
echo "       (Opta F1/F9/F24/F40 + StatsBomb → Kafka → MongoDB)"
echo "======================================================================"

cd /app
python main.py --once
SYNC_EXIT=$?

if [[ $SYNC_EXIT -ne 0 ]]; then
  echo "[seed] ERROR: data sync failed (exit $SYNC_EXIT)"
  exit $SYNC_EXIT
fi

echo "[seed] Phase 1 complete."

# ── Phase 2: F40 biometric seeding (via OptaBatchSeeder) ─────────
#
# enrich_f40.py was removed.  The OptaBatchSeeder (sync/batch_seeder.py)
# handles F40 parsing and player upsert inline using the shared
# parser/mapper stack, so all ScoutPro IDs are assigned correctly.
# If the main sync already ran F40, this is a no-op (upsert is idempotent).

echo ""
echo "======================================================================"
echo "[seed] Phase 2/3 — F40 player profiles (OptaBatchSeeder)"
echo "======================================================================"

python - <<'PYEOF'
import sys, os
sys.path.insert(0, '/app')
try:
    from sync.batch_seeder import OptaBatchSeeder
    seeder = OptaBatchSeeder(
        data_root=os.environ.get('DATA_ROOT', '/app/data/opta/2019'),
        competition_id=int(os.environ.get('COMPETITION_ID', 115)),
        season_id=int(os.environ.get('SEASON_ID', 2019)),
    )
    seeder.seed_f40()
    seeder.close()
    print('[seed] F40 seeding complete')
except Exception as e:
    print(f'[seed] WARNING: F40 seeding failed: {e} (non-fatal)')
PYEOF

# ── Phase 3: aggregate player/team statistics from events ────────
#
# enrich_matches_and_events.py was removed.  The BatchAggregator
# (statistics-service/services/batch_aggregator.py) computes
# player_statistics and team_statistics from match_events directly.

echo ""
echo "======================================================================"
echo "[seed] Phase 3/3 — aggregating player/team statistics (BatchAggregator)"
echo "======================================================================"

python - <<'PYEOF'
import sys
sys.path.insert(0, '/app')
try:
    # The BatchAggregator lives in the statistics-service but we can import
    # it directly here since it only depends on pymongo.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'batch_aggregator',
        '/statistics-service/services/batch_aggregator.py'
    )
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        agg = mod.BatchAggregator()
        result = agg.run()
        agg.close()
        print(f'[seed] Aggregation complete: {result}')
    else:
        print('[seed] batch_aggregator not found in container — skipping aggregation step')
except Exception as e:
    print(f'[seed] WARNING: aggregation failed: {e} (non-fatal)')
PYEOF

# ── Done ──────────────────────────────────────────────────────────

echo ""
echo "======================================================================"
echo "[seed] All phases complete. Database is seeded and ready."
echo ""
echo "  Verify counts from the host:"
echo "    docker exec scoutpro-mongo mongosh -u root -p scoutpro123 \\"
echo "      --authenticationDatabase admin --quiet \\"
echo "      --eval \"db=db.getSiblingDB('scoutpro'); \\"
echo "             ['players','teams','matches','match_events'].forEach(c => \\"
echo "               print(c+': '+db.getCollection(c).countDocuments({})))\""
echo ""
echo "  Or use the management script:"
echo "    ./manage.sh status"
echo "======================================================================"
