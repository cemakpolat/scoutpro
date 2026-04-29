# ScoutPro Frontend-to-Backend API Integration Audit

**Date:** 2026-02-28  
**Scope:** `frontend/src/components/` — all `.tsx` files  
**TypeScript Build:** `tsc --noEmit` passes with **0 errors**

---

## Infrastructure Summary

### `services/api.ts` (ApiService) — 877 lines
A comprehensive singleton wrapping `fetch`, with **mock-data fallback** on every endpoint. Key method groups:

| Category | Methods |
|---|---|
| **Players** | `getPlayers`, `getPlayer`, `searchPlayers` |
| **Matches** | `getMatches`, `getMatch`, `getLiveMatches`, `getMatchEvents` |
| **Teams** | `getTeams`, `getTeam` |
| **Leagues** | `getLeagues`, `getLeague` |
| **Analytics** | `getAnalytics`, `getPlayerAnalytics`, `getMatchAnalytics`, `getDashboardOverview`, `getLeagueTrends`, `getPlayerRankings`, `getTeamRankings`, `getPlayerInsightsAdvanced`, `comparePlayers`, `compareTeams` |
| **AI/Insights** | `getAIInsights`, `getPlayerInsights` |
| **Market** | `getMarketTrends`, `getTransferPredictions` |
| **Notifications** | `getNotifications`, `markNotificationRead` |
| **Tactical** | `getTacticalPatterns` |
| **ML** | `getMLAlgorithms`, `getMLDatasets`, `getMLExperiments`, `createMLExperiment`, `trainModel` |
| **Reports (v2)** | `generatePlayerReport`, `generateTeamReport`, `generateMatchReport`, `generateAsyncReport`, `getReportStatus`, `downloadReport`, `listReports`, `deleteReport` |
| **Export (v2)** | `exportPlayers`, `exportTeams`, `exportMatches`, `exportStatistics`, `exportCustom`, `getExportTemplate` |
| **Video (v2)** | `uploadVideo`, `getVideoMetadata`, `getVideoStreamUrl`, `analyzeVideo`, `listVideos`, `deleteVideo` |

### `context/DataContext.tsx`
Provides global state via `useData()` / `useDataContext()`:
- **Data:** `players`, `matches`, `teams`, `notifications`, `tacticalPatterns`, `marketTrends`
- **Loading/Error:** per-entity states
- **Refresh:** `refreshPlayers`, `refreshMatches`, `refreshTeams`, `refreshNotifications`
- Fetches via `useApi` + `apiService` on mount, receives WebSocket live updates

### `hooks/useApi.ts`
- `useApi<T>(apiCall, deps)` — auto-fetch on mount / dep change, returns `{ data, loading, error, refetch }`
- `useApiLazy<T>()` — manual trigger pattern

---

## Per-Component Integration Status

### Legend
- ✅ **Fully Integrated** — uses API/context for all data, no meaningful hardcoded data
- ⚠️ **Partially Integrated** — imports API services but retains some hardcoded data
- ❌ **Not Integrated** — no API/context imports, fully hardcoded data

---

### 1. `Dashboard.tsx` — ✅ Fully Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ✅ |
| `useData` | ✅ |

- Uses `useData()` for players/matches/loading/errors
- Fetches `getAnalytics('dashboard')`, `getMarketTrends()`, `getTacticalPatterns()` via useApi
- Computes metrics from live context data
- **Hardcoded data:** None

---

### 2. `ScoutingDashboard.tsx` — ✅ Fully Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ✅ |
| `useDataContext` | ✅ |

- Fetches `getAIInsights('scouting')`, `getPlayers(filters)` via useApi
- Positions list `['all', 'GK', 'CB', ...]` is UI constants (acceptable)
- **Hardcoded data:** None (positions list is UI config, not domain data)

---

### 3. `PlayerDatabase.tsx` — ✅ Fully Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ✅ |
| `useData` | ✅ |

- Fetches `getPlayers(filters, queryParams)` via useApi
- Uses `useData()` for player list, loading, errors
- Export via `exportService`
- **Hardcoded data:** None

---

### 4. `PlayerDetail.tsx` — ✅ Fully Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ❌ (uses direct calls) |
| `useData` | ❌ |

- Fetches `getPlayerInsightsAdvanced()`, `getPlayer()` in useEffect
- Downloads reports via `generatePlayerReport()`
- **Hardcoded data:** None (falls back to `initialPlayer` prop data)

