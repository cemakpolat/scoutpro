from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, Optional
from datetime import datetime
import uuid
import asyncio

app = FastAPI(title="Batch Data Manager API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class BatchJobRequest(BaseModel):
    provider: Literal["opta", "statsbomb", "custom"] = Field(description="Data provider source")
    resource_type: Literal["match", "event", "player", "team"] = Field(description="Type of data to import")
    start_date: str = Field(description="Start date for import filtering (YYYY-MM-DD)", examples=["2023-01-01"])
    end_date: str = Field(description="End date for import filtering (YYYY-MM-DD)", examples=["2023-12-31"])
    competition_id: Optional[str] = None
    season_id: Optional[str] = None
    idempotency_token: str = Field(description="Unique token to prevent duplicate runs")


jobs_db: Dict[str, Any] = {}      # idempotency_token -> job
jobs_by_id: Dict[str, str] = {}   # job_id -> idempotency_token

RECORDS_BY_TYPE = {"match": 1523, "player": 342, "team": 48, "event": 87441}


async def simulate_job_progress(idempotency_token: str):
    await asyncio.sleep(1.5)
    if idempotency_token not in jobs_db:
        return
    jobs_db[idempotency_token]["status"] = "in_progress"
    jobs_db[idempotency_token]["started_at"] = datetime.utcnow().isoformat()

    for progress in [10, 25, 40, 60, 75, 90, 100]:
        await asyncio.sleep(2.5)
        if idempotency_token not in jobs_db:
            break
        if jobs_db[idempotency_token]["status"] == "cancelled":
            return
        jobs_db[idempotency_token]["progress"] = progress

    if idempotency_token in jobs_db and jobs_db[idempotency_token]["status"] == "in_progress":
        resource = jobs_db[idempotency_token]["request"].get("resource_type", "match")
        jobs_db[idempotency_token]["status"] = "completed"
        jobs_db[idempotency_token]["completed_at"] = datetime.utcnow().isoformat()
        jobs_db[idempotency_token]["records_processed"] = RECORDS_BY_TYPE.get(resource, 500)
        jobs_db[idempotency_token]["records_failed"] = 0


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
    }

    jobs_db[request.idempotency_token] = job
    jobs_by_id[job_id] = request.idempotency_token

    asyncio.create_task(simulate_job_progress(request.idempotency_token))

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
    }

    jobs_db[new_token] = new_job
    jobs_by_id[new_job_id] = new_token
    asyncio.create_task(simulate_job_progress(new_token))

    return {"status": "job_created", "job_id": new_job_id}


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "batch-data-manager", "jobs_count": len(jobs_db)}


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
