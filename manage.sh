#!/usr/bin/env bash
# =============================================================================
#  ScoutPro — Unified System Management Script
# =============================================================================
#
#  Commands:
#    ./manage.sh build      Build all Docker images from scratch (no cache)
#    ./manage.sh start      Start the full stack (infra + all services)
#    ./manage.sh stop       Gracefully stop all containers (data preserved)
#    ./manage.sh clean      Stop + remove all volumes (full wipe)
#    ./manage.sh seed       Trigger the full data pipeline via API
#    ./manage.sh status     Show container health + MongoDB data counts
#    ./manage.sh validate   Run end-to-end integration checks
#    ./manage.sh logs [svc] Tail logs (all services or one named service)
#    ./manage.sh restart    stop + start
#
#  Pipeline flow (seed):
#    data-provider-mock (./data/) ─→ data-sync-service ─→ Kafka ─→ MongoDB
#    └─ serves F1/F9/F24/F40 as a   └─ fetches, parses,           └─ consumed
#       real Opta HTTP API             assigns ScoutPro IDs,           by all
#                                      publishes events                services
#
# =============================================================================
set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
C_BLUE='\033[0;34m'
C_GREEN='\033[0;32m'
C_YELLOW='\033[1;33m'
C_RED='\033[0;31m'
C_BOLD='\033[1m'
C_OFF='\033[0m'

# ── Config ────────────────────────────────────────────────────────────────────
COMPOSE_FILE="docker-compose.yml"
DATA_SYNC_URL="${DATA_SYNC_URL:-http://localhost:28015}"
MONGO_URL="${MONGO_URL:-mongodb://root:scoutpro123@localhost:27017/scoutpro?authSource=admin}"
COMPETITION_ID="${COMPETITION_ID:-115}"
SEASON_ID="${SEASON_ID:-2019}"

# Minimal startup footprint for day-to-day development.
MINIMAL_SERVICES=(
  mongo
  redis
  data-provider
  data-sync-service
  api-gateway
  nginx
)

_banner() {
  echo -e "${C_BLUE}${C_BOLD}"
  echo "╔═══════════════════════════════════════════════════════════╗"
  echo "║               ScoutPro System Management                 ║"
  echo "╚═══════════════════════════════════════════════════════════╝"
  echo -e "${C_OFF}"
}

_log()  { echo -e "${C_BLUE}[manage]${C_OFF} $*"; }
_ok()   { echo -e "${C_GREEN}[  OK  ]${C_OFF} $*"; }
_warn() { echo -e "${C_YELLOW}[ WARN ]${C_OFF} $*"; }
_err()  { echo -e "${C_RED}[ ERR  ]${C_OFF} $*"; }

_require_docker() {
  if ! docker info > /dev/null 2>&1; then
    _err "Docker is not running. Start Docker Desktop and retry."
    exit 1
  fi
}

# ── wait helpers ──────────────────────────────────────────────────────────────

_wait_http() {
  local label="$1" url="$2" max="${3:-90}"
  _log "Waiting for $label at $url ..."
  local elapsed=0
  until curl -sf --max-time 3 "$url" > /dev/null 2>&1; do
    if [[ $elapsed -ge $max ]]; then
      _err "$label did not respond within ${max}s"
      return 1
    fi
    sleep 3; elapsed=$((elapsed+3))
    printf "."
  done
  echo ""
  _ok "$label is up"
}

_wait_data_sync() {
  _wait_http "data-sync-service" "${DATA_SYNC_URL}/health" 120
}

# =============================================================================
# COMMAND: build
# Rebuild all Docker images from scratch (--no-cache --pull).
# Accepts an optional service name: ./manage.sh build [service]
# =============================================================================
cmd_build() {
  _banner
  _require_docker
  local svc="${1:-}"

  if [[ -n "$svc" ]]; then
    _log "Building image for service '${svc}' from scratch ..."
    docker-compose -f "$COMPOSE_FILE" build --no-cache --pull "$svc"
    _ok "Build complete: ${svc}"
  else
    _log "Building all images from scratch (this may take a while) ..."
    docker-compose -f "$COMPOSE_FILE" build --no-cache --pull
    _ok "All images built successfully."
  fi

  echo ""
  _log "Run '${C_BOLD}./manage.sh start${C_OFF}' to launch the rebuilt stack."
}

