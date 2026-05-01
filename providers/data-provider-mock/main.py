"""
ScoutPro provider server mock.

This server sits outside the ScoutPro microservice boundary and emulates
external Opta and StatsBomb provider contracts using local files from data/.

Opta feed endpoints  : /api/football/f{feed}/{competition_id}/{season_id}[/{match_id}]
StatsBomb endpoints  : /api/statsbomb/events/{match_id}
Admin / discovery    : /api/feeds, /api/health, /docs (Swagger)

Run:
    uvicorn main:app --host 0.0.0.0 --port 7000 --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.opta import router as opta_router
from api.statsbomb import router as statsbomb_router
from api.admin import router as admin_router

app = FastAPI(
    title="ScoutPro Data Provider Mock",
    description=(
        "Local replication of Opta and StatsBomb HTTP APIs backed by files in data/. "
        "Use this in development so ScoutPro services can talk to an external "
        "provider server without real API keys."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(opta_router, prefix="/api/football")
app.include_router(statsbomb_router, prefix="/api/statsbomb")
app.include_router(admin_router, prefix="/api")
