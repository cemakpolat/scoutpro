from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, Optional, List
from datetime import datetime
import uuid
import asyncio
import os
import httpx

app = FastAPI(title="Batch Data Manager API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_SYNC_URL = os.getenv("DATA_SYNC_SERVICE_URL", "http://data-sync-service:8012")
DATA_ROOT_PATTERN = os.getenv("DATA_ROOT_PATTERN", "/data/opta/{year}")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class BatchJobRequest(BaseModel):
    provider: Literal["opta", "statsbomb", "custom"] = Field(description="Data provider source")
    resource_type: Literal["match", "event", "player", "team"] = Field(description="Type of data to import")
    start_date: str = Field(description="Start date for import filtering (YYYY-MM-DD)", examples=["2023-01-01"])
    end_date: str = Field(description="End date for import filtering (YYYY-MM-DD)", examples=["2023-12-31"])
    competition_id: Optional[str] = None
    season_id: Optional[str] = None
    idempotency_token: str = Field(description="Unique token to prevent duplicate runs")


class MultiYearBatchRequest(BaseModel):
    years: List[int] = Field(..., description="Season years to ingest, e.g. [2017, 2018, 2020, 2021]")
    competition_id: int = Field(115, description="Opta competition ID")
    phases: List[str] = Field(
        default=["f1", "f40", "f9", "f24"],
        description="Seeding phases: f1, f40, f9, f24, statsbomb",
    )
    idempotency_token: str = Field(description="Unique token to prevent duplicate runs")


# ---------------------------------------------------------------------------
# In-memory job stores
# ---------------------------------------------------------------------------

jobs_db: Dict[str, Any] = {}      # idempotency_token -> job
jobs_by_id: Dict[str, str] = {}   # job_id -> idempotency_token

multi_year_jobs: Dict[str, Any] = {}  # job_id -> multi-year job state


# ---------------------------------------------------------------------------
# Single-job helpers
# ---------------------------------------------------------------------------

async def _call_data_sync_trigger(
    entity: str,
    provider: str,
    competition_id: Optional[str],
    season_id: Optional[str],
) -> Dict[str, Any]:
    """Forward a sync request to data-sync-service and return the result."""
    params: Dict[str, Any] = {"provider": provider}
    if competition_id:
        params["competition_id"] = competition_id
    if season_id:
        params["season_id"] = season_id

    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            f"{DATA_SYNC_URL}/api/v2/sync/trigger/{entity}",
            params=params,
        )
        resp.raise_for_status()
        return resp.json()


async def run_real_job(idempotency_token: str) -> None:
    """Execute a single-entity batch job by delegating to data-sync-service."""
    await asyncio.sleep(0.5)
    if idempotency_token not in jobs_db:
        return

    job = jobs_db[idempotency_token]
    job["status"] = "in_progress"
    job["started_at"] = datetime.utcnow().isoformat()

    request = job["request"]
    provider = request.get("provider", "opta")
    resource = request.get("resource_type", "match")
    competition_id = request.get("competition_id")
    season_id = request.get("season_id")

    # Map resource_type to entity name expected by data-sync-service
    entity_map = {
        "match": "matches",
        "player": "players",
        "team": "teams",
        "event": "events",
    }
    entity = entity_map.get(resource, "matches")

    job["progress"] = 10
    try:
        result = await _call_data_sync_trigger(entity, provider, competition_id, season_id)
        records = result.get("records_synced", 0)
        sync_status = result.get("status", "completed")

        job["progress"] = 100
        job["status"] = sync_status if sync_status in ("completed", "partial", "failed") else "completed"
        job["records_processed"] = records
        job["records_failed"] = len(result.get("errors", []))
        job["completed_at"] = datetime.utcnow().isoformat()
        job["sync_detail"] = result

    except httpx.HTTPStatusError as exc:
        job["status"] = "failed"
        job["error_message"] = f"data-sync-service HTTP {exc.response.status_code}: {exc.response.text[:200]}"
        job["completed_at"] = datetime.utcnow().isoformat()
    except Exception as exc:
        job["status"] = "failed"
        job["error_message"] = str(exc)
        job["completed_at"] = datetime.utcnow().isoformat()

    job["updated_at"] = datetime.utcnow().isoformat()


# ---------------------------------------------------------------------------
# Multi-year job helper
# ---------------------------------------------------------------------------