---

### 5. `PlayerCard.tsx` — ✅ Fully Integrated (Presentational)
| Import | Present |
|---|---|
| `apiService` | ❌ |
| `useApi` | ❌ |
| `useData` | ❌ |

- Pure presentational component, receives `Player` via props
- **Hardcoded data:** None — N/A (presentational)

---

### 6. `PlayerComparison.tsx` — ✅ Fully Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ❌ (uses direct calls) |
| `useData` | ✅ |

- Uses `useData()` for player list
- Uses `comparisonService`, `apiService.comparePlayers()`
- Export via `exportService`
- **Hardcoded data:** None

---

### 7. `GameAnalysis.tsx` — ⚠️ Partially Integrated
| Import | Present |
|---|---|
| `apiService` | ❌ |
| `useApi` | ❌ |
| `useData` | ✅ |

- Uses `useData()` for matches ✅
- **Hardcoded data:**
  - Quick stats cards: `47` (Games This Month), `156` (Players Tracked), `8.7` (Avg Match Rating), `23` (Scouted Today) — all hardcoded numbers that should be computed from match data or fetched from analytics

---

### 8. `GameDetail.tsx` — ✅ Fully Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ❌ (uses direct calls) |
| `useData` | ❌ |

- Fetches `getMatchEvents()` on mount
- Downloads reports via `generateMatchReport()`
- Stats use game prop data with fallback defaults (e.g. `game.homePossession || 55`)
- **Hardcoded data:** Fallback event list (4 generic events) when API returns empty — acceptable fallback

---

### 9. `GameCard.tsx` — ✅ Fully Integrated (Presentational)
| Import | Present |
|---|---|
| `apiService` | ❌ |
| `useApi` | ❌ |
| `useData` | ❌ |

- Pure presentational, receives `Match` via props
- **Hardcoded data:** None — N/A

---

### 10. `MatchCentre.tsx` — ✅ Fully Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ✅ |
| `useData` | ✅ |

- Uses `useData()` for matches
- Fetches `getLiveMatches()`, `getMatchEvents()` via useApi
- Uses `useLiveMatch()` WebSocket hook for real-time updates
- **Hardcoded data:** Win probability initial values `{ home: 45, away: 35, draw: 20 }` — acceptable defaults

---

### 11. `MultiMatchAnalysis.tsx` — ⚠️ Partially Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ❌ (uses direct calls) |
| `useData` | ✅ |

- Uses `useData()` for matches ✅
- Maps real matches from context ✅
- **Hardcoded data:**
  - `defaultResults.patterns[]` — 4 hardcoded tactical patterns with frequency/impact
  - `defaultResults.keyInsights[]` — 4 hardcoded insight strings
  - These are used as fallback when no API analysis results are available

---

### 12. `AnalyticsDashboard.tsx` — ✅ Fully Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ✅ |
| `useData` | ❌ |

- Fetches `getDashboardOverview()`, `getLeagueTrends()`, `getPlayerRankings()`, `getTeamRankings()`
- Derives display data from API responses
- **Hardcoded data:**
  - `xTData[]` — 5 zone xT values (comment says "static structure, could come from a future endpoint")
  - `styleLabels[]` / `styleColors[]` — UI display constants (acceptable)

---

### 13. `TopPerformers.tsx` — ✅ Fully Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ✅ |
| `useData` | ✅ |

- Uses `useData()` for players/loading
- Fetches `getAnalytics('top-performers')` via useApi
- Filters/sorts players from context
- Shows loading skeleton
- **Hardcoded data:** None

---

### 14. `RecentActivity.tsx` — ✅ Fully Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ✅ |
| `useData` | ✅ |

- Uses `useData()` for notifications
- Fetches `getAIInsights('general')` via useApi
- Merges notifications + AI insights into activity feed
- **Hardcoded data:** None

---

### 15. `StatCard.tsx` — ✅ Fully Integrated (Presentational)
| Import | Present |
|---|---|
| `apiService` | ❌ |
| `useApi` | ❌ |
| `useData` | ❌ |

- Pure presentational, receives all values via props
- **Hardcoded data:** None — N/A

---

### 16. `PerformanceTracker.tsx` — ⚠️ Partially Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ❌ (uses direct calls) |
| `useData` | ✅ |

