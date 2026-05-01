"""
Data Lake Connector (MinIO Bronze/Silver Tier)
Connects ScoutPro microservices to Object Storage.
"""
import os
import json
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

class DataLakeClient:
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ROOT_USER", "minioadmin")
        self.secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        try:
            from minio import Minio
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
            self._ensure_buckets()
        except ImportError:
            self.client = None
            logger.warning("Minio pip package missing. DataLake disabled.")
        except Exception as e:
            self.client = None
            logger.warning(f"Could not connect to MinIO: {e}")

    def _ensure_buckets(self):
        if not self.client: return
        buckets = ["scoutpro-raw", "scoutpro-ml-features", "scoutpro-models"]
        for bucket in buckets:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)

    def upload_raw_json(self, bucket: str, object_name: str, payload: dict):
        """STEP 1: Landing Raw Data in Bronze Tier."""
        if not self.client: return False
        try:
            raw_bytes = json.dumps(payload).encode("utf-8")
            self.client.put_object(
                bucket,
                object_name,
                BytesIO(raw_bytes),
                length=len(raw_bytes),
                content_type="application/json"
            )
            logger.info(f"✅ DataLake: Uploaded {object_name} to {bucket}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload raw JSON: {e}")
            return False
            
    def load_parquet_as_dataframe(self, bucket: str, object_name: str):
        """STEP 3: Connect ML-Service directly to Parquet Features (Gold Tier)"""
        if not self.client: raise ConnectionError("MinIO disconnected.")
        import pandas as pd
        import io
        
        response = self.client.get_object(bucket, object_name)
        file_bytes = response.data
        return pd.read_parquet(io.BytesIO(file_bytes))

datalake = DataLakeClient()