# =============================================================================
# COMMAND: start
# =============================================================================
cmd_start() {
  _banner
  _require_docker

  local mode="minimal"
  case "${1:-}" in
    --full|full|all)
      mode="full"
      ;;
    --minimal|minimal|"")
      mode="minimal"
      ;;
    *)
      _err "Unknown start option: ${1}"
      echo "Usage: ./manage.sh start [--minimal|--full]"
      exit 1
      ;;
  esac

  if [[ "$mode" == "full" ]]; then
    _log "Starting FULL ScoutPro stack ..."
  else
    _log "Starting MINIMAL ScoutPro stack (essential services only) ..."
  fi
  echo ""

  if [[ "$mode" == "full" ]]; then
    docker-compose -f "$COMPOSE_FILE" up -d
  else
    docker-compose -f "$COMPOSE_FILE" up -d "${MINIMAL_SERVICES[@]}"
  fi

  echo ""
  if [[ "$mode" == "full" ]]; then
    _ok "Full stack launched."
  else
    _ok "Minimal stack launched."
    _log "Started services: ${MINIMAL_SERVICES[*]}"
  fi
  echo ""
  _log "Key service URLs:"
  echo "  Frontend            http://localhost:80"
  echo "  API Gateway         http://localhost:3001"
  echo "  Data Provider Mock  http://localhost:17000/api/feeds"
  echo "  Data Sync Service   ${DATA_SYNC_URL}/health"
  echo "  Grafana             http://localhost:3000"
  echo ""
  _log "Run '${C_BOLD}./manage.sh status${C_OFF}' to verify health."
  _log "Run '${C_BOLD}./manage.sh seed${C_OFF}' to load all data through the pipeline."
  if [[ "$mode" == "minimal" ]]; then
    _log "Need all services? Run '${C_BOLD}./manage.sh start --full${C_OFF}'."
  fi
}

# =============================================================================
# COMMAND: stop
# =============================================================================
cmd_stop() {
  _banner
  _require_docker
  _log "Stopping all containers (data volumes preserved) ..."
  docker-compose -f "$COMPOSE_FILE" stop
  _ok "All containers stopped."
}

# =============================================================================
# COMMAND: clean  (destructive — ask for confirmation)
# =============================================================================
cmd_clean() {
  _banner
  _require_docker
  echo -e "${C_RED}${C_BOLD}WARNING: This will remove ALL containers AND their data volumes.${C_OFF}"
  echo -e "${C_RED}MongoDB, Kafka, Redis, TimescaleDB data will be permanently deleted.${C_OFF}"
  echo ""
  read -rp "Type 'yes' to confirm: " confirm
  if [[ "$confirm" != "yes" ]]; then
    _log "Aborted."
    exit 0
  fi

  _log "Stopping and removing containers + volumes ..."
  docker-compose -f "$COMPOSE_FILE" down -v
  _ok "Clean complete — system is in a blank state."
  _log "Run '${C_BOLD}./manage.sh start${C_OFF}' then '${C_BOLD}./manage.sh seed${C_OFF}' to restore."
}