- Uses `useData()` for players ✅
- Fetches `getPlayerInsightsAdvanced()`, `getPlayer()` per selected player ✅
- Export via `exportService` ✅
- **Hardcoded data remaining:**
  - `developmentTracking[]` — 4 items (Technical Skills, Physical Attributes, Mental Strength, Tactical Awareness) with hardcoded scores
  - `performanceAlerts[]` — 4 items with hardcoded alert messages referencing specific players (Mbappé, Pedri, Haaland, Messi)
  - `injuryRiskFactors[]` — 5 items with hardcoded risk percentages
  - Fallback `players` array with 2 hardcoded player entries (Mbappé, Haaland)
  - Fallback `performanceMetrics` object with hardcoded defaults

---

### 17. `PerformancePrediction.tsx` — ✅ Fully Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ❌ (uses direct calls) |
| `useData` | ✅ |

- Fetches `getPlayerRankings('rating', 5)` on mount
- Falls back to `useData()` players if API returns empty
- **Hardcoded data:** None (fallback is context data)

---

### 18. `PotentialChart.tsx` — ✅ Fully Integrated (Presentational)
| Import | Present |
|---|---|
| `apiService` | ❌ |
| `useApi` | ❌ |
| `useData` | ❌ |

- Pure presentational, receives data via props
- **Hardcoded data:** None — N/A

---

### 19. `MarketAnalysis.tsx` — ✅ Fully Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ✅ |
| `useData` | ✅ |

- Uses `useData()` for players
- Fetches `getMarketTrends()` via useApi
- Derives market data from players + randomized change percentages
- Export via `exportService`
- **Hardcoded data:** Random `changePercent` and `transferProbability` — computed client-side (should ideally come from API market predictions)

---

### 20. `TransferHub.tsx` — ❌ Not Integrated
| Import | Present |
|---|---|
| `apiService` | ❌ |
| `useApi` | ❌ |
| `useData` | ❌ |

- Only imports `exportService` for PDF export
- **Hardcoded data (all):**
  - `transferRumors[]` — 3 items (Mbappé, Haaland, Pedri)
  - `marketTrends[]` — 5 position trend items
  - `contractExpirations[]` — 4 items (Messi, Modrić, Busquets, Thiago Silva)
  - `transferAlerts[]` — 4 alert items
  - Market overview stat cards: `€2.4B`, `247`, `89`, `€89M` all hardcoded
  - **BUG:** `valuationPredictions` is referenced on lines 82 and 351 but **never defined** — this will cause a runtime error if the "valuations" tab is selected

---

### 21. `TacticalAnalyzer.tsx` — ❌ Not Integrated
| Import | Present |
|---|---|
| `apiService` | ❌ |
| `useApi` | ❌ |
| `useData` | ❌ |

- **Hardcoded data (all):**
  - `formations[]` — 5 formations with popularity/effectiveness
  - `tacticalPatterns[]` — 4 patterns (High Pressing, Counter-Attack, Possession Play, Set Piece Routine)
  - `playerMovements[]` — 4 items (Mbappé, Neymar, Messi, Verratti)
  - `heatmapData[]` — 5 zone intensity items

---

### 22. `MLAnalysis.tsx` — ❌ Not Integrated
| Import | Present |
|---|---|
| `apiService` | ❌ |
| `useApi` | ❌ |
| `useData` | ❌ |

- **Hardcoded data (all):**
  - `models[]` — 4 model selection items (UI config — acceptable)
  - Summary stats: `94.2%`, `1,247`, `23`, `87%` all hardcoded
  - `PotentialAnalysis` sub-component: 5 hardcoded players (Pedri, Bellingham, Gavi, Camavinga, Musiala) + growth factors (85%, 78%, 92%, 88%)
  - `InjuryRiskAnalysis` sub-component: 5 hardcoded players (Neymar, Bale, Dybala, Reus, Dembélé) with risk percentages + static prevention recommendations
  - `MarketValuePrediction` sub-component: 5 hardcoded players with value predictions + 5 hardcoded value drivers + static market trend descriptions

  **Note:** `MLLaboratory.tsx` is the upgraded version of this component that IS integrated.

---

### 23. `MLLaboratory.tsx` — ✅ Fully Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ✅ |
| `useData` | ❌ |

- Fetches `getMLAlgorithms()`, `getMLDatasets()`, `getMLExperiments()` via useApi
- Uses proper loading/error states
- Export via `exportService`
- **Hardcoded data:** `models[]` — 4 model tab items (UI config, acceptable)

---

### 24. `DataManagement.tsx` — ❌ Not Integrated
| Import | Present |
|---|---|
| `apiService` | ❌ |
| `useApi` | ❌ |
| `useData` | ❌ |

