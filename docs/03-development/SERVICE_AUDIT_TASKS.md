
# ScoutPro Backend Service Audit & Task Roadmap

**Date**: 2026-04-26
**Architect**: Scout Architect 
**Focus**: Scalability, Live Data Ingestion Reliability, Kafka Resilience, Domain-Driven Design (DDD)

## Executive Sandbox Audit
A deep architectural dive into the microservices reveals that while the vertical separation of concerns (microservice boundaries) is theoretically sound, the **internal logic implementations are too simplistic for high-velocity elite sports tracking data**. 

Currently, services act as generic synchronous CRUD APIs. Real-time data endpoints handle heavy parsing, DB writes, and message publishing identically inside the synchronous HTTP thread. This setup will invariably fail (timeout, CPU lock, or OOM) when ingesting multi-megabyte Opta XMLs or 10Hz NBA tracking feeds. 

We must refactor the architecture towards **Dumb Pipes, Smart Consumers, and Dedicated Stream Processors**.

---

## 1. `live-ingestion-service` (The Edge)
**Current Flaws**:
- Uses a monolithic `LiveDataProcessor` that simultaneously inserts events into MongoDB, updates match stats, and publishes to Kafka.
- Parses data in memory on the FastAPI event loop, blocking subsequent requests.
- Does not utilize a fast-acknowledgment standard for high-throughput webhook targets.

**Tasks needed for next iteration**:
- [ ] **Refactor into a "Dumb Pipe"**: Strip all MongoDB/TimescaleDB inserts out of the `LiveDataProcessor`.
- [ ] **Implement Raw Kafka Publishing**: Parse only the envelope (Match ID, source) and push the raw JSON/XML bytes directly to a `raw.events` Kafka topic.
- [ ] **Immediate Ack**: Ensure endpoints return `202 Accepted` in < 50ms to the Opta/StatsBomb webhook clients.

## 2. `shared/messaging` (The Backbone)
**Current Flaws**:
- `AIOKafkaConsumer` is configured with `enable_auto_commit=True` and `auto_commit_interval_ms=1000`. If parsing exceptions occur, messages are lost because the offset is committed automatically in the background.
- Missing standardized routing or Topic Partitioning Keys based on `match_id`, leading to unordered processing across multiple consumer pods.

**Tasks needed for next iteration**:
- [ ] **Disable Auto-Commit**: Refactor `KafkaConsumerClient` to use manual offset commits (`enable_auto_commit=False`) *only after* a message is successfully parsed and written to DB.
- [ ] **Strict Partitioning**: Guarantee that `match_id` is always passed as the Kafka grouping key in `AIOKafkaProducer` so the same match is always processed by the exact same pod, ensuring chronological timeline integrity.
- [ ] **Dead Letter Queue (DLQ)**: Implement logic to route poison-pill events to a DLQ topic instead of crashing the consumer loop.

## 3. `statistics-service` & `match-service` (The Processors)
**Current Flaws**:
- Live statistics are currently pushed simultaneously alongside raw events in the ingestion layer.
- `match_service.py` is a passive CRUD wrapper around MongoDB mappings without explicit business logic for Expected Goals (xG), Possession windowing, etc.
- No genuine usage of TimescaleDB's hypertable continuous aggregates.

**Tasks needed for next iteration**:
- [ ] **Migrate to Stream Processor**: Establish the `statistics-service` as an async Kafka consumer pulling from `raw.events` or `processed.events`.
- [ ] **Sliding Window Aggregation**: Calculate possession, pass clustering, and match pressure in-memory using tumbling windows before flushing batches to TimescaleDB.
- [ ] **Domain-Driven Design (DDD)**: Embed domain methods (like `calculate_xg`, `detect_tactical_shift`) inside `business/` logic folders rather than fetching loose dictionaries from `repositories`.

## 4. `player-service` & `team-service`
**Current Flaws**:
- Both are functioning purely as data-retrieval wrappers. Cache TTL caching uses massive stringified keys lacking intelligent cache invalidation.
- When live data arrives for a player in a game, the `player:{player_id}` cache in Redis does not proactively invalidate.

**Tasks needed for next iteration**:
- [ ] **Event-Driven Cache Invalidation**: Subscribe to `match.completed` or `player.stats_updated` Kafka events to immediately purge or overwrite Redis keys rather than waiting for generic 300s TTLs.
- [ ] **Paginated Cursors**: Replace hardcoded `limit=100` defaults with cursor-based pagination for rapid mobile query traversal.

## 5. `ml-service` (The Brain)
**Current Flaws**:
- Implements a generic 2020-era wrapper around Scikit-Learn algorithms (`LinearRegression`, `DecisionTree`) but lacks bespoke pipelines mapping to football schemas (StatsBomb/Opta features).

**Tasks needed for next iteration**:
- [ ] **Feature Engineering Pipeline**: Add an adapter that sanitizes raw spatial coordinates (x,y points) and parses them into standardized PyTorch/Scikit tensors specifically for things like *Pass Success Probability* or *Pitch Control*.

---
*Created for implementation in Phase 2 Chat Session.*