async def run_multi_year_job(job_id: str, request_data: Dict[str, Any]) -> None:
    """
    Execute a multi-year batch job by calling data-sync-service
    POST /api/v2/batch/seed-years and polling until completion.
    """
    job = multi_year_jobs[job_id]
    job["status"] = "in_progress"
    job["started_at"] = datetime.utcnow().isoformat()

    payload = {
        "years": request_data["years"],
        "competition_id": request_data["competition_id"],
        "phases": request_data["phases"],
        "data_root_pattern": DATA_ROOT_PATTERN,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{DATA_SYNC_URL}/api/v2/batch/seed-years",
                json=payload,
            )
            resp.raise_for_status()
            seed_response = resp.json()

        upstream_job_id = seed_response.get("job_id")
        job["upstream_job_id"] = upstream_job_id
        job["progress"] = 5
        job["updated_at"] = datetime.utcnow().isoformat()

        # Poll until the upstream job is done
        if upstream_job_id:
            poll_url = f"{DATA_SYNC_URL}/api/v2/batch/seed-years/{upstream_job_id}"
            while True:
                await asyncio.sleep(5)
                async with httpx.AsyncClient(timeout=15.0) as client:
                    poll_resp = await client.get(poll_url)
                    if poll_resp.status_code != 200:
                        break
                    upstream = poll_resp.json()

                job["progress"] = upstream.get("progress", job["progress"])
                job["year_results"] = upstream.get("year_results", [])
                job["updated_at"] = datetime.utcnow().isoformat()

                upstream_status = upstream.get("status", "in_progress")
                if upstream_status in ("completed", "failed", "partial"):
                    job["status"] = upstream_status
                    break

        job["status"] = job.get("status", "completed")
        job["progress"] = 100
        job["completed_at"] = datetime.utcnow().isoformat()

    except httpx.HTTPStatusError as exc:
        job["status"] = "failed"
        job["error_message"] = f"data-sync-service HTTP {exc.response.status_code}: {exc.response.text[:200]}"
        job["completed_at"] = datetime.utcnow().isoformat()
    except Exception as exc:
        job["status"] = "failed"
        job["error_message"] = str(exc)
        job["completed_at"] = datetime.utcnow().isoformat()

    job["updated_at"] = datetime.utcnow().isoformat()


# ---------------------------------------------------------------------------
# Single-entity batch job endpoints
# ---------------------------------------------------------------------------

@app.post("/api/v2/batch-jobs")
async def trigger_batch_job(request: BatchJobRequest):
    if request.idempotency_token in jobs_db:
        existing = jobs_db[request.idempotency_token]
        return {"status": "job_already_exists", "job_id": existing["job_id"], "job": existing}

    job_id = f"bdm-{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow().isoformat()

    job = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "request": request.model_dump(),
        "created_at": now,
        "updated_at": now,
        "started_at": None,
        "completed_at": None,
        "records_processed": None,
        "records_failed": None,
        "error_message": None,
        "retry_of": None,
        "sync_detail": None,
    }

    jobs_db[request.idempotency_token] = job
    jobs_by_id[job_id] = request.idempotency_token

    asyncio.create_task(run_real_job(request.idempotency_token))

    return {"status": "job_created", "job_id": job_id}


@app.get("/api/v2/batch-jobs")
async def list_jobs():
    jobs = list(jobs_db.values())
    jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)
    return {"jobs": jobs, "total": len(jobs)}


@app.get("/api/v2/batch-jobs/{job_id}")
async def get_job_status(job_id: str):
    token = jobs_by_id.get(job_id)
    if not token or token not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job": jobs_db[token]}


