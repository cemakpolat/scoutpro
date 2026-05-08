# Implementation Todo

Updated: 2026-05-06

## Verified Baseline

- [x] Opta ingestion reaches live-ingestion, Kafka, match-service, and API gateway.
- [x] Match `1080974` is reachable through match-service and the gateway.
- [x] Full F24 event payload now survives Opta parsing and persistence.

## Active Workstreams

- [x] Create a repo-visible tracker for step-by-step implementation.
- [x] Expose statistics-service through the API gateway for frontend consumption.
- [x] Align frontend API defaults with the gateway routes actually served by the backend.
- [x] Validate frontend-to-gateway retrieval from both API and frontend perspectives.
- [x] Materialize Opta F40/F9 metadata into canonical player and team read models.
- [x] Extend the canonical platform model beyond basic player/team/match/event entities.
- [x] Add provider mapping for Opta, StatsBomb, and future providers.
- [x] Route StatsBomb ingestion through the same canonical read-model pipeline as Opta.
- [x] Replace placeholder analytics/search contracts with fully backed read models.

## ML Consumption Surfaces

- [x] Add a user-facing Model Center page so trained models can be used outside the ML Laboratory.
- [x] Expose interactive prediction and similarity tools through a visible frontend navigation entry.
- [x] Expose background ML task submission and result monitoring through a visible frontend navigation entry.
- [x] Add a first team assessment surface in Model Center using live team stats, insights, rankings, and comparisons.
- [x] Expand team assessment with forecasts, risk flags, and deeper drill-downs.
- [x] Add a first match prediction surface in Model Center with user-entered scenario inputs.
- [x] Add a first clustering explorer in Model Center using live cluster metadata and on-demand cluster assignment.
- [x] Add true sequence-window and lagged-history lens filters so single events, possession windows, and past-event views can be compared directly.
- [x] Add saved feature-lens presets for recurring analytical slices such as shot quality, buildup passing, and fatigue versus workload.
- [x] Reuse the feature lens inside Model Center so event- and parameter-slice exploration is not limited to ML Laboratory.
- [x] Embed the shared feature lens inside Scouting Dashboard so scouting decisions can use the same event and parameter slices without leaving the shortlist flow.
- [x] Add drill-down links from ML Laboratory experiments into user-facing prediction and assessment surfaces.
- [x] Add prediction history and saved runs for user-triggered interactive predictions.
- [x] Add initial contextual entry points from Scouting and Analytics into the Model Center.
- [x] Add direct model entry actions from player and match detail views into Model Center tabs.
- [x] Expand contextual "Use This Model" actions with deeper prefilled workflows inside player, team, and match detail views.

## Current Slice

- [x] Add `/api/statistics` gateway routes.
- [x] Fix frontend API base URL and health endpoint defaults.
- [x] Fix frontend search/export request contracts.
- [x] Rebuild and verify frontend and gateway contracts.
- [x] Materialize Opta F40/F9 player and team metadata into Mongo-backed read models.
- [x] Expose `/api/teams/:id/squad` through the API gateway.
- [x] Fix match-service route ordering so `/api/v2/matches/live` and `/api/v2/matches/date-range` resolve natively instead of falling through `/{match_id}`.
- [x] Restore the gateway live-match proxy to the native match-service `/api/v2/matches/live` endpoint.
- [x] Stabilize backend-driven frontend flows for Report Builder, Admin Console, and Performance Tracker.
- [x] Add scripted Playwright browser regressions for report, admin, and performance flows.

## Verified Contract Checks

- [x] API perspective: `/api/matches/1080974`, `/api/statistics/rankings/teams`, and `/health` return successfully through the gateway.
- [x] Frontend perspective: Vite dev server proxies `/api` and `/health` to the gateway, and browser-side fetches succeed from `http://localhost:5173`.
- [x] Frontend hydration perspective: browser-side fetches for `/api/players`, `/api/teams`, and `/api/notifications` return successfully for DataContext initialization.
- [x] Read-model perspective: Opta F40/F9 ingestion now populates 39 players and 2 teams for the sample match path, and those entities are reachable through player-service, team-service, the gateway, and browser-origin `/api` fetches.
- [x] Match routing perspective: match-service route tests confirm `/api/v2/matches/live`, `/api/v2/matches/date-range`, and `/{match_id}` resolve to the correct handlers.
- [x] Browser regression perspective: Playwright covers direct report export, queued report cleanup, admin snapshot sections, and live Performance Tracker rendering.

## Phase 2: Batch Services & Historical Data Management (Foundation)

### Backend Tasks