# =============================================================================
# COMMAND: seed
# 4-phase pipeline:
#   1. OptaBatchSeeder: Opta F1/F40 (teams, players, matches)
#   2. OptaBatchSeeder: Opta F24 (match events)
#   3. OptaBatchSeeder: StatsBomb CSV (match events, appended)
#   4. BatchAggregator: player/team statistics from all events
# =============================================================================
cmd_seed() {
  _banner

  # ── pre-flight: check data-sync-service is reachable ─────────────────────
  _log "Checking data-sync-service health ..."
  if ! curl -sf --max-time 5 "${DATA_SYNC_URL}/health" > /dev/null; then
    _warn "data-sync-service is not responding at ${DATA_SYNC_URL}."
    _log  "Trying to start it (infrastructure must already be running) ..."
    docker-compose -f "$COMPOSE_FILE" up -d data-sync-service
    _wait_data_sync
  else
    _ok "data-sync-service is healthy"
  fi

  echo ""
  _log "Seeding pipeline: Local Opta + StatsBomb files → OptaBatchSeeder → MongoDB"
  echo ""

  # ── Phase 1: OptaBatchSeeder (F1, F40) ───────────────────────────────────
  echo "── Phase 1/4: OptaBatchSeeder (teams, players, matches) ──────────────"
  docker-compose -f "$COMPOSE_FILE" exec -T data-sync-service python - <<'SEEDEOF'
import sys, os
sys.path.insert(0, '/app')

try:
    from sync.batch_seeder import OptaBatchSeeder
    seeder = OptaBatchSeeder(
        data_root=os.environ.get('DATA_ROOT', '/data/opta/2019'),
        mongo_uri=os.environ.get('MONGODB_URL', 'mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin'),
        db_name='scoutpro',
        competition_id=int(os.environ.get('COMPETITION_ID', 115)),
        season_id=int(os.environ.get('SEASON_ID', 2019)),
    )
    
    print('[seed] Starting OptaBatchSeeder...')
    seeder.seed_f1()    # Teams and matches
    seeder.seed_f40()   # Players
    seeder.close()
    
    print('[seed] Phase 1 complete: teams, players, matches loaded')
except Exception as e:
    print(f'[seed] ERROR: OptaBatchSeeder failed: {e}', file=sys.stderr)
    sys.exit(1)
SEEDEOF
  
  if [[ $? -ne 0 ]]; then
    _warn "OptaBatchSeeder failed (see logs above)"
    return 1
  fi

  _ok "OptaBatchSeeder complete"
  echo ""

  # ── Phase 2: OptaBatchSeeder F24 (events) ───────────────────────────────
  echo "── Phase 2/4: OptaBatchSeeder (events from F24) ───────────────────────"
  docker-compose -f "$COMPOSE_FILE" exec -T data-sync-service python - <<'EVENTSEOF'
import sys, os
sys.path.insert(0, '/app')

try:
    from sync.batch_seeder import OptaBatchSeeder
    seeder = OptaBatchSeeder(
        data_root=os.environ.get('DATA_ROOT', '/data/opta/2019'),
        mongo_uri=os.environ.get('MONGODB_URL', 'mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin'),
        db_name='scoutpro',
        competition_id=int(os.environ.get('COMPETITION_ID', 115)),
        season_id=int(os.environ.get('SEASON_ID', 2019)),
    )

    print('[seed] Loading events from F24 files...')
    seeder.seed_f24()
    seeder.close()

    print('[seed] Phase 2 complete: events loaded')
except Exception as e:
    print(f'[seed] WARNING: Event seeding failed: {e} (non-fatal)', file=sys.stderr)
EVENTSEOF

  _ok "Events loaded"
  echo ""

  # ── Phase 3: StatsBomb CSV events ────────────────────────────────────────
  echo "── Phase 3/4: OptaBatchSeeder (events from StatsBomb CSVs) ─────────────"
  docker-compose -f "$COMPOSE_FILE" exec -T data-sync-service python - <<'SBEOF'
import sys, os
sys.path.insert(0, '/app')

try:
    from sync.batch_seeder import OptaBatchSeeder
    seeder = OptaBatchSeeder(
        data_root=os.environ.get('DATA_ROOT', '/data/opta/2019'),
        mongo_uri=os.environ.get('MONGODB_URL', 'mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin'),
        db_name='scoutpro',
        competition_id=int(os.environ.get('COMPETITION_ID', 115)),
        season_id=int(os.environ.get('SEASON_ID', 2019)),
    )

    print('[seed] Loading events from StatsBomb CSV files...')
    seeder.seed_statsbomb()
    seeder.close()

    print('[seed] Phase 3 complete: StatsBomb events loaded')
except Exception as e:
    print(f'[seed] WARNING: StatsBomb seeding failed: {e} (non-fatal)', file=sys.stderr)
SBEOF

  _ok "StatsBomb events loaded"
  echo ""

  # ── Phase 4: BatchAggregator (statistics) ────────────────────────────────
  echo "── Phase 4/4: BatchAggregator (player/team statistics) ──────────────"
  docker-compose -f "$COMPOSE_FILE" exec -T statistics-service python - <<'STATSEOF'
import sys, os
sys.path.insert(0, '/app')

try:
    from services.batch_aggregator import BatchAggregator
    agg = BatchAggregator(
        mongo_uri=os.environ.get('MONGODB_URL', 'mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin'),
        db_name='scoutpro',
    )

    print('[seed] Starting BatchAggregator...')
    result = agg.run()
    agg.close()

    print(f'[seed] Phase 4 complete: player_statistics={result.get("player_docs",0)}, team_statistics={result.get("team_docs",0)}')
except Exception as e:
    print(f'[seed] WARNING: BatchAggregator failed: {e} (non-fatal)', file=sys.stderr)
STATSEOF

  _ok "Batch aggregation complete"

  echo ""
  _log "Waiting 3 s for MongoDB to flush all writes ..."
  sleep 3

  # ── Show data counts ──────────────────────────────────────────────────────
  cmd_status

  echo ""
  _ok "Seed complete. Open http://localhost:80 to explore the data."
}

