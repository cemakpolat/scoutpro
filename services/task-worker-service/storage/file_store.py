from __future__ import annotations

import io
import json
from typing import Any, Dict, Optional

from minio import Minio
from minio.error import S3Error


class FileStore:
    """MinIO-backed storage for large task outputs (PDFs, CSVs, videos)."""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool = False):
        self._client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        self._bucket = bucket
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    def upload_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> Dict[str, str]:
        self._client.put_object(
            self._bucket,
            key,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return {"storage": "minio", "bucket": self._bucket, "key": key}

    def upload_json(self, key: str, data: Any) -> Dict[str, str]:
        payload = json.dumps(data).encode()
        return self.upload_bytes(key, payload, content_type="application/json")

    def download_bytes(self, key: str) -> bytes:
        resp = self._client.get_object(self._bucket, key)
        try:
            return resp.read()
        finally:
            resp.close()
            resp.release_conn()

    def presigned_url(self, key: str, expires_seconds: int = 3600) -> str:
        from datetime import timedelta
        return self._client.presigned_get_object(self._bucket, key, expires=timedelta(seconds=expires_seconds))

    def delete(self, key: str) -> None:
        try:
            self._client.remove_object(self._bucket, key)
        except S3Error:
            pass
