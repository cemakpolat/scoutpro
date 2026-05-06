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
- [ ] Extend the canonical platform model beyond basic player/team/match/event entities.
- [ ] Add provider mapping for Opta, StatsBomb, and future providers.
- [ ] Route StatsBomb ingestion through the same canonical read-model pipeline as Opta.
- [ ] Replace placeholder analytics/search contracts with fully backed read models.

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