- [x] Create `batch-data-manager` microservice to orchestrate historical data ingestion pipelines
- [x] Implement idempotent upsert logic in data-sync-service for safe re-import of historical datasets
- [x] Design dual-stream Kafka topology: fast in-memory topics for live data, durable queues for batch historical imports
- [x] Add provider selection parameter to data ingestion contracts (source: "opta" | "statsbomb" | "custom")
- [x] Implement data-freshness metadata on all canonical entities (live, verified, historical, stale)
- [x] Create task-worker-service job queue for async batch import operations with progress tracking
- [x] Add `/api/v2/batch-jobs` endpoints (now in `batch-data-manager`): POST (trigger), GET (list), GET /:id (status & progress)
- [x] Implement idempotency tokens to prevent duplicate batch job submissions
- [x] Add database indexes on (match_id, provider, data_freshness) for efficient historical querying
- [x] Create admin API contracts for provider credential management and batch scheduling

### Frontend Tasks

- [x] Build Data Ingestion Dashboard page with provider selection dropdowns (Opta, StatsBomb, custom)
- [x] Design batch job submission form: select provider, date range, data type (matches, events, metadata)
- [x] Implement real-time batch job monitoring with WebSocket subscriptions to task-worker-service progress
- [x] Add toast notifications for batch job events: started, progress updates, completed, failed
- [x] Create data freshness indicator component (visual tags: [LIVE], [VERIFIED], [HISTORICAL])
- [x] Display active and completed batch jobs in a sortable history table
- [x] Add "Refresh Data" action on match detail pages with provider selection modal
- [x] Integrate data-freshness flags into all player/team/match list views for transparency
- [x] Implement error handling UI for failed batch imports with retry capability

## Phase 3: Player Trajectory & Development Forecasting

### Backend Tasks

- [x] Extend `ml-service` with player trajectory model that clusters players across consecutive seasons
- [x] Create time-series aggregation pipeline to compute player metrics snapshots per month/season
- [x] Add API endpoint `/api/v2/players/:id/trajectory` returning cluster evolution + baseline comparisons
- [x] Implement Markov-chain or regression model to forecast player's likely cluster 1-2 seasons forward
- [x] Add provider filtering to trajectory queries (show only Opta data, only StatsBomb, or cross-provider consensus)
- [x] Create caching layer for trajectory pre-computation to avoid ML re-runs on every request

### Frontend Tasks

- [x] Build Player Trajectory UI in Model Center showing cluster history across seasons (visual timeline)
- [x] Add comparable player baseline overlay to show how this player's trajectory compares to peers
- [x] Design trajectory forecast visualization (cone chart showing confidence bands for next 1-2 seasons)
- [x] Implement provider filter dropdown in trajectory view (filter by data source)
- [x] Add drill-down from trajectory forecast into the similar-player clustering explorer
- [x] Create exportable trajectory reports for scouting decision documentation

## Phase 4: Tactical Fingerprinting (Automated Formation Inference)

### Backend Tasks

- [ ] Extend `analytics-service` with formation inference ML model (k-means on normalized touch locations)
- [ ] Segment match events into 15-minute windows and compute average player touch heatmaps per window
- [ ] Create API endpoint `/api/v2/matches/:id/formations` returning inferred formations per window + confidence
- [ ] Implement provider-aware event preprocessing (standardize Opta F24 and StatsBomb event location coordinates)
- [ ] Add formation tagging to `match-service` match metadata (detected vs reported formations)
- [ ] Cache formation inference results per match to avoid repeated ML computation

### Frontend Tasks

- [ ] Build tactical fingerprinting visualization in match detail views (timeline of formation changes)
- [ ] Display both provider-reported formation (F9 data) and ML-inferred formation side-by-side for comparison
- [ ] Add interactive heatmap showing player touch density per 15-minute window
- [ ] Implement formation timeline scrubber to jump to specific windows in match video
- [ ] Add provider data quality indicator (e.g., "Formation inferred from Opta events" vs "StatsBomb reported")
- [ ] Create tactical comparison: this match's formations vs team's season average formations

## Phase 5: Video-to-Event Synchronization (P2)

### Backend Tasks

- [ ] Extend `video-service` with event timestamp mapping to video files
- [ ] Create synchronization calibration: link match start time in video to first canonical event timestamp
- [ ] Add API contract `/api/v2/matches/:id/video-map` returning event→video offset mappings

### Frontend Tasks

- [ ] Integrate video player with canonical event timeline (click event → jump to video timestamp)
- [ ] Show relevant event context window (10-second clip around each event) directly from frontend

## Phase 6: Contextual Transfer/Market Value Estimator (P2)

### Backend Tasks

- [ ] Build valuation model in `ml-service` integrating performance trends, cluster position, age, contract
- [ ] Create API endpoint `/api/v2/players/:id/valuation` returning estimated value range + confidence

### Frontend Tasks

- [ ] Add valuation card to player detail pages showing estimated market value band
- [ ] Integrate into scouting shortlist views for ROI assessment