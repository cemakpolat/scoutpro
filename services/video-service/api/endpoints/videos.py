"""Video Service API Endpoints"""
import uuid
import logging
import os
from datetime import datetime, timezone
from typing import Optional, List

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Path, Query
from fastapi.responses import RedirectResponse
from motor.motor_asyncio import AsyncIOMotorClient

from config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/videos", tags=["videos"])

settings = get_settings()
BUCKET_NAME = "scoutpro-videos"
_KEYWORDS = ["goal", "corner", "penalty", "foul", "offside", "freekick", "header"]


def get_minio_client():
    """Create a boto3 S3 client configured for MinIO."""
    endpoint = os.getenv("MINIO_ENDPOINT", settings.minio_endpoint)
    if not endpoint.startswith("http"):
        endpoint = f"http://{endpoint}"
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", settings.minio_access_key),
        aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", settings.minio_secret_key),
        region_name="us-east-1",
    )


def _get_collection():
    """Return the MongoDB video_analyses collection."""
    client = AsyncIOMotorClient(settings.mongodb_url)
    return client[settings.mongodb_database]["video_analyses"]


def _ensure_bucket(s3) -> None:
    """Create the MinIO bucket if it does not exist."""
    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
    except ClientError:
        s3.create_bucket(Bucket=BUCKET_NAME)


def _extract_tags(filename: str) -> List[str]:
    """Extract known football event keywords from a filename."""
    lower = (filename or "").lower()
    return [kw for kw in _KEYWORDS if kw in lower]


# ---------------------------------------------------------------------------
# POST /upload
# ---------------------------------------------------------------------------

