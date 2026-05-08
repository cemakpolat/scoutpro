from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, Optional

app = FastAPI(title="Batch Data Manager API", version="1.0.0")

class BatchJobRequest(BaseModel):
    provider: Literal["opta", "statsbomb", "custom"] = Field(description="Data provider source")
    resource_type: Literal["match", "event", "player", "team"] = Field(description="Type of data to import")
    start_date: str = Field(description="Start date for import filtering (YYYY-MM-DD)", examples=["2023-01-01"])
    end_date: str = Field(description="End date for import filtering (YYYY-MM-DD)", examples=["2023-12-31"])
    competition_id: Optional[str] = None
    season_id: Optional[str] = None
    idempotency_token: str = Field(description="Unique token to prevent duplicate runs")

# Track jobs in-memory for MVP (would be Mongo in production)
jobs_db: Dict[str, Any] = {}

@app.post("/api/v2/batch-jobs")
async def trigger_batch_job(request: BatchJobRequest):
    if request.idempotency_token in jobs_db:
        return {"status": "job_already_exists", "job": jobs_db[request.idempotency_token]}

    job_id = f"job_{len(jobs_db) + 1}_{request.provider}"
    jobs_db[request.idempotency_token] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "request": request.model_dump()
    }
    
    # In reality, we'd send a Kafka message to data-sync-service here
    
    return {"status": "job_created", "job_id": job_id}

@app.get("/api/v2/batch-jobs")
async def list_jobs():
    return {"jobs": list(jobs_db.values())}

@app.get("/api/v2/batch-jobs/{job_id}")
async def get_job_status(job_id: str):
    for token, job in jobs_db.items():
        if job["job_id"] == job_id:
            return {"job": job}
    raise HTTPException(status_code=404, detail="Job not found")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "batch-data-manager"}

# --- Provider Credentials Admin API ---
class ProviderCredentials(BaseModel):
    provider: Literal["opta", "statsbomb", "custom"]
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    environment: Literal["production", "staging", "development"] = "production"
    is_active: bool = True

credentials_db: Dict[str, Dict[str, Any]] = {}

@app.put("/api/v2/admin/providers/{provider}/credentials")
async def update_provider_credentials(provider: str, creds: ProviderCredentials):
    if provider != creds.provider:
        raise HTTPException(status_code=400, detail="Provider path mismatch")
    
    credentials_db[provider] = creds.model_dump()
    # Explicitly mapping passwords to **** in real response, returning masked here
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
