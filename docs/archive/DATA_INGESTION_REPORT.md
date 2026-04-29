# Data Ingestion & Transformation Report

**Author:** Scout Architect
**Date:** April 28, 2026
**Project:** ScoutPro (Football Analytics Platform)

## Overview
This architectural report outlines how raw football data providers (Opta, StatsBomb) are ingested into the system, transformed into unified domain entities, dispatched through the data pipeline, and ultimately consumed by internal microservices.

---

## 1. Data Ingestion Layer

The injection point for manual or external test feeds originates via the `ingest_real_data.py` script. The process operates as follows:

1. **Extraction & Chunking:** The script parses local StatsBomb `.csv` or Opta JSON files into raw event dictionaries. It segments the heavy event data into discrete chunks of 100 events to prevent massive payload transmission spikes.
2. **Transmission:** Each batch is sent securely via HTTP POST to the `live-ingestion-service` endpoint (`/api/v2/ingestion/events/{match_id}`).

Inside the **Live Ingestion Service**:
- To maintain optimal throughput, FastAPI accepts the payload and immediately returns an HTTP `202 Accepted`.
- It offloads the extensive transformation step to an asynchronous `BackgroundTasks` function which securely calls the `LiveDataProcessor`.

---

## 2. Transformation & Unified Model Mapping

The ingestion service relies entirely on the **Clean Architecture Domain Entities** found in the `shared/adapters` directory. 

1. **Stream Execution:** Under `LiveDataProcessor.process_live_update()`, incoming raw structures are routed into designated parsers.
2. **Current Implementation Gap:** The processor currently hardcodes `OptaParser().parse_events()` regardless of the payload's origin provider. *(Architect's Note: The `ProviderFactory` must replace this hardcoded line to properly switch between `OptaParser` and `StatsBombParser` based on incoming provider metadata).*
3. **Domain Taxonomy:** The parser relies on `OptaEventFactory`, dynamically translating supplier-specific deep taxonomies, cryptic attributes, and coordinates into ScoutPro’s unified formats mapping directly to the `ScoutProEvent` or `ScoutProMatch` (via `BaseEventInfo` schemas).
4. **Serialization:** Re-serialized using `.model_dump()`, the fully structured dicts are packaged uniformly into an event envelope containing timestamps and the `match_id`.

---

## 3. Kafka Distribution & Downstream Microservices

With the uniform clean topology guaranteed, the `live-ingestion-service` uses `AIOKafkaProducer` to publish the envelope to the central Kafka topic: **`raw.events`**. Downstream bounded contexts employ continuous stream consumption:

### A) Match Service
- Uses `MatchStreamProcessor` consuming `raw.events`.
- **Domain Focus:** Contextual match flow. Uses domain logic to append rolling/tumbling window calculations on the match scale (e.g., Passing Networks, Aggregate Possession Percentages, Game State flags).

### B) Statistics Service
- Uses `StatisticsStreamProcessor` consuming `raw.events`.
- **Domain Focus:** Time-Series Analytics & Persistence. Extracts discrete stats and persists them immediately to **TimescaleDB**. Timescale handles the event-time tracking natively, enabling the front-end to request temporal "Match Timelines" with sub-second accuracy.

### C) ML Service
- Uses `MLFeatureStreamProcessor` consuming `raw.events`.
- **Domain Focus:** Real-time Predictive Modeling. Events are streamed instantly to a `FeatureEngineeringPipeline` which converts spatial and statistical fields into standard matrix tensors (e.g., `pass_tensor`). In Phase 2, this serves directly to PyTorch to dynamically forecast live xG, xA, and pass completion probability immediately upon the action happening on the pitch.

---

## 4. Architect's Summary & Required Re-Factoring

The event-driven pattern serves high scalability beautifully. However, the system requires an immediate technical patch within `live-ingestion-service/ingestion/stream_processor.py`.

*Before launching to production:* The hardcoded `self.parser = OptaParser()` needs to be dynamically invoked using `app.state.ProviderFactory.get_parser(metadata.provider)` to guarantee the ingestion script tests for StatsBomb won't inadvertently route CSV fields into XML/JSON Opta taxonomy validation failure traps.