@router.post("/upload", summary="Upload a video")
async def upload_video(
    file: UploadFile = File(...),
    match_id: Optional[str] = Form(None),
    team_id: Optional[str] = Form(None),
):
    """Upload a video file to MinIO and store metadata in MongoDB."""
    try:
        s3 = get_minio_client()
        _ensure_bucket(s3)

        video_id = str(uuid.uuid4())
        minio_key = f"{video_id}/{file.filename}"
        content = await file.read()

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=minio_key,
            Body=content,
            ContentType=file.content_type or "video/mp4",
        )

        doc = {
            "video_id": video_id,
            "filename": file.filename,
            "size_bytes": len(content),
            "duration_seconds": None,
            "match_id": match_id,
            "team_id": team_id,
            "minio_key": minio_key,
            "upload_time": datetime.now(timezone.utc),
            "status": "uploaded",
            "tags": _extract_tags(file.filename or ""),
        }

        col = _get_collection()
        await col.insert_one(doc)
        doc.pop("_id", None)
        return doc

    except Exception as e:
        logger.error(f"Error uploading video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /  (list) — registered before /{video_id} to avoid shadowing
# ---------------------------------------------------------------------------

@router.get("/", summary="List videos")
async def list_videos(
    match_id: Optional[str] = Query(None),
    team_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
):
    """List video metadata with optional match_id / team_id filters."""
    try:
        col = _get_collection()
        query: dict = {}
        if match_id:
            query["match_id"] = match_id
        if team_id:
            query["team_id"] = team_id
        videos = await col.find(query, {"_id": 0}).limit(limit).to_list(length=limit)
        return {"videos": videos, "total": len(videos)}
    except Exception as e:
        logger.error(f"Error listing videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /{video_id}/stream — registered before /{video_id} to avoid shadowing
# ---------------------------------------------------------------------------

@router.get("/{video_id}/stream", summary="Stream video")
async def stream_video(video_id: str = Path(...)):
    """Generate a 1-hour presigned MinIO URL and redirect (307) to it."""
    try:
        col = _get_collection()
        doc = await col.find_one({"video_id": video_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Video not found")

        s3 = get_minio_client()
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": doc["minio_key"]},
            ExpiresIn=3600,
        )
        return RedirectResponse(url=url, status_code=307)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming video {video_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /{video_id}
# ---------------------------------------------------------------------------

@router.get("/{video_id}", summary="Get video metadata")
async def get_video(video_id: str = Path(...)):
    """Fetch video metadata from MongoDB by video_id."""
    try:
        col = _get_collection()
        doc = await col.find_one({"video_id": video_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Video not found")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video {video_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# DELETE /{video_id}
# ---------------------------------------------------------------------------

@router.delete("/{video_id}", summary="Delete video")
async def delete_video(video_id: str = Path(...)):
    """Delete video from MinIO and remove metadata from MongoDB."""
    try:
        col = _get_collection()
        doc = await col.find_one({"video_id": video_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Video not found")

        s3 = get_minio_client()
        try:
            s3.delete_object(Bucket=BUCKET_NAME, Key=doc["minio_key"])
        except Exception as minio_err:
            logger.warning(f"MinIO delete failed for {video_id}: {minio_err}")

        await col.delete_one({"video_id": video_id})
        return {"message": "Video deleted", "video_id": video_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting video {video_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# POST /{video_id}/analyze
# ---------------------------------------------------------------------------

@router.post("/{video_id}/analyze", summary="Analyze video")
async def analyze_video(video_id: str = Path(...)):
    """
    Mark a video as 'analyzing' and record basic analysis stats.

    Frame count is estimated at 25 fps. Tags are extracted from the filename
    using football event keywords (goal, corner, penalty, …).
    """
    try:
        col = _get_collection()
        doc = await col.find_one({"video_id": video_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Video not found")

        duration = doc.get("duration_seconds") or 0
        frame_count = int(duration * 25)
        tags = _extract_tags(doc.get("filename", ""))

        await col.update_one(
            {"video_id": video_id},
            {
                "$set": {
                    "status": "analyzing",
                    "analysis": {
                        "duration_seconds": duration,
                        "frame_count": frame_count,
                        "tags": tags,
                        "started_at": datetime.now(timezone.utc),
                    },
                }
            },
        )

        return {
            "video_id": video_id,
            "status": "analyzing",
            "analysis": {
                "duration_seconds": duration,
                "frame_count": frame_count,
                "tags": tags,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing video {video_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# POST /{video_id}/link-event
# ---------------------------------------------------------------------------

@router.post("/{video_id}/link-event", summary="Link video to a match event")
async def link_video_to_event(
    video_id: str = Path(...),
    match_id: str = Query(..., description="Match ID"),
    event_id: Optional[str] = Query(None, description="Event ID (MongoDB ObjectId)"),
    event_timestamp: Optional[int] = Query(None, description="Event timestamp in match (seconds)"),
    event_type: Optional[str] = Query(None, description="Event type (goal, corner, foul, etc.)"),
    notes: Optional[str] = Query(None, description="Additional notes about the event"),
):
    """
    Link a video to a specific match event.
    
    This allows the system to quickly retrieve videos for a given match event,
    enabling event-driven video lookup for replays and analysis.
    """
    try:
        col = _get_collection()
        
        # Verify video exists
        doc = await col.find_one({"video_id": video_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")
        
        # Create event link
        event_link = {
            "match_id": match_id,
            "event_id": event_id,
            "event_timestamp": event_timestamp,
            "event_type": event_type,
            "notes": notes,
            "linked_at": datetime.now(timezone.utc),
        }
        
        # Update video with event link
        result = await col.update_one(
            {"video_id": video_id},
            {
                "$push": {
                    "event_links": event_link
                },
                "$set": {
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")
        
        return {
            "success": True,
            "video_id": video_id,
            "event_link": event_link,
            "message": f"Video linked to event in match {match_id}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking video to event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET / with event filtering
# ---------------------------------------------------------------------------

@router.get("/", summary="List videos with optional event filtering")
async def list_videos_with_event_filter(
    match_id: Optional[str] = Query(None, description="Filter by match ID"),
    event_id: Optional[str] = Query(None, description="Filter by event ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    team_id: Optional[str] = Query(None, description="Filter by team ID"),
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
):
    """
    List videos with optional filtering by match or event.
    
    Filters:
    - match_id: Get all videos for a specific match
    - event_id: Get videos linked to a specific event
    - event_type: Get videos of specific event types (goal, corner, etc.)
    - team_id: Get videos from team's matches
    """
    try:
        col = _get_collection()
        
        # Build query
        query = {}
        
        if match_id:
            query["$or"] = [
                {"match_id": match_id},
                {"event_links.match_id": match_id}
            ]
        
        if event_id:
            query["event_links.event_id"] = event_id
        
        if event_type:
            query["event_links.event_type"] = event_type
        
        if team_id:
            query["team_id"] = team_id
        
        # Fetch videos
        cursor = col.find(query).skip(skip).limit(limit)
        videos = await cursor.to_list(length=limit)
        
        # Clean response
        for video in videos:
            video.pop("_id", None)
        
        total = await col.count_documents(query)
        
        return {
            "videos": videos,
            "total": total,
            "limit": limit,
            "skip": skip,
            "pages": (total + limit - 1) // limit
        }
    
    except Exception as e:
        logger.error(f"Error listing videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

