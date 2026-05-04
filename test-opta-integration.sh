#!/usr/bin/env bash
# =============================================================================
#  ScoutPro — Opta Integration Validation Script
# =============================================================================
#
#  Tests the full ingestion pipeline using the data-sync-service HTTP API.
#  No longer calls any standalone scripts (all deleted).
#
#  Pipeline under test:
#    data-provider-mock (./data/) → data-sync-service → Kafka → MongoDB
#
#  Usage:
#    ./test-opta-integration.sh
#    MATCH_ID=2086929 ./test-opta-integration.sh
#    WAIT=20 ./test-opta-integration.sh
#
# =============================================================================
set -euo pipefail

COMPETITION_ID="${COMPETITION_ID:-115}"
SEASON_ID="${SEASON_ID:-2019}"
MATCH_ID="${MATCH_ID:-1080974}"
WAIT="${WAIT:-15}"
DATA_SYNC_URL="${DATA_SYNC_URL:-http://localhost:28015}"
GATEWAY_URL="${GATEWAY_URL:-http://localhost:3001}"
PROVIDER_URL="${PROVIDER_URL:-http://localhost:7000}"

C_GREEN='\033[0;32m'
C_YELLOW='\033[1;33m'
C_BLUE='\033[0;34m'
C_BOLD='\033[1m'
C_OFF='\033[0m'
_ok()  { echo -e "${C_GREEN}[  OK  ]${C_OFF} $*"; }
_warn(){ echo -e "${C_YELLOW}[ WARN ]${C_OFF} $*"; }
_log() { echo -e "${C_BLUE}[ INFO ]${C_OFF} $*"; }

PASS=0; FAIL=0

_check_http() {
  local label="$1" url="$2" expect="${3:-}"
  local body http_code
  http_code=$(curl -s -o /tmp/sp_test_body.txt -w "%{http_code}" --max-time 10 "$url" 2>/dev/null) || http_code="000"
  body=$(cat /tmp/sp_test_body.txt 2>/dev/null)
  if [[ "$http_code" != "200" ]]; then
    _warn "FAIL: $label → HTTP $http_code"; ((FAIL++)) || true; return
  fi
  if [[ -n "$expect" ]] && ! echo "$body" | grep -q "$expect"; then
    _warn "FAIL: $label → missing '${expect}'"; ((FAIL++)) || true; return
  fi
  _ok "PASS: $label"; ((PASS++)) || true
}

_trigger() {
  local entity="$1" provider="${2:-opta}"
  _log "  POST /api/v2/sync/trigger/${entity}?provider=${provider} ..."
  local resp status records
  resp=$(curl -sf -X POST "${DATA_SYNC_URL}/api/v2/sync/trigger/${entity}" \
    -G \
    --data-urlencode "provider=${provider}" \
    --data-urlencode "competition_id=${COMPETITION_ID}" \
    --data-urlencode "season_id=${SEASON_ID}" \
    -H "Accept: application/json" --max-time 300 \
  ) || { _warn "sync/${entity} returned error"; return; }
  status=$(echo "$resp"  | python3 -c "import sys,json;print(json.load(sys.stdin).get('status','?'))"         2>/dev/null)
  records=$(echo "$resp" | python3 -c "import sys,json;print(json.load(sys.stdin).get('records_synced',0))"  2>/dev/null)
  _ok "${entity}: status=${status}  records=${records}"
}

_mongo_count() {
  docker exec -i scoutpro-mongo mongosh \
    -u root -p scoutpro123 --authenticationDatabase admin --quiet \
    --eval "db=db.getSiblingDB('scoutpro');print(db.getCollection('${1}').countDocuments({}))" \
    2>/dev/null | tail -1
}

# =============================================================================
echo ""
echo -e "${C_BOLD}ScoutPro — Opta Integration Test${C_OFF}"
echo "  Competition: ${COMPETITION_ID}  Season: ${SEASON_ID}  Match: ${MATCH_ID}"
echo ""