# =============================================================================
# COMMAND: status
# =============================================================================
cmd_status() {
  _banner
  _require_docker

  echo -e "${C_BOLD}Container health:${C_OFF}"
  docker-compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" \
    2>/dev/null || docker-compose -f "$COMPOSE_FILE" ps

  echo ""
  echo -e "${C_BOLD}MongoDB data counts:${C_OFF}"
  docker exec -i scoutpro-mongo mongosh \
    -u root -p scoutpro123 \
    --authenticationDatabase admin \
    --quiet \
    --eval "
      db = db.getSiblingDB('scoutpro');
      var cols = ['players','teams','matches','match_events','player_statistics','team_statistics'];
      cols.forEach(function(c) {
        var n = db.getCollection(c).countDocuments({});
        print('  ' + c.padEnd(25) + n);
      });
    " 2>/dev/null || _warn "MongoDB not reachable (containers may still be starting)"

  echo ""
  echo -e "${C_BOLD}ScoutPro ID coverage:${C_OFF}"
  docker exec -i scoutpro-mongo mongosh \
    -u root -p scoutpro123 \
    --authenticationDatabase admin \
    --quiet \
    --eval "
      db = db.getSiblingDB('scoutpro');
      var pl  = db.players.countDocuments({'scoutpro_id': {\$exists: true}});
      var pl2 = db.players.countDocuments({});
      var ev  = db.match_events.countDocuments({'scoutpro_event_id': {\$exists: true}});
      var ev2 = db.match_events.countDocuments({});
      print('  players with scoutpro_id :  ' + pl + ' / ' + pl2);
      print('  events  with scoutpro_id :  ' + ev + ' / ' + ev2);
    " 2>/dev/null || true

  echo ""
  echo -e "${C_BOLD}Service endpoints:${C_OFF}"
  for spec in "frontend:80:/index.html" "api-gateway:3001:/health" "data-provider:17000:/api/health" "data-sync:28015:/health"; do
    local name port path
    name=$(echo "$spec" | cut -d: -f1)
    port=$(echo "$spec" | cut -d: -f2)
    path=$(echo "$spec" | cut -d: -f3)
    if curl -sf --max-time 3 "http://localhost:${port}${path}" > /dev/null 2>&1; then
      _ok "${name} (port ${port})"
    else
      _warn "${name} (port ${port}) not responding"
    fi
  done
}

