"""
Data Sync Service

Main entry point for the multi-provider data synchronization service.

This service orchestrates:
- Periodic data synchronization from multiple providers (Opta, StatsBomb, etc.)
- Entity resolution and merging
- Conflict detection and resolution
- Quality enrichment
- Canonical data storage

Usage:
    # Run as FastAPI server (default in Docker)
    uvicorn main:app --host 0.0.0.0 --port 8012

    # Run with default configuration (daemon)
    python main.py

    # Run specific sync job
    python main.py --job opta_teams

    # Run once and exit
    python main.py --once

    # Run in daemon mode
    python main.py --daemon
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import Optional

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from sync import (
    SyncScheduler,
    SyncFrequency,
    create_default_scheduler,
    EventBatchSyncer,
    PlayerSyncer,
    TeamSyncer,
    MatchSyncer,
    EventSyncer,
    list_provider_sync_profiles,
)

# ---------------------------------------------------------------------------
# MongoDB helpers
# ---------------------------------------------------------------------------

_MONGO_URL = os.getenv(
    "MONGODB_URL",
    f"mongodb://{os.getenv('MONGODB_HOST', 'mongo')}:"
    f"{os.getenv('MONGODB_PORT', '27017')}/scoutpro",
)
_MONGO_DB = os.getenv("MONGODB_DATABASE", "scoutpro")

_mongo_client: Optional[AsyncIOMotorClient] = None


def _get_db():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(_MONGO_URL)
    return _mongo_client[_MONGO_DB]


# ---------------------------------------------------------------------------
# Scheduler (lazy singleton)
# ---------------------------------------------------------------------------

_scheduler: Optional[SyncScheduler] = None


def _get_scheduler() -> Optional[SyncScheduler]:
    global _scheduler
    if _scheduler is None:
        try:
            providers = [
                provider.strip()
                for provider in os.getenv('SYNC_PROVIDERS', 'opta').split(',')
                if provider.strip()
            ]
            competitions = [
                competition.strip()
                for competition in os.getenv(
                    'SYNC_COMPETITIONS',
                    os.getenv('OPTA_COMPETITION_ID', '115'),
                ).split(',')
                if competition.strip()
            ]
            _scheduler = create_default_scheduler(
                providers=providers,
                competitions=competitions,
            )
        except Exception as exc:
            print(f"[DataSync] Could not create default scheduler: {exc}")
    return _scheduler


# ---------------------------------------------------------------------------
# Entity → MongoDB collection mapping
# ---------------------------------------------------------------------------

_ENTITY_COLLECTIONS = {
    "players": "players",
    "teams": "teams",
    "matches": "matches",
    "events": "events",
}

_ENTITY_SYNCERS = {
    "players": PlayerSyncer,
    "teams": TeamSyncer,
    "matches": MatchSyncer,
    "events": EventBatchSyncer,
}


# ---------------------------------------------------------------------------
# FastAPI lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(application: FastAPI):
    # Allow disabling the scheduler in development to keep the HTTP API up
    # when dependent services (Kafka, Redis, large provider feeds) aren't available.
    start_scheduler = os.getenv('START_SCHEDULER', 'true').lower() in ('1', 'true', 'yes')
    scheduler = _get_scheduler() if start_scheduler else None
    bg_task = None
    if scheduler:
        # Run the scheduler loop in the background so the HTTP server stays up.
        # Jobs fire at their configured intervals (Opta events every 15 min,
        # StatsBomb events every hour, players/teams/matches daily).
        bg_task = asyncio.create_task(scheduler.start())
    yield
    # Graceful shutdown: stop the scheduler loop then cancel the task.
    if scheduler:
        scheduler.stop()
    if bg_task:
        bg_task.cancel()
        try:
            await bg_task
        except asyncio.CancelledError:
            pass
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Data Sync Service",
    description="ScoutPro multi-provider data synchronization service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://api-gateway:3001,http://localhost:3001,http://localhost:5173,http://localhost:5174",
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "data-sync-service", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# GET /api/v2/sync/status
# ---------------------------------------------------------------------------

@app.get("/api/v2/sync/status")
async def sync_status():
    """Return scheduler status, last run times per job, and DB record counts."""
    try:
        db = _get_db()
        scheduler = _get_scheduler()

        # Collect job info from scheduler
        jobs_info = []
        if scheduler:
            for job in scheduler.jobs:
                last_result = None
                if job.last_result:
                    last_result = {
                        "status": job.last_result.status.value,
                        "entities_fetched": job.last_result.entities_fetched,
                        "entities_created": job.last_result.entities_created,
                        "entities_updated": job.last_result.entities_updated,
                        "errors": job.last_result.errors[:5],
                    }
                jobs_info.append({
                    "name": job.name,
                    "provider": job.provider,
                    "frequency": job.frequency.value,
                    "enabled": job.enabled,
                    "last_run": job.last_run.isoformat() if job.last_run else None,
                    "run_count": job.run_count,
                    "last_result": last_result,
                })

        # Collect record counts from MongoDB
        counts = {}
        for entity, collection in _ENTITY_COLLECTIONS.items():
            try:
                counts[entity] = await db[collection].count_documents({})
            except Exception:
                counts[entity] = -1

        return {
            "scheduler_running": scheduler.running if scheduler else False,
            "total_jobs": len(scheduler.jobs) if scheduler else 0,
            "enabled_jobs": sum(1 for j in scheduler.jobs if j.enabled) if scheduler else 0,
            "jobs": jobs_info,
            "provider_profiles": list_provider_sync_profiles(
                sorted({job.provider for job in scheduler.jobs}) if scheduler else None
            ),
            "db_counts": counts,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/sync/provider-profiles")
async def provider_profiles():
    scheduler = _get_scheduler()
    providers = sorted({job.provider for job in scheduler.jobs}) if scheduler else None
    return {
        "profiles": list_provider_sync_profiles(providers),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# POST /api/v2/sync/trigger/{entity}
# ---------------------------------------------------------------------------

@app.post("/api/v2/sync/trigger/{entity}")
async def trigger_sync(
    entity: str,
    provider: str = "statsbomb",
    competition_id: Optional[str] = None,
    season_id: Optional[str] = None,
    max_matches: Optional[int] = None,
    lookback_days: Optional[int] = None,
):
    """
    Manually trigger a sync for 'players', 'teams', 'matches', or 'events'.

    Tries to run the appropriate syncer; on failure falls back to counting
    existing MongoDB records. Stores the outcome in the sync_history collection.
    """
    if entity not in _ENTITY_COLLECTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown entity '{entity}'. Valid: {list(_ENTITY_COLLECTIONS.keys())}",
        )

    db = _get_db()
    started_at = datetime.now(timezone.utc)
    records_synced = 0
    status = "completed"
    errors = []

    try:
        syncer_class = _ENTITY_SYNCERS[entity]
        sync_config = {
            key: value
            for key, value in {
                'competition_id': competition_id,
                'season_id': season_id,
                'max_matches': max_matches,
                'lookback_days': lookback_days,
                'online': provider in ('opta', 'statsbomb'),
            }.items()
            if value is not None
        }
        syncer = syncer_class(provider=provider, config=sync_config)
        result = await syncer.sync(**sync_config)
        records_synced = result.entities_fetched
        if result.errors:
            errors = result.errors[:10]
            status = "partial" if records_synced > 0 else "failed"
    except Exception as syncer_err:
        # Graceful fallback: count what's already in the DB
        errors.append(f"Syncer error: {syncer_err}")
        try:
            collection = _ENTITY_COLLECTIONS[entity]
            records_synced = await db[collection].count_documents({})
            status = "reported"
        except Exception as db_err:
            errors.append(f"DB count error: {db_err}")
            status = "failed"

    completed_at = datetime.now(timezone.utc)

    history_entry = {
        "entity": entity,
        "provider": provider,
        "started_at": started_at,
        "completed_at": completed_at,
        "records_synced": records_synced,
        "status": status,
        "errors": errors,
    }

    try:
        await db["sync_history"].insert_one(history_entry)
    except Exception as hist_err:
        errors.append(f"sync_history write error: {hist_err}")

    history_entry.pop("_id", None)
    # Convert datetimes for JSON serialisation
    history_entry["started_at"] = started_at.isoformat()
    history_entry["completed_at"] = completed_at.isoformat()

    return history_entry


# ---------------------------------------------------------------------------
# GET /api/v2/sync/history
# ---------------------------------------------------------------------------

@app.get("/api/v2/sync/history")
async def sync_history():
    """Return the last 20 sync results from the sync_history collection."""
    try:
        db = _get_db()
        cursor = (
            db["sync_history"]
            .find({}, {"_id": 0})
            .sort("started_at", -1)
            .limit(20)
        )
        records = await cursor.to_list(length=20)
        # Serialise datetime objects
        for rec in records:
            for key in ("started_at", "completed_at"):
                if key in rec and hasattr(rec[key], "isoformat"):
                    rec[key] = rec[key].isoformat()
        return {"history": records, "total": len(records)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




async def run_once(scheduler: SyncScheduler):
    """
    Run all sync jobs once and exit

    Args:
        scheduler: Configured sync scheduler
    """
    print("\n=== Data Sync Service (Run Once Mode) ===\n")

    await scheduler.run_all_jobs()

    print("\n=== Sync completed ===")
    status = scheduler.get_status()

    print(f"\nSummary:")
    print(f"  Total jobs: {status['total_jobs']}")
    print(f"  Enabled jobs: {status['enabled_jobs']}")

    # Print job results
    for job in status['jobs']:
        if job['last_result']:
            result = job['last_result']
            print(f"\n  {job['name']}:")
            print(f"    Status: {result['status']}")
            print(f"    Fetched: {result['entities_fetched']}")
            print(f"    Created: {result['entities_created']}")
            print(f"    Updated: {result['entities_updated']}")
            if result['errors']:
                print(f"    Errors: {len(result['errors'])}")


async def run_daemon(scheduler: SyncScheduler):
    """
    Run scheduler in daemon mode (continuous)

    Args:
        scheduler: Configured sync scheduler
    """
    print("\n=== Data Sync Service (Daemon Mode) ===\n")

    try:
        await scheduler.start()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        scheduler.stop()


async def run_single_job(job_name: str, config: dict):
    """
    Run a single sync job

    Args:
        job_name: Job name (e.g., 'opta_teams', 'statsbomb_matches')
        config: Job configuration
    """
    print(f"\n=== Running single job: {job_name} ===\n")

    # Parse job name
    parts = job_name.split('_')
    if len(parts) < 2:
        print(f"Error: Invalid job name '{job_name}'")
        print("Format: <provider>_<entity_type> (e.g., opta_teams)")
        return

    provider = parts[0]
    entity_type = parts[1]

    # Create syncer based on entity type
    syncer_map = {
        'players': PlayerSyncer,
        'teams': TeamSyncer,
        'matches': MatchSyncer,
        'events': EventSyncer
    }

    syncer_class = syncer_map.get(entity_type)

    if not syncer_class:
        print(f"Error: Unknown entity type '{entity_type}'")
        print(f"Available: {list(syncer_map.keys())}")
        return

    # Create and run syncer
    syncer = syncer_class(provider=provider, config=config)
    result = await syncer.sync(**config)

    # Print result
    print(f"\n=== Sync completed ===")
    print(f"  Status: {result.status.value}")
    print(f"  Fetched: {result.entities_fetched}")
    print(f"  Created: {result.entities_created}")
    print(f"  Updated: {result.entities_updated}")
    print(f"  Merged: {result.entities_merged}")
    print(f"  Duration: {result.duration_seconds:.2f}s")

    if result.errors:
        print(f"  Errors: {len(result.errors)}")
        for error in result.errors[:5]:  # Show first 5 errors
            print(f"    • {error}")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Data Sync Service')

    parser.add_argument(
        '--once',
        action='store_true',
        help='Run all jobs once and exit'
    )

    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run in daemon mode (continuous)'
    )

    parser.add_argument(
        '--job',
        type=str,
        help='Run a single job (format: provider_entity, e.g., opta_teams)'
    )

    parser.add_argument(
        '--provider',
        type=str,
        default='opta',
        help='Provider name (default: opta)'
    )

    parser.add_argument(
        '--competition',
        type=str,
        default=os.getenv('COMPETITION_ID', os.getenv('OPTA_COMPETITION_ID', '115')),
        help='Competition ID (default: from COMPETITION_ID env var or 115)'
    )

    parser.add_argument(
        '--season',
        type=str,
        default=os.getenv('SEASON_ID', os.getenv('OPTA_SEASON_ID', '2019')),
        help='Season ID (default: from SEASON_ID env var or 2019)'
    )

    parser.add_argument(
        '--match',
        type=str,
        help='Match ID (for event sync)'
    )

    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_args()

    db_host = os.getenv('MONGODB_HOST', 'mongo')
    db_port = int(os.getenv('MONGODB_PORT', '27017'))
    db_name = os.getenv('MONGODB_DATABASE', 'scoutpro')

    # Build config
    config = {
        'competition_id': args.competition,
        'season_id': args.season,
        'db_name': db_name,
        'db_host': db_host,
        'db_port': db_port
    }

    if args.match:
        config['match_id'] = args.match

    # Single job mode
    if args.job:
        await run_single_job(args.job, config)
        return

    # Create scheduler
    providers = [args.provider]
    competitions = [args.competition]

    scheduler = create_default_scheduler(
        providers=providers,
        competitions=competitions
    )

    # Run once mode
    if args.once:
        await run_once(scheduler)
        return

    # Daemon mode (default)
    await run_daemon(scheduler)


if __name__ == '__main__':
    asyncio.run(main())
