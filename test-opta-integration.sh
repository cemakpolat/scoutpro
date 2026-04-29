#!/bin/bash

# test-opta-integration.sh
# Tests the ScoutPro ingestion flow using a single Opta 2019 match to avoid LLM rate limits.

MATCH_ID="1080974"
DATA_DIR="./data/opta/2019"
ENDPOINT="http://localhost:8006/api/v2/ingestion/events" # Using direct ingestion container port (8006)

echo "=================================="
echo " ScoutPro Automated Opta Test"
echo "=================================="

# 1. Start Infrastructure
echo "[1/4] Starting backend infrastructure..."
docker-compose up -d mongo redis kafka zookeeper timescaledb elasticsearch api-gateway live-ingestion-service match-service player-service team-service statistics-service ml-service search-service notification-service websocket-server
echo "Waiting 30 seconds for containers to be ready..."
sleep 30

# 2. Ingest Match Files (F1, F9, F40, F24)
echo "[2/4] Ingesting Match: $MATCH_ID"

# Ingest F1 (Fixtures/Schedules)
if [ -f "$DATA_DIR/f1_115_2019" ]; then
    echo " -> Ingesting F1..."
    python3 scripts/ingest_real_data.py --source opta --filepath "$DATA_DIR/f1_115_2019" --endpoint "$ENDPOINT/$MATCH_ID" --match_id "$MATCH_ID"
fi

# Ingest F9 (Match Results/Lineups)
if [ -f "$DATA_DIR/f9_115_2019" ]; then
    echo " -> Ingesting F9..."
    python3 scripts/ingest_real_data.py --source opta --filepath "$DATA_DIR/f9_115_2019" --endpoint "$ENDPOINT/$MATCH_ID" --match_id "$MATCH_ID"
fi

# Ingest F40 (Squads)
if [ -f "$DATA_DIR/f40_115_2019" ]; then
    echo " -> Ingesting F40..."
    python3 scripts/ingest_real_data.py --source opta --filepath "$DATA_DIR/f40_115_2019" --endpoint "$ENDPOINT/$MATCH_ID" --match_id "$MATCH_ID"
fi

# Ingest F24 (Live Events) for specific match
F24_FILE="$DATA_DIR/f24_115_2019_$MATCH_ID"
if [ -f "$F24_FILE" ]; then
    echo " -> Ingesting F24 Events..."
    python3 scripts/ingest_real_data.py --source opta --filepath "$F24_FILE" --endpoint "$ENDPOINT/$MATCH_ID" --match_id "$MATCH_ID"
fi

# 3. Wait for Async Processing
echo "[3/4] Waiting 10 seconds for message brokers (Kafka/RabbitMQ) to process events..."
sleep 10

# 4. Verify System Database / API View
echo "[4/4] Verifying Processed Data..."

# Fetch the match through the Match Service
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8003/api/v2/matches/$MATCH_ID")
if [ "$HTTP_STATUS" -eq 200 ]; then
    echo "✅ Success: Match $MATCH_ID data is available in the system."
else
    echo "❌ Error: Match $MATCH_ID could not be accessed. (HTTP Status: $HTTP_STATUS)"
fi

echo "=================================="
echo " Test Complete."
echo "=================================="
