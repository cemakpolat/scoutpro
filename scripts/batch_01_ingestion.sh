#!/usr/bin/env bash
# ---------------------------------------------------------
# batch_01_ingestion.sh
# Retrieves data from provider and stores all data, 
# events, players, etc. into TimescaleDB and MongoDB.
# ---------------------------------------------------------

echo "=========================================================="
echo "⚽ ScoutPro - Batch Ingestion Pipeline"
echo "=========================================================="

export PYTHONPATH="$(pwd)"
export MONGODB_HOST="localhost"
export MONGODB_PORT="27017"
export MONGODB_DATABASE="scoutpro"

# We assume data-sync-service pulls data continuously or on-demand
echo "Starting data-sync-service for full batch synchronization..."
python3 services/data-sync-service/main.py --once

# If there is specific TimescaleDB seed logic:
if [ -f "scripts/seed_all_opta.py" ]; then
    echo "Running local file seeder to patch legacy data if needed..."
    python3 scripts/seed_all_opta.py
fi

echo "=========================================================="
echo "✅ Batch Ingestion Complete."
echo "=========================================================="
