# Providers

Provider servers live at the workspace root because they represent external
data boundaries, not ScoutPro business-domain microservices.

- `data-provider-mock/` exposes Opta- and StatsBomb-compatible HTTP routes for offline development.
- Production provider servers can keep the same HTTP contract while using real vendor credentials upstream.
