# ScoutPro - Microservices & Cloud Architecture

**Version**: 2.0
**Date**: 2025-10-04
**Architecture Type**: Event-Driven Microservices with Real-Time Streaming

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Microservices Design](#microservices-design)
3. [Real-Time Streaming Architecture](#real-time-streaming-architecture)
4. [Event-Driven Patterns](#event-driven-patterns)
5. [Data Flow & Integration](#data-flow--integration)
6. [Local Development (Docker Compose)](#local-development-docker-compose)
7. [Cloud Architecture (AWS/Azure/GCP)](#cloud-architecture)
8. [Deployment Strategies](#deployment-strategies)
9. [Monitoring & Observability](#monitoring--observability)

---

## 🏗️ Architecture Overview

### Microservices Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌────────────┬────────────┬────────────┬────────────┬───────────────────┐  │
│  │  Web App   │ Mobile App │ Dashboard  │ 3rd Party  │ WebSocket Clients │  │
│  │  (React)   │ (Native)   │ (Analytics)│    APIs    │  (Live Updates)   │  │
│  └────────────┴────────────┴────────────┴────────────┴───────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                          API GATEWAY / INGRESS                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Kong / Nginx / AWS API Gateway                                      │   │
│  │  • Authentication (JWT)         • Request Routing                    │   │
│  │  • Rate Limiting                • Load Balancing                     │   │
│  │  • SSL Termination              • API Versioning                     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MICROSERVICES LAYER                                 │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │   Player    │  │    Team     │  │   Match     │  │   Statistics     │   │
│  │   Service   │  │   Service   │  │   Service   │  │    Service       │   │
│  │  (Port 8001)│  │ (Port 8002) │  │ (Port 8003) │  │   (Port 8004)    │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────────────┘   │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │     ML      │  │  Live Data  │  │   Search    │  │   Notification   │   │
│  │   Service   │  │   Ingestion │  │   Service   │  │     Service      │   │
│  │  (Port 8005)│  │ (Port 8006) │  │ (Port 8007) │  │   (Port 8008)    │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────────────┘   │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │   Report    │  │   Export    │  │    Video    │  │   Analytics      │   │
│  │   Service   │  │   Service   │  │   Service   │  │     Service      │   │
│  │  (Port 8009)│  │ (Port 8010) │  │ (Port 8011) │  │   (Port 8012)    │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                      EVENT STREAMING / MESSAGE BUS                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Apache Kafka / RabbitMQ / AWS Kinesis                               │   │
│  │                                                                       │   │
│  │  Topics:                                                             │   │
│  │  • player.events          • match.live.updates                       │   │
│  │  • team.events            • statistics.calculated                    │   │
│  │  • ml.predictions         • notifications.send                       │   │
│  │  • search.index.update    • video.analysis.complete                  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                       REAL-TIME STREAMING LAYER                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  WebSocket Server (Socket.IO / AWS AppSync)                          │   │
│  │  • Live match updates         • Player performance streaming         │   │
│  │  • Real-time notifications    • Chat/Collaboration                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Stream Processing (Apache Flink / Spark Streaming / AWS Kinesis)   │   │
│  │  • Event aggregation          • Real-time analytics                 │   │
│  │  • Window operations          • Pattern detection                    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                         │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │   MongoDB   │  │ PostgreSQL  │  │    Redis    │  │   Elasticsearch  │   │
│  │  (NoSQL)    │  │ (Relational)│  │   (Cache)   │  │  (Search/Logs)   │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────────────┘   │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │  TimescaleDB│  │   InfluxDB  │  │     S3      │  │    MinIO         │   │
│  │(Time Series)│  │  (Metrics)  │  │  (Storage)  │  │  (Object Store)  │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL DATA SOURCES                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │  Opta API   │  │  StatsBomb  │  │  Wyscout    │  │   Custom Feeds   │   │
│  │  (Feeds)    │  │    API      │  │    API      │  │   (Webhooks)     │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY & MONITORING                                │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Prometheus + Grafana (Metrics)                                      │   │
│  │  ELK Stack (Logs)                                                    │   │
│  │  Jaeger (Distributed Tracing)                                        │   │
│  │  Sentry (Error Tracking)                                             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Microservices Design

### Service Boundaries & Responsibilities

#### 1. **Player Service** (Port 8001)
**Domain**: Player management and statistics
**Responsibilities**:
- Player CRUD operations
- Player statistics retrieval (per90, percentile)
- Player search and filtering
- Player comparison
- Position mapping

**Technology Stack**:
- FastAPI (Python)
- MongoDB (primary), Opta/StatsBomb (enrichment)
- Redis (caching)

**API Endpoints**:
```
GET    /api/v2/players
GET    /api/v2/players/{id}
POST   /api/v2/players/compare
GET    /api/v2/players/search?q=
GET    /api/v2/players/rank/{stat}
```

**Events Published**:
- `player.created`
- `player.updated`
- `player.statistics.calculated`

**Events Consumed**:
- `match.completed` → Update player stats
- `statistics.recalculated` → Invalidate cache

---

#### 2. **Team Service** (Port 8002)
**Domain**: Team management and analytics
**Responsibilities**:
- Team CRUD operations
- Team statistics and rankings
- Squad management
- Formation analysis

**API Endpoints**:
```
GET    /api/v2/teams
GET    /api/v2/teams/{id}
GET    /api/v2/teams/{id}/squad
GET    /api/v2/teams/{id}/formations
```

**Events Published**:
- `team.created`
- `team.squad.updated`
- `team.formation.changed`

---

#### 3. **Match Service** (Port 8003)
**Domain**: Match data and events
**Responsibilities**:
- Match CRUD operations
- Match events (goals, cards, subs)
- Match statistics
- Historical match data

**API Endpoints**:
```
GET    /api/v2/matches
GET    /api/v2/matches/{id}
GET    /api/v2/matches/{id}/events
GET    /api/v2/matches/{id}/stats
```

**Events Published**:
- `match.created`
- `match.started`
- `match.completed`
- `match.event.occurred` (goal, card, sub)

---

#### 4. **Live Data Ingestion Service** (Port 8006)
**Domain**: Real-time data ingestion from external sources
**Responsibilities**:
- Poll Opta live feeds (F1, F9, F24)
- WebSocket connections to data providers
- Data normalization and validation
- Event streaming to Kafka

**Technology Stack**:
- Python/Go (high performance)
- WebSocket clients
- Kafka Producer
- Redis (deduplication)

**Data Flow**:
```
Opta API (polling every 5s)
    ↓
Normalize & Validate
    ↓
Kafka Topic: match.live.updates
    ↓
Consumers: Match Service, Statistics Service, WebSocket Server
```

**Events Published**:
- `match.live.update` (score, stats, minute)
- `match.event.live` (goal, card, VAR)
- `player.performance.live`

---

#### 5. **Statistics Service** (Port 8004)
**Domain**: Statistical calculations and aggregations
**Responsibilities**:
- Real-time stat calculations
- Per90/percentile computations
- Historical aggregations
- Custom metric formulas

**Technology Stack**:
- Python (pandas, numpy)
- TimescaleDB (time-series storage)
- Redis (pre-computed cache)

**Processing Pipeline**:
```
Event Stream → Calculate Stats → Store → Publish
     ↓              ↓              ↓         ↓
Kafka Topic    NumPy/Pandas   TimescaleDB  Kafka
```

**Events Consumed**:
- `match.event.occurred`
- `match.completed`

**Events Published**:
- `statistics.calculated`
- `player.stats.updated`
- `team.stats.updated`

---

#### 6. **ML Service** (Port 8005)
**Domain**: Machine Learning training and predictions
**Responsibilities**:
- Model training
- Real-time predictions
- Feature engineering
- Model versioning (MLflow)

**API Endpoints**:
```
POST   /api/v2/ml/train
POST   /api/v2/ml/predict
GET    /api/v2/ml/models
GET    /api/v2/ml/models/{id}/metrics
```

**Events Consumed**:
- `statistics.calculated` → Trigger retraining
- `match.completed` → Update training data

**Events Published**:
- `ml.model.trained`
- `ml.prediction.made`

---

#### 7. **Search Service** (Port 8007)
**Domain**: Full-text search and indexing
**Responsibilities**:
- Elasticsearch index management
- Advanced search queries
- Autocomplete/suggestions
- Faceted search

**Technology Stack**:
- FastAPI
- Elasticsearch
- Redis (query cache)

**API Endpoints**:
```
GET    /api/v2/search?q=&filters=
GET    /api/v2/search/suggest?q=
```

**Events Consumed**:
- `player.created/updated` → Index update
- `team.created/updated` → Index update
- `match.completed` → Index match data

---

#### 8. **Notification Service** (Port 8008)
**Domain**: User notifications and alerts
**Responsibilities**:
- Push notifications
- Email notifications
- In-app notifications
- Alert rule engine

**Technology Stack**:
- Python/Node.js
- Firebase Cloud Messaging
- SendGrid (email)
- Redis (user preferences)

**Events Consumed**:
- `match.event.live` → Notify subscribed users
- `ml.prediction.made` → Alert if significant
- `player.performance.anomaly` → Send alert

---

#### 9. **Video Service** (Port 8011)
**Domain**: Video analysis and clips
**Responsibilities**:
- Video upload/storage (S3/MinIO)
- Frame extraction
- Object detection (players, ball)
- Clip generation

**Technology Stack**:
- Python (OpenCV, FFmpeg)
- S3/MinIO (storage)
- GPU workers for ML models

---

#### 10. **Analytics Service** (Port 8012)
**Domain**: Business intelligence and dashboards
**Responsibilities**:
- Pre-aggregated reports
- Dashboard data
- Trend analysis
- KPI calculations

**API Endpoints**:
```
GET    /api/v2/analytics/dashboard
GET    /api/v2/analytics/trends/{metric}
GET    /api/v2/analytics/reports/{id}
```

---

#### 11. **Report Service** (Port 8009)
**Domain**: Report generation and export
**Responsibilities**:
- PDF report generation
- Excel export
- Custom templates
- Scheduled reports

**Events Consumed**:
- `report.requested` → Generate async

---

#### 12. **Export Service** (Port 8010)
**Domain**: Data export in various formats
**Responsibilities**:
- CSV export
- JSON export
- Excel with charts
- API data dumps

---

## 🌊 Real-Time Streaming Architecture

### Live Match Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL DATA SOURCES                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                     │
│  │ Opta Feed  │  │  StatsBomb │  │  Custom    │                     │
│  │  WebSocket │  │   API      │  │  Webhooks  │                     │
│  └────────────┘  └────────────┘  └────────────┘                     │
└─────────────────────────────────────────────────────────────────────┘
         ↓                 ↓                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│              LIVE DATA INGESTION SERVICE (8006)                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Ingestion Workers (Multiple instances for redundancy)       │   │
│  │                                                               │   │
│  │  1. WebSocket Listener → Opta F24 events                     │   │
│  │  2. HTTP Poller (5s interval) → Opta F1/F9 feeds             │   │
│  │  3. Webhook Receiver → Custom feeds                          │   │
│  │                                                               │   │
│  │  Data Processing:                                            │   │
│  │  ├→ Deduplication (Redis)                                    │   │
│  │  ├→ Validation (Schema check)                                │   │
│  │  ├→ Normalization (Unified format)                           │   │
│  │  └→ Enrichment (Player/Team lookup)                          │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      KAFKA / EVENT STREAM                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Topics (Partitioned by match_id for ordering):              │   │
│  │                                                               │   │
│  │  • match.live.raw           (Raw feed data)                  │   │
│  │  • match.live.normalized    (Processed events)               │   │
│  │  • match.events.stream      (Discrete events: goal, card)    │   │
│  │  • player.performance.live  (Per-player stats)               │   │
│  │  • match.stats.windowed     (5-min aggregated stats)         │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐
│  STREAM         │  │  STATISTICS     │  │  WEBSOCKET              │
│  PROCESSOR      │  │  SERVICE        │  │  SERVER                 │
│  (Flink/Spark)  │  │  (Consumer)     │  │  (Socket.IO)            │
│                 │  │                 │  │                         │
│  • Window ops   │  │  • Calculate    │  │  • Maintain client      │
│  • Aggregation  │  │    stats        │  │    connections          │
│  • Pattern      │  │  • Store in     │  │  • Push to browser      │
│    detection    │  │    TimescaleDB  │  │  • Room management      │
│                 │  │  • Publish      │  │    (per match)          │
│  Outputs:       │  │    updates      │  │                         │
│  ├→ Possession  │  │                 │  │  Rooms:                 │
│  ├→ xG trends   │  │                 │  │  • match:{id}           │
│  ├→ Pressure    │  │                 │  │  • player:{id}          │
│  └→ Heatmaps    │  │                 │  │  • team:{id}            │
└─────────────────┘  └─────────────────┘  └─────────────────────────┘
         ↓                    ↓                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA STORAGE                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ TimescaleDB  │  │   MongoDB    │  │       Redis              │  │
│  │ (Time Series)│  │  (Documents) │  │  (Real-time cache)       │  │
│  │              │  │              │  │                          │  │
│  │ • Match stats│  │ • Match data │  │ • Current match state    │  │
│  │   per minute │  │ • Events     │  │ • Player positions       │  │
│  │ • Player     │  │ • Player     │  │ • Live scores            │  │
│  │   metrics    │  │   stats      │  │ • Connection tracking    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT APPLICATIONS                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  React App (WebSocket client)                                │   │
│  │  ┌────────────────────────────────────────────────────────┐  │   │
│  │  │  useEffect(() => {                                     │  │   │
│  │  │    socket.emit('join', {matchId: '123'})              │  │   │
│  │  │    socket.on('match:update', (data) => {              │  │   │
│  │  │      // Update score, stats, events                   │  │   │
│  │  │    })                                                  │  │   │
│  │  │  }, [])                                                │  │   │
│  │  └────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### WebSocket Server Implementation

```python
# websocket_server/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi_socketio import SocketManager
import asyncio
import aioredis
from aiokafka import AIOKafkaConsumer

app = FastAPI()
socket_manager = SocketManager(app=app)

# Redis for pub/sub and state
redis = aioredis.from_url("redis://localhost:6379")

# Kafka consumer for live events
kafka_consumer = AIOKafkaConsumer(
    'match.live.normalized',
    'match.events.stream',
    bootstrap_servers=['localhost:9092']
)

# Room management
class RoomManager:
    def __init__(self):
        self.rooms = {}  # match_id -> set of session_ids

    async def join_match(self, match_id: str, session_id: str):
        if match_id not in self.rooms:
            self.rooms[match_id] = set()
        self.rooms[match_id].add(session_id)
        await socket_manager.emit(f'match:{match_id}', session_id)

    async def leave_match(self, match_id: str, session_id: str):
        if match_id in self.rooms:
            self.rooms[match_id].discard(session_id)

room_manager = RoomManager()

@app.on_event("startup")
async def startup():
    """Start Kafka consumer in background"""
    asyncio.create_task(consume_kafka_events())

async def consume_kafka_events():
    """Consume Kafka events and broadcast to WebSocket clients"""
    await kafka_consumer.start()
    try:
        async for msg in kafka_consumer:
            event = json.loads(msg.value.decode())
            match_id = event.get('match_id')

            # Broadcast to all clients in this match room
            if match_id and match_id in room_manager.rooms:
                await socket_manager.emit(
                    f'match:update',
                    event,
                    room=f'match:{match_id}'
                )
    finally:
        await kafka_consumer.stop()

@socket_manager.on('join_match')
async def join_match(sid, data):
    """Client joins a match room"""
    match_id = data.get('match_id')
    await room_manager.join_match(match_id, sid)

    # Send current match state from Redis
    current_state = await redis.get(f'match:{match_id}:state')
    if current_state:
        await socket_manager.emit('match:state', json.loads(current_state), to=sid)

@socket_manager.on('leave_match')
async def leave_match(sid, data):
    """Client leaves a match room"""
    match_id = data.get('match_id')
    await room_manager.leave_match(match_id, sid)

@socket_manager.on('disconnect')
async def disconnect(sid):
    """Handle client disconnect"""
    # Remove from all rooms
    for match_id in list(room_manager.rooms.keys()):
        await room_manager.leave_match(match_id, sid)
```

### Stream Processing (Apache Flink Example)

```python
# stream_processor/flink_job.py
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors import FlinkKafkaConsumer, FlinkKafkaProducer
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.window import TumblingProcessingTimeWindows
from pyflink.common.time import Time
import json

env = StreamExecutionEnvironment.get_execution_environment()

# Kafka source
kafka_consumer = FlinkKafkaConsumer(
    topics='match.live.normalized',
    deserialization_schema=SimpleStringSchema(),
    properties={
        'bootstrap.servers': 'kafka:9092',
        'group.id': 'stream-processor'
    }
)

# Kafka sink
kafka_producer = FlinkKafkaProducer(
    topic='match.stats.windowed',
    serialization_schema=SimpleStringSchema(),
    producer_config={'bootstrap.servers': 'kafka:9092'}
)

# Processing pipeline
stream = env.add_source(kafka_consumer)

# Parse JSON
parsed_stream = stream.map(lambda x: json.loads(x))

# Key by match_id and player_id
keyed_stream = parsed_stream.key_by(lambda x: (x['match_id'], x.get('player_id')))

# 5-minute tumbling windows
windowed_stream = keyed_stream.window(
    TumblingProcessingTimeWindows.of(Time.minutes(5))
)

# Aggregate statistics
def aggregate_stats(events):
    """Aggregate events in window"""
    stats = {
        'match_id': events[0]['match_id'],
        'player_id': events[0].get('player_id'),
        'window_start': events[0]['timestamp'],
        'window_end': events[-1]['timestamp'],
        'total_passes': sum(1 for e in events if e['type'] == 'pass'),
        'successful_passes': sum(1 for e in events if e['type'] == 'pass' and e.get('outcome') == 'success'),
        'shots': sum(1 for e in events if e['type'] == 'shot'),
        'possession_seconds': calculate_possession(events),
        'distance_covered': calculate_distance(events)
    }
    return json.dumps(stats)

aggregated_stream = windowed_stream.apply(aggregate_stats)

# Sink to Kafka
aggregated_stream.add_sink(kafka_producer)

# Execute
env.execute("Match Stats Aggregator")

def calculate_possession(events):
    """Calculate possession time from events"""
    # Implementation here
    pass

def calculate_distance(events):
    """Calculate distance covered from position events"""
    # Implementation here
    pass
```

---

## 🔄 Event-Driven Patterns

### Event Types

#### 1. **Domain Events** (Past tense - what happened)
```python
# player.events
player.created = {
    "event_id": "uuid",
    "event_type": "player.created",
    "timestamp": "2025-10-04T19:00:00Z",
    "data": {
        "player_id": "123",
        "name": "Player Name",
        "position": "Forward"
    },
    "metadata": {
        "user_id": "user_123",
        "source": "player-service"
    }
}

player.statistics.calculated = {
    "event_id": "uuid",
    "event_type": "player.statistics.calculated",
    "timestamp": "2025-10-04T19:05:00Z",
    "data": {
        "player_id": "123",
        "stat_type": "shot",
        "stats": {
            "goals": 15,
            "shots_on_target": 45,
            "xG": 12.3
        },
        "per_90": true
    }
}
```

#### 2. **Live Events** (Real-time updates)
```python
# match.live.events
match.event.live = {
    "event_id": "uuid",
    "event_type": "match.event.live",
    "timestamp": "2025-10-04T19:45:23Z",
    "data": {
        "match_id": "match_456",
        "minute": 67,
        "type": "goal",
        "team_id": "team_789",
        "player_id": "player_123",
        "assist_player_id": "player_456",
        "xG": 0.45,
        "coordinates": {"x": 88, "y": 45}
    },
    "sequence_number": 1234  # For ordering
}

match.live.update = {
    "event_id": "uuid",
    "event_type": "match.live.update",
    "timestamp": "2025-10-04T19:45:00Z",
    "data": {
        "match_id": "match_456",
        "minute": 67,
        "score": {"home": 2, "away": 1},
        "stats": {
            "possession": {"home": 58, "away": 42},
            "shots": {"home": 12, "away": 8},
            "xG": {"home": 1.8, "away": 0.9}
        }
    }
}
```

#### 3. **Command Events** (Requests for action)
```python
# commands
report.generate.requested = {
    "command_id": "uuid",
    "command_type": "report.generate.requested",
    "timestamp": "2025-10-04T19:00:00Z",
    "data": {
        "report_type": "player_season_analysis",
        "player_id": "123",
        "season_id": "2023-2024",
        "format": "pdf"
    },
    "reply_to": "reports.generated"  # Reply topic
}
```

### Event Flow Patterns

#### Pattern 1: Event-Driven Saga (Distributed Transaction)

```python
# Scenario: Generate comprehensive player report

# 1. User requests report
report.generate.requested → Report Service

# 2. Report Service orchestrates:
#    (Publishes commands, listens for responses)

Report Service:
    ├→ Publish: player.data.fetch.requested → Player Service
    ├→ Publish: statistics.fetch.requested → Statistics Service
    ├→ Publish: video.clips.fetch.requested → Video Service
    ├→ Publish: ml.insights.fetch.requested → ML Service

    # Listen for responses:
    ├← Subscribe: player.data.fetched
    ├← Subscribe: statistics.fetched
    ├← Subscribe: video.clips.fetched
    ├← Subscribe: ml.insights.fetched

    # When all received:
    └→ Generate PDF
    └→ Publish: report.generated

# 3. Notification Service listens
report.generated → Notification Service → Email to user
```

#### Pattern 2: Event Sourcing for Match State

```python
# Match state is built from event stream

Event Stream:
├→ match.created (t=0)
├→ match.started (t=5)
├→ match.event.live (goal, t=23min)
├→ match.event.live (yellow_card, t=34min)
├→ match.event.live (substitution, t=45min)
├→ match.halftime (t=45min)
├→ match.resumed (t=46min)
├→ match.event.live (goal, t=67min)
└→ match.completed (t=90min)

# Rebuild state by replaying events:
def rebuild_match_state(match_id):
    events = kafka.consume_from_beginning(f"match:{match_id}")

    state = MatchState()
    for event in events:
        state.apply(event)

    return state

# Current state is always computable:
current_state = rebuild_match_state("match_456")
```

#### Pattern 3: CQRS (Command Query Responsibility Segregation)

```python
# Write Model (Commands)
POST /api/v2/players → Player Service → player.created event → Kafka

# Read Model (Queries)
GET /api/v2/players → Player Read Service → MongoDB/Elasticsearch

# Event Handler (Sync read model)
class PlayerEventHandler:
    async def handle_player_created(self, event):
        # Update MongoDB read model
        await mongo_db.players.insert_one(event.data)

        # Update Elasticsearch search index
        await es.index(index='players', body=event.data)

        # Update Redis cache
        await redis.set(f"player:{event.data.id}", json.dumps(event.data))

# Benefits:
# - Optimized writes (fast event publishing)
# - Optimized reads (denormalized, indexed)
# - Can have multiple read models for different use cases
```

---

## 🐳 Local Development (Docker Compose)

### Complete docker-compose.yml

```yaml
version: '3.9'

services:
  # ============ API GATEWAY ============
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - player-service
      - team-service
      - match-service
    networks:
      - scoutpro-network

  # ============ MICROSERVICES ============
  player-service:
    build:
      context: ./services/player-service
      dockerfile: Dockerfile
    ports:
      - "8001:8000"
    environment:
      - MONGODB_URL=mongodb://mongo:27017
      - REDIS_URL=redis://redis:6379
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - SERVICE_NAME=player-service
    depends_on:
      - mongo
      - redis
      - kafka
    volumes:
      - ./services/player-service:/app
    networks:
      - scoutpro-network
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure

  team-service:
    build:
      context: ./services/team-service
      dockerfile: Dockerfile
    ports:
      - "8002:8000"
    environment:
      - MONGODB_URL=mongodb://mongo:27017
      - REDIS_URL=redis://redis:6379
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    depends_on:
      - mongo
      - redis
      - kafka
    networks:
      - scoutpro-network

  match-service:
    build:
      context: ./services/match-service
      dockerfile: Dockerfile
    ports:
      - "8003:8000"
    environment:
      - MONGODB_URL=mongodb://mongo:27017
      - TIMESCALEDB_URL=postgresql://timescale:5432/scoutpro
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    depends_on:
      - mongo
      - timescaledb
      - kafka
    networks:
      - scoutpro-network

  statistics-service:
    build:
      context: ./services/statistics-service
      dockerfile: Dockerfile
    ports:
      - "8004:8000"
    environment:
      - TIMESCALEDB_URL=postgresql://timescale:5432/scoutpro
      - REDIS_URL=redis://redis:6379
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    depends_on:
      - timescaledb
      - kafka
    networks:
      - scoutpro-network

  ml-service:
    build:
      context: ./services/ml-service
      dockerfile: Dockerfile
    ports:
      - "8005:8000"
    environment:
      - MONGODB_URL=mongodb://mongo:27017
      - MLFLOW_TRACKING_URI=http://mlflow:5000
      - S3_ENDPOINT=http://minio:9000
    depends_on:
      - mongo
      - minio
      - mlflow
    volumes:
      - ml-models:/models
    networks:
      - scoutpro-network

  live-ingestion-service:
    build:
      context: ./services/live-ingestion-service
      dockerfile: Dockerfile
    ports:
      - "8006:8000"
    environment:
      - OPTA_API_KEY=${OPTA_API_KEY}
      - STATSBOMB_API_KEY=${STATSBOMB_API_KEY}
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - REDIS_URL=redis://redis:6379
    depends_on:
      - kafka
      - redis
    networks:
      - scoutpro-network

  search-service:
    build:
      context: ./services/search-service
      dockerfile: Dockerfile
    ports:
      - "8007:8000"
    environment:
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - REDIS_URL=redis://redis:6379
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    depends_on:
      - elasticsearch
      - kafka
    networks:
      - scoutpro-network

  notification-service:
    build:
      context: ./services/notification-service
      dockerfile: Dockerfile
    ports:
      - "8008:8000"
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - REDIS_URL=redis://redis:6379
      - FIREBASE_CREDENTIALS=${FIREBASE_CREDENTIALS}
      - SENDGRID_API_KEY=${SENDGRID_API_KEY}
    depends_on:
      - kafka
      - redis
    networks:
      - scoutpro-network

  websocket-server:
    build:
      context: ./services/websocket-server
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - REDIS_URL=redis://redis:6379
    depends_on:
      - kafka
      - redis
    networks:
      - scoutpro-network

  stream-processor:
    build:
      context: ./services/stream-processor
      dockerfile: Dockerfile
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - TIMESCALEDB_URL=postgresql://timescale:5432/scoutpro
      - FLINK_JOBMANAGER_HOST=flink-jobmanager
    depends_on:
      - kafka
      - timescaledb
      - flink-jobmanager
    networks:
      - scoutpro-network

  # ============ MESSAGE BROKER ============
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"
    networks:
      - scoutpro-network

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
      - "9093:9093"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:9093
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
    volumes:
      - kafka-data:/var/lib/kafka/data
    networks:
      - scoutpro-network

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    ports:
      - "8090:8080"
    environment:
      - KAFKA_CLUSTERS_0_NAME=local
      - KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS=kafka:9092
    depends_on:
      - kafka
    networks:
      - scoutpro-network

  # ============ DATABASES ============
  mongo:
    image: mongo:7.0
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: scoutpro123
      MONGO_INITDB_DATABASE: scoutpro
    volumes:
      - mongo-data:/data/db
      - ./init-mongo.js:/docker-entrypoint-initdb.d/init-mongo.js
    networks:
      - scoutpro-network

  timescaledb:
    image: timescale/timescaledb:latest-pg15
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: scoutpro
      POSTGRES_USER: scoutpro
      POSTGRES_PASSWORD: scoutpro123
    volumes:
      - timescale-data:/var/lib/postgresql/data
      - ./init-timescale.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - scoutpro-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    networks:
      - scoutpro-network

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.0
    ports:
      - "9200:9200"
      - "9300:9300"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - es-data:/usr/share/elasticsearch/data
    networks:
      - scoutpro-network

  # ============ OBJECT STORAGE ============
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin123
    command: server /data --console-address ":9001"
    volumes:
      - minio-data:/data
    networks:
      - scoutpro-network

  # ============ ML OPS ============
  mlflow:
    image: ghcr.io/mlflow/mlflow:latest
    ports:
      - "5000:5000"
    environment:
      - MLFLOW_BACKEND_STORE_URI=postgresql://scoutpro:scoutpro123@timescaledb:5432/mlflow
      - MLFLOW_S3_ENDPOINT_URL=http://minio:9000
      - AWS_ACCESS_KEY_ID=minioadmin
      - AWS_SECRET_ACCESS_KEY=minioadmin123
    depends_on:
      - timescaledb
      - minio
    networks:
      - scoutpro-network

  # ============ STREAM PROCESSING ============
  flink-jobmanager:
    image: flink:1.18-scala_2.12
    ports:
      - "8081:8081"
    command: jobmanager
    environment:
      - |
        FLINK_PROPERTIES=
        jobmanager.rpc.address: flink-jobmanager
    networks:
      - scoutpro-network

  flink-taskmanager:
    image: flink:1.18-scala_2.12
    depends_on:
      - flink-jobmanager
    command: taskmanager
    environment:
      - |
        FLINK_PROPERTIES=
        jobmanager.rpc.address: flink-jobmanager
        taskmanager.numberOfTaskSlots: 4
    networks:
      - scoutpro-network
    deploy:
      replicas: 2

  # ============ MONITORING ============
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - scoutpro-network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_INSTALL_PLUGINS=redis-datasource
    volumes:
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus
    networks:
      - scoutpro-network

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "5775:5775/udp"
      - "6831:6831/udp"
      - "6832:6832/udp"
      - "5778:5778"
      - "16686:16686"
      - "14268:14268"
      - "14250:14250"
      - "9411:9411"
    environment:
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
    networks:
      - scoutpro-network

  # ============ LOGGING ============
  elasticsearch-logs:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.0
    ports:
      - "9201:9200"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - es-logs-data:/usr/share/elasticsearch/data
    networks:
      - scoutpro-network

  logstash:
    image: docker.elastic.co/logstash/logstash:8.10.0
    ports:
      - "5044:5044"
      - "9600:9600"
    volumes:
      - ./logging/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    environment:
      - "LS_JAVA_OPTS=-Xmx256m -Xms256m"
    depends_on:
      - elasticsearch-logs
    networks:
      - scoutpro-network

  kibana:
    image: docker.elastic.co/kibana/kibana:8.10.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch-logs:9200
    depends_on:
      - elasticsearch-logs
    networks:
      - scoutpro-network

networks:
  scoutpro-network:
    driver: bridge

volumes:
  mongo-data:
  timescale-data:
  redis-data:
  es-data:
  es-logs-data:
  minio-data:
  kafka-data:
  ml-models:
  prometheus-data:
  grafana-data:
```

### Service Dockerfile Template

```dockerfile
# services/player-service/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Startup Script

```bash
#!/bin/bash
# start-local.sh

echo "🚀 Starting ScoutPro Local Environment..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Creating from template..."
    cp .env.example .env
    echo "⚠️  Please configure .env file with your API keys"
    exit 1
fi

# Create required directories
mkdir -p {services,monitoring,logging,nginx}

# Build and start services
echo "📦 Building services..."
docker-compose build

echo "🔧 Starting infrastructure (databases, Kafka)..."
docker-compose up -d mongo timescaledb redis kafka elasticsearch minio

echo "⏳ Waiting for infrastructure to be ready..."
sleep 20

echo "🚀 Starting microservices..."
docker-compose up -d

echo "📊 Starting monitoring stack..."
docker-compose up -d prometheus grafana jaeger

echo "✅ ScoutPro is starting up!"
echo ""
echo "📍 Access points:"
echo "   - API Gateway: http://localhost:80"
echo "   - Grafana: http://localhost:3000 (admin/admin123)"
echo "   - Jaeger: http://localhost:16686"
echo "   - Kafka UI: http://localhost:8090"
echo "   - Kibana: http://localhost:5601"
echo "   - MLflow: http://localhost:5000"
echo ""
echo "📝 View logs: docker-compose logs -f [service-name]"
echo "🛑 Stop all: docker-compose down"
```

---

## ☁️ Cloud Architecture

### AWS Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            USERS / CLIENTS                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         AWS ROUTE 53 (DNS)                               │
│                   scoutpro.com → CloudFront/ALB                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                   AWS CLOUDFRONT (CDN)                                   │
│  • Static assets (React app)                                            │
│  • Edge caching                                                          │
│  • SSL/TLS termination                                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│              AWS APPLICATION LOAD BALANCER (ALB)                         │
│  • Path-based routing                                                    │
│  • Health checks                                                         │
│  • SSL termination                                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                     AWS API GATEWAY (Optional)                           │
│  • REST API management                                                   │
│  • WebSocket support                                                     │
│  • Throttling & rate limiting                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                AMAZON EKS (Kubernetes) / ECS (Fargate)                   │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                        MICROSERVICES                                │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │ │
│  │  │   Player    │  │    Team     │  │   Match     │               │ │
│  │  │   Service   │  │   Service   │  │   Service   │               │ │
│  │  │  (ECS Task) │  │  (ECS Task) │  │  (ECS Task) │               │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │ │
│  │                                                                     │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │ │
│  │  │ Statistics  │  │     ML      │  │Live Ingest  │               │ │
│  │  │   Service   │  │   Service   │  │   Service   │               │ │
│  │  │  (ECS Task) │  │  (ECS Task) │  │  (ECS Task) │               │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │ │
│  │                                                                     │ │
│  │  Auto Scaling Groups (based on CPU/Memory/Custom Metrics)          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    MESSAGE STREAMING / EVENT BUS                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Amazon MSK (Managed Kafka)                                        │ │
│  │  • 3 broker minimum (multi-AZ)                                     │ │
│  │  • Topic: player.events, match.live.updates, etc.                 │ │
│  │  • Auto-scaling enabled                                            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                             OR                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Amazon Kinesis Data Streams                                       │ │
│  │  • Serverless streaming                                            │ │
│  │  • On-demand capacity mode                                         │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      STREAM PROCESSING                                   │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  AWS Lambda (Event-driven processing)                              │ │
│  │  • Triggered by Kinesis/MSK                                        │ │
│  │  • Stateless aggregations                                          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                             OR                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Amazon Kinesis Data Analytics (Apache Flink)                     │ │
│  │  • Complex event processing                                        │ │
│  │  • Windowed aggregations                                           │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                          REAL-TIME LAYER                                 │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  AWS AppSync (GraphQL WebSocket)                                   │ │
│  │  • Real-time subscriptions                                         │ │
│  │  • Managed WebSocket connections                                   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                             OR                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Amazon API Gateway WebSocket API                                  │ │
│  │  • Custom WebSocket server on ECS                                  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐   │
│  │  DocumentDB │  │     RDS     │  │ ElastiCache │  │ OpenSearch   │   │
│  │  (MongoDB)  │  │ PostgreSQL  │  │   (Redis)   │  │(Elasticsearch│   │
│  │             │  │             │  │             │  │    + Kibana) │   │
│  │ • Multi-AZ  │  │ • Multi-AZ  │  │ • Cluster   │  │              │   │
│  │ • Auto      │  │ • Read      │  │   mode      │  │ • Full-text  │   │
│  │   backup    │  │   replicas  │  │             │  │   search     │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────────┘   │
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐   │
│  │ Timestream  │  │  DynamoDB   │  │     S3      │  │   Glacier    │   │
│  │(Time Series)│  │  (NoSQL)    │  │  (Storage)  │  │  (Archive)   │   │
│  │             │  │             │  │             │  │              │   │
│  │ • Match     │  │ • Sessions  │  │ • Videos    │  │ • Old data   │   │
│  │   metrics   │  │ • Real-time │  │ • Models    │  │   archival   │   │
│  │   per min   │  │   state     │  │ • Reports   │  │              │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                          ML/AI LAYER                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Amazon SageMaker                                                  │ │
│  │  • Training jobs (spot instances)                                  │ │
│  │  • Model hosting (endpoints)                                       │ │
│  │  • Model registry                                                  │ │
│  │  • A/B testing                                                     │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  AWS Lambda (Inference)                                            │ │
│  │  • Lightweight predictions                                         │ │
│  │  • Cost-effective for sporadic loads                               │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    MONITORING & OBSERVABILITY                            │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Amazon CloudWatch                                                 │ │
│  │  • Metrics, Logs, Dashboards                                       │ │
│  │  • Alarms & Auto-scaling triggers                                  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  AWS X-Ray                                                         │ │
│  │  • Distributed tracing                                             │ │
│  │  • Service maps                                                    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Amazon Managed Grafana + Prometheus                               │ │
│  │  • Custom dashboards                                               │ │
│  │  • Multi-source metrics                                            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                           SECURITY                                       │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  AWS WAF (Web Application Firewall)                                │ │
│  │  AWS Shield (DDoS protection)                                      │ │
│  │  AWS Secrets Manager (API keys, credentials)                       │ │
│  │  AWS IAM (Identity & Access Management)                            │ │
│  │  VPC (Network isolation)                                           │ │
│  │  AWS Certificate Manager (SSL/TLS)                                 │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### AWS Service Mapping

| Component | Local (Docker) | AWS Cloud |
|-----------|---------------|-----------|
| **API Gateway** | Nginx | AWS ALB + API Gateway |
| **Microservices** | Docker Containers | ECS Fargate / EKS |
| **Message Queue** | Kafka | Amazon MSK / Kinesis |
| **Stream Processing** | Apache Flink | Kinesis Analytics / Lambda |
| **WebSocket** | Socket.IO Server | AWS AppSync / API Gateway WS |
| **MongoDB** | MongoDB Container | Amazon DocumentDB |
| **PostgreSQL** | PostgreSQL Container | Amazon RDS PostgreSQL |
| **TimescaleDB** | TimescaleDB Container | Timestream / RDS with extension |
| **Redis** | Redis Container | Amazon ElastiCache Redis |
| **Elasticsearch** | Elasticsearch Container | Amazon OpenSearch |
| **Object Storage** | MinIO | Amazon S3 |
| **ML Platform** | MLflow | Amazon SageMaker |
| **Monitoring** | Prometheus + Grafana | CloudWatch + Managed Grafana |
| **Tracing** | Jaeger | AWS X-Ray |
| **Logging** | ELK Stack | CloudWatch Logs + OpenSearch |
| **Secrets** | .env files | AWS Secrets Manager |

### Azure Alternative

```
Azure Front Door (CDN)
  ↓
Azure Application Gateway (WAF)
  ↓
Azure Kubernetes Service (AKS)
  ↓
Azure Event Hubs (Kafka-compatible)
  ↓
Azure Stream Analytics (Flink alternative)
  ↓
Data Layer:
├→ Azure Cosmos DB (MongoDB API)
├→ Azure Database for PostgreSQL
├→ Azure Cache for Redis
├→ Azure Cognitive Search (Elasticsearch alternative)
├→ Azure Data Explorer (Time-series)
└→ Azure Blob Storage

ML: Azure Machine Learning
Monitoring: Azure Monitor + Application Insights
```

### GCP Alternative

```
Cloud CDN + Cloud Load Balancing
  ↓
Google Kubernetes Engine (GKE)
  ↓
Cloud Pub/Sub (Message Queue)
  ↓
Dataflow (Apache Beam - Stream processing)
  ↓
Data Layer:
├→ Cloud Firestore / MongoDB Atlas on GCP
├→ Cloud SQL (PostgreSQL)
├→ Cloud Memorystore (Redis)
├→ Elasticsearch on GKE
├→ BigQuery (Time-series analytics)
└→ Cloud Storage

ML: Vertex AI
Monitoring: Cloud Monitoring + Cloud Trace
```

---

## 🚀 Deployment Strategies

### Blue-Green Deployment

```yaml
# kubernetes/deployment-blue-green.yaml
apiVersion: v1
kind: Service
metadata:
  name: player-service
spec:
  selector:
    app: player-service
    version: blue  # Switch to 'green' for deployment
  ports:
    - port: 80
      targetPort: 8000
---
# Blue deployment (current production)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: player-service-blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: player-service
      version: blue
  template:
    metadata:
      labels:
        app: player-service
        version: blue
    spec:
      containers:
      - name: player-service
        image: player-service:v1.2.0
---
# Green deployment (new version)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: player-service-green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: player-service
      version: green
  template:
    metadata:
      labels:
        app: player-service
        version: green
    spec:
      containers:
      - name: player-service
        image: player-service:v1.3.0

# Switch traffic:
# kubectl patch service player-service -p '{"spec":{"selector":{"version":"green"}}}'
```

### Canary Deployment

```yaml
# kubernetes/canary-deployment.yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: player-service
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: player-service
  service:
    port: 80
  analysis:
    interval: 1m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 1m
    - name: request-duration
      thresholdRange:
        max: 500
      interval: 1m
  # Progressive rollout: 10% → 20% → 30% → ... → 100%
```

### Auto-Scaling Configuration

```yaml
# kubernetes/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: player-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: player-service
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
```

---

## 📊 Monitoring & Observability

### Metrics Collection

```python
# shared/monitoring.py
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Define metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'active_websocket_connections',
    'Number of active WebSocket connections',
    ['service']
)

kafka_messages_consumed = Counter(
    'kafka_messages_consumed_total',
    'Total Kafka messages consumed',
    ['topic', 'service']
)

ml_predictions_total = Counter(
    'ml_predictions_total',
    'Total ML predictions made',
    ['model_id', 'model_version']
)

ml_prediction_duration = Histogram(
    'ml_prediction_duration_seconds',
    'ML prediction duration',
    ['model_id']
)

# Decorator for tracking endpoints
def track_endpoint(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        method = request.method
        endpoint = request.path

        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            status = result.status_code
            return result
        except Exception as e:
            status = 500
            raise
        finally:
            duration = time.time() - start_time
            http_requests_total.labels(method, endpoint, status).inc()
            http_request_duration_seconds.labels(method, endpoint).observe(duration)

    return wrapper

# Usage in FastAPI
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Auto-instrument FastAPI
Instrumentator().instrument(app).expose(app)

@app.get("/api/v2/players/{player_id}")
@track_endpoint
async def get_player(player_id: str):
    # ... implementation
    pass
```

### Distributed Tracing

```python
# shared/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.kafka import KafkaInstrumentor

# Initialize tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Configure Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)

trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Auto-instrument FastAPI
app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

# Auto-instrument Kafka
KafkaInstrumentor().instrument()

# Manual tracing
@app.get("/api/v2/players/{player_id}")
async def get_player(player_id: str):
    with tracer.start_as_current_span("get_player") as span:
        span.set_attribute("player_id", player_id)

        # Trace repository call
        with tracer.start_as_current_span("repository.get_player"):
            player = await player_repo.get_by_id(player_id)

        # Trace stats calculation
        with tracer.start_as_current_span("stats.calculate"):
            stats = await stats_service.calculate(player_id)

        return player
```

### Logging Strategy

```python
# shared/logging_config.py
import logging
import json
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['service'] = 'player-service'
        log_record['environment'] = os.getenv('ENV', 'development')
        log_record['trace_id'] = get_trace_id()  # From OpenTelemetry context

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Console handler (JSON format)
    handler = logging.StreamHandler()
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Elasticsearch handler (via Logstash)
    logstash_handler = logstash.LogstashHandler(
        'logstash', 5044, version=1
    )
    logger.addHandler(logstash_handler)

# Usage
logger = logging.getLogger(__name__)
logger.info("Player retrieved", extra={
    "player_id": player_id,
    "duration_ms": duration,
    "cache_hit": cache_hit
})
```

---

## 🎯 Summary

### Key Architectural Decisions

1. **Microservices over Monolith**: Better scalability, team autonomy, fault isolation
2. **Event-Driven Architecture**: Loose coupling, real-time processing, async workflows
3. **Kafka/Kinesis for Streaming**: High throughput, durability, replay capability
4. **Multi-Database Strategy**: Right tool for right data (MongoDB, PostgreSQL, TimescaleDB, Redis)
5. **Docker Compose for Local**: Fast development, production parity
6. **Kubernetes/ECS for Cloud**: Auto-scaling, self-healing, service discovery
7. **Observability First**: Metrics, logs, traces from day one

### Next Steps

1. ✅ Review architecture diagrams
2. 📝 Finalize service boundaries
3. 🔧 Set up Docker Compose locally
4. 🚀 Implement Player Service (reference implementation)
5. 📊 Configure monitoring stack
6. ☁️ Choose cloud provider (AWS/Azure/GCP)
7. 🎯 Deploy MVP to cloud

---

**Document Version**: 1.0
**Last Updated**: 2025-10-04
**Author**: ScoutPro Engineering Team
