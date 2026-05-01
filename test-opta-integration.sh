#!/bin/bash

# test-opta-integration.sh
# Tests the ScoutPro ingestion flow using a single Opta 2019 match to avoid LLM rate limits.

MATCH_ID="1080974"
DATA_DIR="./data/opta/2019"
ENDPOINT="http://localhost:28006/api/v2/ingestion/events" # Using direct ingestion service host port
MATCH_API="http://localhost:28003/api/v2/matches"
GATEWAY_MATCH_API="http://localhost:3001/api/matches"
PLAYER_API="http://localhost:28001/api/v2/players"
TEAM_API="http://localhost:28002/api/v2/teams"
GATEWAY_PLAYER_API="http://localhost:3001/api/players"
GATEWAY_TEAM_API="http://localhost:3001/api/teams"

echo "=================================="
echo " ScoutPro Automated Opta Test"
echo "=================================="

# 1. Start Infrastructure
echo "[1/4] Starting backend infrastructure..."
docker-compose up -d mongo redis kafka zookeeper timescaledb elasticsearch api-gateway live-ingestion-service match-service player-service team-service statistics-service ml-service search-service notification-service websocket-server
echo "Waiting 30 seconds for containers to be ready..."
sleep 10

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
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$MATCH_API/$MATCH_ID")
if [ "$HTTP_STATUS" -eq 200 ]; then
    echo "✅ Success: Match $MATCH_ID data is available in the system."
else
    echo "❌ Error: Match $MATCH_ID could not be accessed. (HTTP Status: $HTTP_STATUS)"
fi

EVENT_COUNT=$(curl -s "$MATCH_API/$MATCH_ID/events" | python3 -c 'import json,sys; data=json.load(sys.stdin); print(len(data.get("data", data)) if isinstance(data, dict) else len(data))' 2>/dev/null || echo "0")
echo "ℹ️ Match events visible through match-service: $EVENT_COUNT"

GATEWAY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$GATEWAY_MATCH_API/$MATCH_ID")
if [ "$GATEWAY_STATUS" -eq 200 ]; then
    echo "✅ Success: Match $MATCH_ID is also reachable through the API gateway."
else
    echo "❌ Error: Match $MATCH_ID is not reachable through the API gateway. (HTTP Status: $GATEWAY_STATUS)"
fi

PLAYER_COUNT=$(curl -s "$PLAYER_API" | python3 -c 'import json,sys; data=json.load(sys.stdin); print(len(data.get("data", [])))' 2>/dev/null || echo "0")
TEAM_COUNT=$(curl -s "$TEAM_API" | python3 -c 'import json,sys; data=json.load(sys.stdin); print(len(data.get("data", [])))' 2>/dev/null || echo "0")
GATEWAY_PLAYER_COUNT=$(curl -s "$GATEWAY_PLAYER_API" | python3 -c 'import json,sys; data=json.load(sys.stdin); print(len(data) if isinstance(data, list) else 0)' 2>/dev/null || echo "0")
GATEWAY_TEAM_COUNT=$(curl -s "$GATEWAY_TEAM_API" | python3 -c 'import json,sys; data=json.load(sys.stdin); print(len(data) if isinstance(data, list) else 0)' 2>/dev/null || echo "0")

echo "ℹ️ Player read model count through player-service: $PLAYER_COUNT"
echo "ℹ️ Team read model count through team-service: $TEAM_COUNT"
echo "ℹ️ Player read model count through gateway: $GATEWAY_PLAYER_COUNT"
echo "ℹ️ Team read model count through gateway: $GATEWAY_TEAM_COUNT"

if [ "$PLAYER_COUNT" -gt 0 ] && [ "$TEAM_COUNT" -gt 0 ] && [ "$GATEWAY_PLAYER_COUNT" -gt 0 ] && [ "$GATEWAY_TEAM_COUNT" -gt 0 ]; then
    echo "✅ Success: Player and team read models are populated and reachable through the gateway."
else
    echo "❌ Error: Player/team read models were not fully populated through the service and gateway path."
fi

echo "=================================="
echo " Test Complete."
echo "=================================="
