"""
Live Ingestion API Endpoints
"""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from typing import Dict, Any, List
from pydantic import BaseModel
import sys
sys.path.append('/app')
from shared.models.base import APIResponse

router = APIRouter(prefix="/api/v2/ingestion", tags=["ingestion"])

# Track active ingestion tasks
active_tasks = {}

class EventsPayload(BaseModel):
    events: List[Dict[str, Any]]
    
async def process_batch_background(events: List[Dict[str, Any]], request: Request, match_id: str):
    processor = getattr(request.app.state, "processor", None)
    if processor:
        try:
            # Transform statsbomb row format to the required internal format if necessary, 
            # or directly pass raw to process_live_update.
            payload = {
                "match_id": match_id,
                "events": events,
                "stats": {}
            }
            await processor.process_live_update(payload)
        except Exception as e:
            print(f"Failed background processing: {e}")

@router.post("/events/{match_id}", response_model=APIResponse, status_code=202)
async def ingest_events(match_id: str, payload: EventsPayload, request: Request, background_tasks: BackgroundTasks):
    """Receive a batch of physical match events (e.g. parsed from CSV/XML)"""
    if len(payload.events) == 0:
        return APIResponse(success=False, message="No events provided")
    
    # Store ingestion processing as background task
    background_tasks.add_task(process_batch_background, payload.events, request, match_id)
    
    return APIResponse(
        success=True,
        data={"match_id": match_id, "processed_events": len(payload.events)},
        message=f"Queued {len(payload.events)} events for processing"
    )

@router.post("/start/{match_id}", response_model=APIResponse)
async def start_ingestion(match_id: str):
    """Start ingesting live data for a match"""
    if match_id in active_tasks:
        return APIResponse(
            success=True,
            message=f"Ingestion already active for match {match_id}"
        )

    # This would start a background task
    active_tasks[match_id] = {"status": "active", "match_id": match_id}

    return APIResponse(
        success=True,
        data={"match_id": match_id, "status": "started"},
        message=f"Started ingestion for match {match_id}"
    )


@router.post("/stop/{match_id}", response_model=APIResponse)
async def stop_ingestion(match_id: str):
    """Stop ingesting live data for a match"""
    if match_id not in active_tasks:
        raise HTTPException(
            status_code=404,
            detail=f"No active ingestion for match {match_id}"
        )

    # Stop the task
    del active_tasks[match_id]

    return APIResponse(
        success=True,
        data={"match_id": match_id, "status": "stopped"},
        message=f"Stopped ingestion for match {match_id}"
    )


@router.get("/status", response_model=APIResponse)
async def get_ingestion_status():
    """Get status of all active ingestion tasks"""
    return APIResponse(
        success=True,
        data={
            "active_tasks": list(active_tasks.values()),
            "count": len(active_tasks)
        },
        message=f"{len(active_tasks)} active ingestion tasks"
    )


@router.get("/status/{match_id}", response_model=APIResponse)
async def get_match_ingestion_status(match_id: str):
    """Get ingestion status for a specific match"""
    if match_id not in active_tasks:
        raise HTTPException(
            status_code=404,
            detail=f"No active ingestion for match {match_id}"
        )

    return APIResponse(
        success=True,
        data=active_tasks[match_id],
        message=f"Ingestion status for match {match_id}"
    )
