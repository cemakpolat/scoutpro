#!/usr/bin/env bash
# ----------------------------------------------------------------
# seed-data.sh  —  ScoutPro one-command first-setup
#
# Starts the minimum infrastructure required for seeding, then
# runs the data-seeder container which:
#   • pulls all Opta (F1/F9/F24/F40) + StatsBomb data from the
#     local mock provider
#   • parses, normalises, and publishes events through Kafka
#   • upserts everything into MongoDB and TimescaleDB
#   • runs enrichment (F40 biometrics + match/event name linking)
#
# Usage:
#   ./seed-data.sh               # seed everything
#   ./seed-data.sh --no-build    # skip docker build (use cached image)
# ----------------------------------------------------------------
set -euo pipefail

COMPOSE_MAIN="docker-compose.yml"
COMPOSE_SEED="docker-compose.seed.yml"

BUILD_FLAG="--build"
for arg in "$@"; do
  [[ "$arg" == "--no-build" ]] && BUILD_FLAG=""
done

echo ""
echo "======================================================================"
echo "  ScoutPro — Data Seeder"
echo "======================================================================"
echo ""

# ── Step 1: start required infrastructure ────────────────────────
echo "[seed-data] Starting infrastructure services ..."
docker compose -f "$COMPOSE_MAIN" up -d \
  zookeeper kafka \
  mongo timescaledb redis \
  data-provider

echo ""
echo "[seed-data] Infrastructure containers started."
echo "[seed-data] The seeder will wait internally for each service"
echo "            to pass its healthcheck before proceeding."
echo ""

# ── Step 2: build (optional) and run the seeder ──────────────────
echo "[seed-data] Running data-seeder ..."
echo ""

docker compose \
  -f "$COMPOSE_MAIN" \
  -f "$COMPOSE_SEED" \
  run --rm $BUILD_FLAG \
  data-seeder

EXIT_CODE=$?

echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
  echo "======================================================================"
  echo "  Seeding complete. Start the full system with:"
  echo ""
  echo "    docker compose up -d"
  echo ""
  echo "  Verify data in MongoDB:"
  echo "    docker exec -it scoutpro-mongo mongosh -u root -p scoutpro123 \\"
  echo "      --eval 'use scoutpro; printjson({players: db.players.countDocuments(), teams: db.teams.countDocuments(), matches: db.matches.countDocuments(), events: db.match_events.countDocuments()})'"
  echo "======================================================================"
else
  echo "======================================================================"
  echo "  ERROR: seeder exited with code $EXIT_CODE."
  echo "  Check the output above for details."
  echo "======================================================================"
  exit $EXIT_CODE
fi