@app.post("/api/v2/batch-jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    token = jobs_by_id.get(job_id)
    if not token or token not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs_db[token]
    if job["status"] in ("completed", "failed", "cancelled"):
        raise HTTPException(status_code=409, detail=f"Cannot cancel a job in '{job['status']}' state")

    jobs_db[token]["status"] = "cancelled"
    jobs_db[token]["updated_at"] = datetime.utcnow().isoformat()
    return {"status": "cancelled", "job_id": job_id}


@app.post("/api/v2/batch-jobs/{job_id}/retry")
async def retry_job(job_id: str):
    token = jobs_by_id.get(job_id)
    if not token or token not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs_db[token]
    if job["status"] not in ("failed", "cancelled"):
        raise HTTPException(status_code=409, detail="Can only retry failed or cancelled jobs")

    new_token = f"retry_{uuid.uuid4().hex}"
    new_job_id = f"bdm-{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow().isoformat()

    new_job = {
        "job_id": new_job_id,
        "status": "pending",
        "progress": 0,
        "request": job["request"],
        "created_at": now,
        "updated_at": now,
        "started_at": None,
        "completed_at": None,
        "records_processed": None,
        "records_failed": None,
        "error_message": None,
        "retry_of": job_id,
        "sync_detail": None,
    }

    jobs_db[new_token] = new_job
    jobs_by_id[new_job_id] = new_token
    asyncio.create_task(run_real_job(new_token))

    return {"status": "job_created", "job_id": new_job_id}


# ---------------------------------------------------------------------------
# Multi-year batch endpoints
# ---------------------------------------------------------------------------

@app.post("/api/v2/batch-jobs/multi-year", status_code=202)
async def trigger_multi_year_job(request: MultiYearBatchRequest):
    """
    Trigger ingestion of multiple season years at once.

    Delegates to data-sync-service POST /api/v2/batch/seed-years and polls
    for completion, streaming progress back through this job record.

    Example body:
        {
          "years": [2017, 2018, 2020, 2021],
          "competition_id": 115,
          "phases": ["f1", "f40", "f24"],
          "idempotency_token": "my-unique-run-id"
        }
    """
    if request.idempotency_token in multi_year_jobs:
        existing = multi_year_jobs[request.idempotency_token]
        return {"status": "job_already_exists", "job": existing}

    invalid_phases = set(request.phases) - {"f1", "f40", "f9", "f24", "statsbomb"}
    if invalid_phases:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown phases: {sorted(invalid_phases)}. Valid: f1, f40, f9, f24, statsbomb",
        )

    job_id = f"my-{uuid.uuid4().hex[:10]}"
    now = datetime.utcnow().isoformat()

    job: Dict[str, Any] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "years": request.years,
        "competition_id": request.competition_id,
        "phases": request.phases,
        "year_results": [],
        "upstream_job_id": None,
        "error_message": None,
        "created_at": now,
        "updated_at": now,
        "started_at": None,
        "completed_at": None,
    }

    multi_year_jobs[request.idempotency_token] = job

    asyncio.create_task(
        run_multi_year_job(
            job_id,
            {
                "years": request.years,
                "competition_id": request.competition_id,
                "phases": request.phases,
            },
        )
    )

    return {"status": "job_created", "job_id": job_id, "years": request.years}


@app.get("/api/v2/batch-jobs/multi-year")
async def list_multi_year_jobs():
    """List all multi-year batch jobs."""
    jobs = sorted(multi_year_jobs.values(), key=lambda j: j.get("created_at", ""), reverse=True)
    return {"jobs": jobs, "total": len(jobs)}


@app.get("/api/v2/batch-jobs/multi-year/{job_id}")
async def get_multi_year_job(job_id: str):
    """Get the status of a multi-year batch job by job_id."""
    for job in multi_year_jobs.values():
        if job.get("job_id") == job_id:
            return job
    raise HTTPException(status_code=404, detail=f"Multi-year job '{job_id}' not found")


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "batch-data-manager",
        "jobs_count": len(jobs_db),
        "multi_year_jobs_count": len(multi_year_jobs),
        "data_sync_url": DATA_SYNC_URL,
    }


# --- Provider Credentials ---

class ProviderCredentials(BaseModel):
    provider: Literal["opta", "statsbomb", "custom"]
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    environment: Literal["production", "staging", "development"] = "production"
    is_active: bool = True


credentials_db: Dict[str, Dict[str, Any]] = {}


@app.get("/api/v2/admin/providers")
async def list_providers():
    result = []
    for provider in ("opta", "statsbomb", "custom"):
        creds = credentials_db.get(provider, {})
        result.append({
            "provider": provider,
            "is_configured": bool(creds),
            "environment": creds.get("environment", "not_configured"),
            "is_active": creds.get("is_active", False),
        })
    return {"providers": result}


@app.put("/api/v2/admin/providers/{provider}/credentials")
async def update_provider_credentials(provider: str, creds: ProviderCredentials):
    if provider != creds.provider:
        raise HTTPException(status_code=400, detail="Provider path mismatch")
    credentials_db[provider] = creds.model_dump()
    return {"status": "success", "provider": provider, "message": "Credentials updated"}


@app.get("/api/v2/admin/providers/{provider}/credentials")
async def get_provider_credentials(provider: str):
    if provider not in credentials_db:
        raise HTTPException(status_code=404, detail="Credentials not configured")

    creds = credentials_db[provider].copy()
    if creds.get("api_key"):
        creds["api_key"] = "****" + creds["api_key"][-4:] if len(creds["api_key"]) > 4 else "****"
    if creds.get("password"):
        creds["password"] = "****"
    return creds
