#!/bin/bash

# ScoutPro - Kafka Topics Creation Script
# This script creates all required Kafka topics for the ScoutPro microservices architecture

set -e

echo "========================================="
echo "ScoutPro - Kafka Topics Setup"
echo "========================================="
echo ""

# Configuration
KAFKA_CONTAINER="kafka"
BOOTSTRAP_SERVER="localhost:9092"
PARTITIONS=3
REPLICATION_FACTOR=1

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to create a topic
create_topic() {
    local topic_name=$1
    local partitions=${2:-$PARTITIONS}
    local replication=${3:-$REPLICATION_FACTOR}

    echo -n "Creating topic: ${topic_name}..."

    # Check if topic already exists
    if docker-compose exec -T kafka kafka-topics --bootstrap-server $BOOTSTRAP_SERVER --list 2>/dev/null | grep -q "^${topic_name}$"; then
        echo -e " ${YELLOW}Already exists${NC}"
        return 0
    fi

    # Create the topic
    if docker-compose exec -T kafka kafka-topics \
        --create \
        --bootstrap-server $BOOTSTRAP_SERVER \
        --topic $topic_name \
        --partitions $partitions \
        --replication-factor $replication \
        --if-not-exists \
        2>/dev/null; then
        echo -e " ${GREEN}Created${NC}"
    else
        echo -e " ${RED}Failed${NC}"
        return 1
    fi
}

# Check if Kafka is running
echo "Checking if Kafka is running..."
if ! docker-compose ps kafka 2>/dev/null | grep -q "Up"; then
    echo -e "${RED}Error: Kafka container is not running${NC}"
    echo "Please start Kafka first: docker-compose up -d kafka"
    exit 1
fi

echo -e "${GREEN}Kafka is running${NC}"
echo ""

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
sleep 5

echo ""
echo "========================================="
echo "Creating Core Event Topics"
echo "========================================="

# Core event topics
create_topic "player.events" 5 1
create_topic "team.events" 3 1
create_topic "match.events" 5 1

echo ""
echo "========================================="
echo "Creating Live Data Topics"
echo "========================================="

# Live data topics (higher partitions for throughput)
create_topic "match.live.updates" 10 1
create_topic "match.live.raw" 10 1
create_topic "match.live.normalized" 10 1
create_topic "match.events.stream" 8 1
create_topic "player.performance.live" 8 1
create_topic "match.stats.windowed" 5 1

echo ""
echo "========================================="
echo "Creating Statistics Topics"
echo "========================================="

# Statistics topics
create_topic "statistics.calculated" 5 1
create_topic "statistics.recalculated" 3 1
create_topic "player.stats.updated" 5 1
create_topic "team.stats.updated" 3 1

echo ""
echo "========================================="
echo "Creating ML Topics"
echo "========================================="

# ML topics
create_topic "ml.predictions" 5 1
create_topic "ml.model.trained" 3 1
create_topic "ml.prediction.made" 5 1
create_topic "ml.model.train.requested" 3 1

echo ""
echo "========================================="
echo "Creating Search & Notification Topics"
echo "========================================="

# Search topics
create_topic "search.index.update" 5 1
create_topic "search.query.log" 3 1

# Notification topics
create_topic "notifications.send" 5 1
create_topic "notifications.sent" 3 1

echo ""
echo "========================================="
echo "Creating Report & Export Topics"
echo "========================================="

# Report topics
create_topic "report.requested" 3 1
create_topic "report.generated" 3 1
create_topic "report.failed" 3 1

# Export topics
create_topic "export.requested" 3 1
create_topic "export.completed" 3 1

echo ""
echo "========================================="
echo "Creating Video Topics"
echo "========================================="

# Video topics
create_topic "video.uploaded" 3 1
create_topic "video.processed" 3 1
create_topic "video.analysis.complete" 3 1

echo ""
echo "========================================="
echo "List All Topics"
echo "========================================="

echo ""
echo "Created topics:"
docker-compose exec -T kafka kafka-topics --bootstrap-server $BOOTSTRAP_SERVER --list | sort

echo ""
echo "========================================="
echo "Topic Details"
echo "========================================="
echo ""

# Show details for key topics
echo "Player Events Topic:"
docker-compose exec -T kafka kafka-topics --bootstrap-server $BOOTSTRAP_SERVER --describe --topic player.events

echo ""
echo "Match Live Updates Topic:"
docker-compose exec -T kafka kafka-topics --bootstrap-server $BOOTSTRAP_SERVER --describe --topic match.live.updates

echo ""
echo "========================================="
echo "Kafka Topics Setup Complete!"
echo "========================================="
echo ""
echo -e "${GREEN}All topics created successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Start backend services: docker-compose up -d"
echo "2. Check Kafka UI: http://localhost:8090"
echo "3. Test event publishing from services"
echo ""