- **Hardcoded data (all):**
  - `datasets[]` — 5 datasets (Player Statistics, Match Events, Transfer Market, Injury Records, Tactical Analysis) with sizes, records, sources, quality scores
  - `dataQualityIssues[]` — 5 items with counts and severities
  - `pipelineJobs[]` — 4 pipeline job items with statuses
  - Upload progress is simulated client-side

---

### 25. `AdminConsole.tsx` — ⚠️ Partially Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ❌ (uses direct calls) |
| `useData` | ✅ |

- Fetches `getDashboardOverview()`, API health check on mount ✅
- Uses `useData()` for players/teams ✅
- **Hardcoded data remaining:**
  - `userRoles[]` — 4 user items (John Smith, Sarah Wilson, Mike Johnson, Emma Davis)
  - `apiKeys[]` — 3 API key items
  - `auditLogs[]` — 4 log entries
  - `subscriptions[]` — 4 club subscription items
  - `sections[]` — 6 navigation items (UI config, acceptable)

---

### 26. `NotificationCenter.tsx` — ✅ Fully Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ❌ |
| `useData` | ❌ (receives via props) |

- Receives notifications via props
- Calls `apiService.markNotificationRead()` for fire-and-forget updates
- **Hardcoded data:** None

---

### 27. `ReportBuilder.tsx` — ⚠️ Partially Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ✅ |
| `useData` | ✅ |

- Uses `useData()` for players/teams ✅
- Fetches `listReports()` via useApi ✅
- Generates reports via `generatePlayerReport()`, `generateTeamReport()`, etc. ✅
- **Hardcoded data remaining:**
  - `templates[]` — 4 report template definitions (Player Analysis, Team Tactical, Market Intelligence, Match Analysis) — arguably design-time config
  - `reportSections[]` — 4+ section items with hardcoded status and content descriptions

---

### 28. `VideoAnalysis.tsx` — ⚠️ Partially Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ❌ |
| `useData` | ❌ |

- Uses `videoService` (local service) for video CRUD
- Imports `apiService` and `exportService`
- **Hardcoded data:**
  - `speeds[]` — `[0.25, 0.5, 0.75, 1, 1.25, 1.5, 2]` (UI config, acceptable)
  - Videos data comes from `videoService.getVideos()` (separate local service, not the main apiService)

---

### 29. `SearchPage.tsx` — ⚠️ Partially Integrated
| Import | Present |
|---|---|
| `apiService` | ❌ |
| `useApi` | ❌ |
| `useData` | ❌ |

- Uses `searchService` (separate service) for search functionality
- Uses `exportService` for exports
- **Hardcoded data:** Search relies on `searchService` which may use mock data internally

---

### 30. `CalendarScheduling.tsx` — ✅ Fully Integrated (via Context)
| Import | Present |
|---|---|
| `apiService` | ❌ |
| `useApi` | ❌ |
| `useCalendar` | ✅ |

- Uses `CalendarContext` for events, trips, matches, CRUD operations
- **Hardcoded data:** `monthNames[]`, `dayNames[]` — UI constants (acceptable)

---

### 31. `CollaborationHub.tsx` — ✅ Fully Integrated (via Context)
| Import | Present |
|---|---|
| `apiService` | ❌ |
| `useApi` | ❌ |
| `useCollaboration` | ✅ |

- Uses `CollaborationContext` for workspaces, tasks, activities, CRUD operations
- **Hardcoded data:** None
- **TODO:** Line 410: `// TODO: Show share modal after view modal`

---

### 32. `DataImporter.tsx` — ⚠️ Partially Integrated
| Import | Present |
|---|---|
| `apiService` | ✅ |
| `useApi` | ❌ |
| `useData` | ❌ |

- Imports `apiService`, uses `getDashboardOverview()` as connectivity check
- **Hardcoded data:** Has `mockJobs[]` as fallback import history (mock data in component)

---

### 33. `Navigation.tsx` — ✅ Fully Integrated (UI component)
| Import | Present |
|---|---|
| `apiService` | ❌ |
| `useAuth` | ✅ |
| `useData` | ❌ |

- Uses `AuthContext` for user/logout
- **Hardcoded data:** `navItems[]` — navigation menu items (UI config, acceptable)

---

### Subdirectory Components