# =============================================================================
# COMMAND: validate
# Quick end-to-end checks: provider feeds → sync API → MongoDB counts
# =============================================================================
cmd_validate() {
  _banner
  local pass=0 fail=0

  _check() {
    local label="$1" url="$2" expect="${3:-}"
    local body
    body=$(curl -sf --max-time 10 "$url" 2>/dev/null) || { _warn "FAIL: $label (no response)"; ((fail++)) || true; return; }
    if [[ -n "$expect" ]] && ! echo "$body" | grep -q "$expect"; then
      _warn "FAIL: $label (expected '${expect}' in response)"
      ((fail++)) || true
    else
      _ok "PASS: $label"
      ((pass++)) || true
    fi
  }

  echo "── Provider mock ─────────────────────────────────────────────────────"
  _check "health"          "http://localhost:17000/api/health"      "ok"
  _check "feeds catalogue" "http://localhost:17000/api/feeds"       "opta"
  _check "F1 feed"         "http://localhost:17000/api/football/f1/${COMPETITION_ID}/${SEASON_ID}" ""
  _check "F40 feed"        "http://localhost:17000/api/football/f40/${COMPETITION_ID}/${SEASON_ID}" ""

  echo ""
  echo "── data-sync-service ─────────────────────────────────────────────────"
  _check "health"       "${DATA_SYNC_URL}/health"            "healthy"
  _check "sync status"  "${DATA_SYNC_URL}/api/v2/sync/status" "provider"

  echo ""
  echo "── api-gateway ───────────────────────────────────────────────────────"
  _check "health"   "http://localhost:3001/health"  ""
  _check "players"  "http://localhost:3001/api/players" ""
  _check "matches"  "http://localhost:3001/api/matches" ""

  echo ""
  echo "── MongoDB data ──────────────────────────────────────────────────────"
  local mp mt mm me
  mp=$(docker exec -i scoutpro-mongo mongosh -u root -p scoutpro123 --authenticationDatabase admin --quiet \
       --eval "db=db.getSiblingDB('scoutpro'); print(db.players.countDocuments({}))" 2>/dev/null | tail -1)
  mt=$(docker exec -i scoutpro-mongo mongosh -u root -p scoutpro123 --authenticationDatabase admin --quiet \
       --eval "db=db.getSiblingDB('scoutpro'); print(db.teams.countDocuments({}))" 2>/dev/null | tail -1)
  mm=$(docker exec -i scoutpro-mongo mongosh -u root -p scoutpro123 --authenticationDatabase admin --quiet \
       --eval "db=db.getSiblingDB('scoutpro'); print(db.matches.countDocuments({}))" 2>/dev/null | tail -1)
  me=$(docker exec -i scoutpro-mongo mongosh -u root -p scoutpro123 --authenticationDatabase admin --quiet \
       --eval "db=db.getSiblingDB('scoutpro'); print(db.match_events.countDocuments({}))" 2>/dev/null | tail -1)

  for label_val in "players:$mp" "teams:$mt" "matches:$mm" "match_events:$me"; do
    local lbl cnt
    lbl=$(echo "$label_val" | cut -d: -f1)
    cnt=$(echo "$label_val" | cut -d: -f2)
    if [[ "$cnt" =~ ^[0-9]+$ ]] && [[ "$cnt" -gt 0 ]]; then
      _ok "PASS: ${lbl} has ${cnt} documents"
      ((pass++)) || true
    else
      _warn "FAIL: ${lbl} is empty (run './manage.sh seed')"
      ((fail++)) || true
    fi
  done

  echo ""
  echo "── Summary ───────────────────────────────────────────────────────────"
  _ok  "Passed: ${pass}"
  if [[ $fail -gt 0 ]]; then
    _warn "Failed: ${fail} — run './manage.sh seed' if data is missing"
  fi
}