# ── 1: Pre-flight ─────────────────────────────────────────────────────────────
echo -e "${C_BOLD}[1/5] Pre-flight: services reachable${C_OFF}"
_check_http "data-provider /api/health"  "${PROVIDER_URL}/api/health"  "ok"
_check_http "data-sync-service /health"  "${DATA_SYNC_URL}/health"     "healthy"
_check_http "api-gateway /health"        "${GATEWAY_URL}/health"       ""

# ── 2: Provider feed availability ────────────────────────────────────────────
echo ""
echo -e "${C_BOLD}[2/5] Data-provider feed availability${C_OFF}"
_check_http "F1  (schedule)"  "${PROVIDER_URL}/api/football/f1/${COMPETITION_ID}/${SEASON_ID}"  ""
_check_http "F40 (squads)"   "${PROVIDER_URL}/api/football/f40/${COMPETITION_ID}/${SEASON_ID}" ""
_check_http "F24 (events)"   "${PROVIDER_URL}/api/football/f24/${COMPETITION_ID}/${SEASON_ID}/${MATCH_ID}" ""
_check_http "feeds catalogue" "${PROVIDER_URL}/api/feeds" "opta"

# ── 3: Trigger sync pipeline ─────────────────────────────────────────────────
echo ""
echo -e "${C_BOLD}[3/5] Triggering sync pipeline: data-provider → data-sync → Kafka → MongoDB${C_OFF}"
_trigger "teams"   "opta"
_trigger "players" "opta"
_trigger "matches" "opta"
_trigger "events"  "opta"

_log "Waiting ${WAIT}s for Kafka consumers to flush to MongoDB ..."
sleep "$WAIT"

# ── 4: MongoDB verification ───────────────────────────────────────────────────
echo ""
echo -e "${C_BOLD}[4/5] MongoDB document counts${C_OFF}"
for col in players teams matches match_events; do
  cnt=$(_mongo_count "$col")
  if [[ "$cnt" =~ ^[0-9]+$ ]] && [[ "$cnt" -gt 0 ]]; then
    _ok "PASS: ${col} — ${cnt} documents"; ((PASS++)) || true
  else
    _warn "FAIL: ${col} is empty"; ((FAIL++)) || true
  fi
done

_log "ScoutPro ID coverage:"
docker exec -i scoutpro-mongo mongosh \
  -u root -p scoutpro123 --authenticationDatabase admin --quiet \
  --eval "
    db=db.getSiblingDB('scoutpro');
    print('  players with scoutpro_id : '+db.players.countDocuments({'scoutpro_id':{\$exists:true}})+' / '+db.players.countDocuments({}));
    print('  events  with event_source: '+db.match_events.countDocuments({'event_source':{\$exists:true}})+' / '+db.match_events.countDocuments({}));
  " 2>/dev/null || true

_log "Sample shot event from match ${MATCH_ID}:"
docker exec -i scoutpro-mongo mongosh \
  -u root -p scoutpro123 --authenticationDatabase admin --quiet \
  --eval "
    db=db.getSiblingDB('scoutpro');
    var ev=db.match_events.findOne({matchID:'${MATCH_ID}',type_name:'miss'});
    if(ev){print('  type='+ev.type_name+' player='+ev.player_id+' source='+ev.event_source+' loc='+JSON.stringify(ev.location));}
    else{print('  (no miss events for match ${MATCH_ID})'); }
  " 2>/dev/null || true

# ── 5: API Gateway ────────────────────────────────────────────────────────────
echo ""
echo -e "${C_BOLD}[5/5] API Gateway spot-check${C_OFF}"
_check_http "GET /api/players" "${GATEWAY_URL}/api/players" ""
_check_http "GET /api/matches" "${GATEWAY_URL}/api/matches" ""
_check_http "GET /api/teams"   "${GATEWAY_URL}/api/teams"   ""

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════════"
_ok  "Passed: ${PASS}"
[[ $FAIL -gt 0 ]] && _warn "Failed: ${FAIL} — run './manage.sh seed' if data is missing" || true
echo "  Troubleshoot: ./manage.sh logs data-sync-service"
echo "═══════════════════════════════════════════════════════════════"