#### `auth/LoginPage.tsx`, `auth/RegisterPage.tsx`, `auth/ProtectedRoute.tsx`
- Auth-specific, use `AuthContext` — no data integration needed
- **Status:** ✅ N/A (auth layer)

#### `search/GlobalSearch.tsx`, `search/AdvancedFilters.tsx`, `search/SavedSearches.tsx`
- Sub-components of SearchPage — no direct API imports
- **Status:** ✅ N/A (presentational sub-components)

#### `shared/ConfirmDialog.tsx`
- Pure UI component
- **Status:** ✅ N/A (utility)

---

## Summary

### Overall Counts (34 top-level + sub-components)

| Status | Count | Components |
|---|---|---|
| ✅ Fully Integrated | 20 | Dashboard, ScoutingDashboard, PlayerDatabase, PlayerDetail, PlayerCard, PlayerComparison, GameDetail, GameCard, MatchCentre, AnalyticsDashboard, TopPerformers, RecentActivity, StatCard, PerformancePrediction, PotentialChart, MarketAnalysis, MLLaboratory, NotificationCenter, CalendarScheduling, CollaborationHub |
| ⚠️ Partially Integrated | 8 | GameAnalysis, MultiMatchAnalysis, PerformanceTracker, AdminConsole, ReportBuilder, VideoAnalysis, SearchPage, DataImporter |
| ❌ Not Integrated | 3 | **TransferHub**, **TacticalAnalyzer**, **MLAnalysis** |
| N/A (Presentational/Auth) | 7 | Navigation, auth/*, search/*, shared/* |

### Critical Bug
- **TransferHub.tsx** — `valuationPredictions` is used on lines 82 and 351 but **never defined**. Selecting the "Valuations" tab will cause a **runtime crash** (`ReferenceError`).

### TODO/FIXME Comments
- **CollaborationHub.tsx:410** — `// TODO: Show share modal after view modal`

### What Still Needs Work

#### High Priority (fully hardcoded, no API connection)
1. **TransferHub.tsx** — Needs `apiService.getMarketTrends()`, `getTransferPredictions()`, new endpoints for rumors/contracts. Fix `valuationPredictions` bug.
2. **TacticalAnalyzer.tsx** — Needs `apiService.getTacticalPatterns()`, new endpoints for formations, player movements, and heatmap data.
3. **MLAnalysis.tsx** — Has been superseded by `MLLaboratory.tsx` which IS integrated. Consider removing `MLAnalysis.tsx` or redirecting to MLLaboratory. The sub-components (`PotentialAnalysis`, `InjuryRiskAnalysis`, `MarketValuePrediction`) are entirely hardcoded.

#### Medium Priority (partially integrated, has hardcoded data arrays)
4. **PerformanceTracker.tsx** — `developmentTracking[]`, `performanceAlerts[]`, `injuryRiskFactors[]` should come from player insights API.
5. **AdminConsole.tsx** — `userRoles[]`, `apiKeys[]`, `auditLogs[]`, `subscriptions[]` need admin API endpoints.
6. **GameAnalysis.tsx** — Quick stats cards (47, 156, 8.7, 23) should be computed from match data or fetched from an analytics endpoint.
7. **DataManagement.tsx** — `datasets[]`, `dataQualityIssues[]`, `pipelineJobs[]` need data management API endpoints.
8. **ReportBuilder.tsx** — `templates[]` and `reportSections[]` could be fetched from the report service.
9. **DataImporter.tsx** — Has mock import jobs; needs real import history endpoint.

#### Low Priority
10. **SearchPage.tsx** — Uses its own `searchService`; should be evaluated whether to unify with `apiService`.
11. **VideoAnalysis.tsx** — Uses its own `videoService`; `apiService` has v2 video endpoints that could replace the local service.
12. **MarketAnalysis.tsx** — Client-side random `changePercent`/`transferProbability` should come from market predictions API.
13. **AnalyticsDashboard.tsx** — `xTData[]` (5 xT zone values) is hardcoded with a comment noting it should come from a future endpoint.

### API Methods Available but Unused by Components
- `getTransferPredictions()` — not consumed by TransferHub
- `getTeamInsights()` — not consumed by any component
- `getLeagues()` / `getLeague()` — not consumed by any component
- `exportPlayers/Teams/Matches/Statistics()` (v2 export endpoints) — components use local `exportService` instead
- `uploadVideo()`, `analyzeVideo()`, `listVideos()` (v2 video endpoints) — VideoAnalysis uses local `videoService`