# =============================================================================
# COMMAND: logs
#
#   ./manage.sh logs                  tail last 50 lines from every service
#   ./manage.sh logs <service>        follow a single service  (e.g. api-gateway)
#   ./manage.sh logs -f               follow ALL services live
#   ./manage.sh logs -f <service>     follow a single service live
#   ./manage.sh logs -n <N> [svc]     show last N lines (default 50)
#   ./manage.sh logs --list           print available service names
# =============================================================================
cmd_logs() {
  _require_docker

  local follow=false
  local lines=50
  local svc=""

  # parse flags
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -f|--follow)   follow=true ; shift ;;
      -n|--lines)    lines="${2:?'-n requires a number'}"; shift 2 ;;
      --list)
        _log "Available services:"
        docker-compose -f "$COMPOSE_FILE" config --services 2>/dev/null | sort | sed 's/^/  /'
        return 0
        ;;
      -*)
        _err "Unknown flag: $1"
        echo "Usage: ./manage.sh logs [-f] [-n N] [service]"
        exit 1
        ;;
      *)  svc="$1"; shift ;;
    esac
  done

  # single-service always follows; multi-service only if -f
  local args=("--timestamps" "--tail=${lines}")
  if [[ -n "$svc" || "$follow" == true ]]; then
    args+=("-f")
  fi

  if [[ -n "$svc" ]]; then
    _log "Logs for '${svc}' (tail=${lines}${follow:+, following}) — Ctrl-C to stop"
    docker-compose -f "$COMPOSE_FILE" logs "${args[@]}" "$svc"
  else
    if [[ "$follow" == true ]]; then
      _log "Following all service logs (tail=${lines}) — Ctrl-C to stop"
    else
      _log "Last ${lines} log lines from every service (use -f to follow)"
    fi
    docker-compose -f "$COMPOSE_FILE" logs "${args[@]}"
  fi
}

# =============================================================================
# COMMAND: restart
# =============================================================================
cmd_restart() {
  cmd_stop
  sleep 2
  cmd_start "$@"
}

# =============================================================================
# ENTRYPOINT
# =============================================================================
CMD="${1:-help}"
shift || true

case "$CMD" in
  build)    cmd_build "$@" ;;
  start)    cmd_start "$@" ;;
  stop)     cmd_stop     ;;
  clean)    cmd_clean    ;;
  seed)     cmd_seed     ;;
  status)   cmd_status   ;;
  validate) cmd_validate ;;
  logs)     cmd_logs "$@" ;;
  restart)  cmd_restart "$@" ;;
  help|--help|-h)
    _banner
    echo "Usage: ./manage.sh <command> [options]"
    echo ""
    echo "  build [svc] Rebuild images from scratch (--no-cache --pull)"
    echo "              Omit [svc] to rebuild everything"
    echo "  start [mode] Start containers"
    echo "              modes: --minimal (default), --full"
    echo "  stop        Stop all containers (data preserved)"
    echo "  clean       Stop + wipe all volumes (destructive)"
    echo "  restart [mode] stop then start (same modes as start)"
    echo ""
    echo "  seed        Trigger full data pipeline:"
    echo "              data-provider → data-sync → Kafka → MongoDB"
    echo "  status      Show container health + MongoDB document counts"
    echo "  validate    End-to-end integration checks"
    echo ""
    echo "  logs [opts] [svc]  Show container logs"
    echo "    (no args)        last 50 lines from every service"
    echo "    <service>        follow a single service live"
    echo "    -f               follow all services live"
    echo "    -f <service>     follow a single service live"
    echo "    -n <N> [svc]     show last N lines"
    echo "    --list           print all service names"
    echo ""
    echo "Environment overrides:"
    echo "  DATA_SYNC_URL    default: http://localhost:28015"
    echo "  COMPETITION_ID   default: 115"
    echo "  SEASON_ID        default: 2019"
    ;;
  *)
    _err "Unknown command: $CMD"
    echo "Run './manage.sh help' for usage."
    exit 1
    ;;
esac
