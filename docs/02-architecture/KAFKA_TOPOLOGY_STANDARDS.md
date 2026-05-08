# ScoutPro Kafka Topology Standards

This document defines the systematic standard for naming and configuring Kafka topics in the ScoutPro architecture, particularly focusing on the dual-stream topology required for live data ingestion versus batch historical data loading.

## Topic Naming Convention

All new Kafka topics must follow this template pattern:
`<domain>.<stream>.<entity_or_action>[.<qualifier>]`

### 1. Domain
The overarching bounded context the topic serves:
- `match`: Data about games, schedules, and on-pitch event streams
- `player`: Player profiles, mappings, transfers
- `team`: Team metadata, squads, staff
- `statistics`: Computed aggregates, rankings, and standard metrics
- `ml`: Predictions, model training, similarity outputs
- `batch`: Large-scale data ingestion and async jobs
- `notifications`: User-facing alerts and WebSocket payloads

### 2. Stream Type (Critical for Dual-Stream Architecture)
Specifies the latency sensitivity and durability requirement of the data:
- `live`: Low-latency, high-throughput, short retention. Used for matches currently in progress. 
- `batch`: High-durability, longer retention, background processing. Used for historical data syncs, model training, or bulk imports.
- `core`: Standard CRUD domain events (e.g., player profile updated)
- `system`: App mechanics (exports, reports, logs)

### 3. Entity or Action
What exactly is in the message:
- Entities: `events`, `metadata`, `squad`, `stats`
- Actions: `updated`, `requested`, `processed`

## Configuration Templates

### Template A: Live Stream (`*.live.*`)
**Purpose:** Real-time data from Opta webhooks or live match scrappers.
- **Partitions:** 8-10 (High concurrency for quick consumer group distribution)
- **Retention:** 24 Hours (`retention.ms=86400000`)
- **Cleanup Policy:** `delete` (No need to hold live websockets long-term)
- **Examples:** `match.live.raw`, `match.live.normalized`

### Template B: Batch / Historical Stream (`*.batch.*`)
**Purpose:** Large historical data loads (e.g., scraping 10 seasons of StatsBomb CSVs). Must not block live match processing.
- **Partitions:** 3-5 (Steady, durable processing)
- **Retention:** 7 Days (`retention.ms=604800000`) or Log Compaction
- **Cleanup Policy:** `compact` or `delete`
- **Examples:** `batch.historical.matches`, `batch.historical.events`

### Template C: Core Domain Events (`*.core.*` or `domain.entity.action`)
**Purpose:** System of record state changes.
- **Partitions:** 5
- **Retention:** Infinite / Log Compaction (`cleanup.policy=compact`)
- **Examples:** `player.events`, `team.events`

## Dual-Stream Implementation

To ensure StatsBomb chunk imports don't delay Opta's real-time goal notifications, Consumers must implement isolated Consumer Groups matching the streams:

1. `LiveIngestionConsumerGroup` listens to `match.live.raw`
2. `BatchHistoricalConsumerGroup` listens to `batch.historical.events`

This ensures batch pipeline saturation never creates lag on the live match websocket push lines.
