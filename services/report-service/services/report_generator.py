"""
Report Generator Service
Manages asynchronous report generation and storage
"""
import uuid
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
import sys
sys.path.append('/app')
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Global fallback for local dev when Redis/MinIO aren't accessible
_LOCAL_REPORTS_DB = {}

class ReportGenerator:
    """Manages report generation jobs and storage using Redis and MinIO"""

    def __init__(self):
        self.settings = get_settings()
        self.redis = None
        self.minio = None
        self._init_clients()

    def _init_clients(self):
        try:
            import redis.asyncio as aioredis
            self.redis = aioredis.from_url(self.settings.redis_url, decode_responses=True)
        except Exception as e:
            logger.warning(f"Failed to initialize Redis client: {e}")

        try:
            from minio import Minio
            self.minio = Minio(
                self.settings.minio_endpoint,
                access_key=self.settings.minio_access_key,
                secret_key=self.settings.minio_secret_key,
                secure=self.settings.minio_secure
            )
            # Ensure bucket exists
            if not self.minio.bucket_exists(self.settings.minio_bucket):
                self.minio.make_bucket(self.settings.minio_bucket)
        except Exception as e:
            logger.warning(f"Failed to initialize MinIO client: {e}")

    async def _save_job(self, report_id: str, data: dict):
        if self.redis:
            try:
                # Convert enums or complex types before checking
                clean_data = {}
                for k, v in data.items():
                    if hasattr(v, "dict"):
                        clean_data[k] = v.dict()
                    elif isinstance(v, Enum):
                        clean_data[k] = v.value
                    elif type(v).__name__ == "ReportRequest":
                        clean_data[k] = {"format": getattr(v, "format", "pdf")}
                    else:
                        clean_data[k] = v

                # Handle payload that shouldn't be cast directly to string
                await self.redis.setex(
                    f"report_job:{report_id}", 
                    timedelta(days=30), 
                    json.dumps(clean_data)
                )
                return
            except Exception as e:
                logger.error(f"Redis error saving job: {e}")
                
        # Fallback
        _LOCAL_REPORTS_DB[report_id] = data

    async def _get_job(self, report_id: str) -> Optional[dict]:
        if self.redis:
            try:
                data_str = await self.redis.get(f"report_job:{report_id}")
                if data_str:
                    return json.loads(data_str)
            except Exception as e:
                logger.error(f"Redis error getting job: {e}")
        # Fallback
        return _LOCAL_REPORTS_DB.get(report_id)

    async def create_report_job(self, request: Any) -> str:
        report_id = str(uuid.uuid4())
        
        # Attempt to convert Pydantic to dict 
        req_data = request.dict() if hasattr(request, "dict") else request
        
        job_data = {
            "report_id": report_id,
            "status": "pending",
            "request": req_data,
            "created_at": datetime.now().isoformat(),
            "download_url": None,
            "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
        }

        await self._save_job(report_id, job_data)
        logger.info(f"Created report job: {report_id}")
        return report_id

    async def process_report(self, report_id: str, request: Any):
        try:
            job = await self._get_job(report_id)
            if not job:
                logger.error(f"Job {report_id} not found to process")
                return

            # Update status to processing
            job["status"] = "processing"
            await self._save_job(report_id, job)

            # Generate the report based on type
            from services.pdf_generator import PDFGenerator
            from services.excel_generator import ExcelGenerator

            fmt = request.format.value if hasattr(request.format, "value") else request.format
            rtype = request.report_type.value if hasattr(request.report_type, "value") else request.report_type

            if fmt == "pdf":
                generator = PDFGenerator()
            else:
                generator = ExcelGenerator()

            # Generate based on report type
            content = None
            if rtype == "player" and len(request.entity_ids) > 0:
                content = await generator.generate_player_report(request.entity_ids[0], include_stats=getattr(request, 'include_stats', True))
            elif rtype == "team" and len(request.entity_ids) > 0:
                content = await generator.generate_team_report(request.entity_ids[0], include_stats=getattr(request, 'include_stats', True))
            elif rtype == "match" and len(request.entity_ids) > 0:
                content = await generator.generate_match_report(request.entity_ids[0], include_stats=getattr(request, 'include_stats', True))

            if content:
                import io
                content_bytes = io.BytesIO(content) if isinstance(content, bytes) else io.BytesIO(content.encode('utf-8'))
                
                minio_success = False
                if self.minio:
                    try:
                        filename = f"{report_id}.{fmt}"
                        self.minio.put_object(
                            self.settings.minio_bucket, 
                            filename, 
                            content_bytes, 
                            length=content_bytes.getbuffer().nbytes,
                            content_type="application/pdf" if fmt == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        job["minio_object"] = filename
                        minio_success = True
                    except Exception as e:
                        logger.error(f"MinIO upload failed: {e}")

                if not minio_success:
                    # Fallback to local memory
                    job["content"] = content

                job["status"] = "completed"
                job["download_url"] = f"/api/v2/reports/{report_id}/download"
                await self._save_job(report_id, job)
                logger.info(f"Report {report_id} generated successfully")
            else:
                job["status"] = "failed"
                job["error"] = "Failed to generate report content"
                await self._save_job(report_id, job)
                logger.error(f"Report {report_id} generation failed")

        except Exception as e:
            logger.error(f"Error processing report {report_id}: {e}")
            job = await self._get_job(report_id)
            if job:
                job["status"] = "failed"
                job["error"] = str(e)
                await self._save_job(report_id, job)

    async def get_report_status(self, report_id: str) -> Optional[Dict[str, Any]]:
        job = await self._get_job(report_id)
        if not job:
            return None
        return {
            "report_id": report_id,
            "status": job["status"],
            "download_url": job.get("download_url"),
            "created_at": job["created_at"],
            "expires_at": job.get("expires_at")
        }

    async def download_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        job = await self._get_job(report_id)
        if not job or job.get("status") != "completed":
            return None

        content = job.get("content")
        req = job.get("request", {})
        fmt = req.get("format", "pdf") if isinstance(req, dict) else "pdf"
        
        if not content and "minio_object" in job and self.minio:
            try:
                response = self.minio.get_object(self.settings.minio_bucket, job["minio_object"])
                content = response.read()
                response.close()
                response.release_conn()
            except Exception as e:
                logger.error(f"Failed to fetch {job['minio_object']} from Minio: {e}")

        if not content:
            return None

        content_type = "application/pdf" if fmt == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"report_{report_id}.{fmt}"

        return {
            "content": content,
            "content_type": content_type,
            "filename": filename
        }
