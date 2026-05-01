#!/usr/bin/env python3
"""
Step 3: Feature Engineering Pipeline (Medallion Gold Tier)
Extracts raw events from MongoDB/TimescaleDB, computes ML features,
and uploads them as .parquet to MinIO for ML model training.
"""
import os
import sys
import logging
from io import BytesIO
from pymongo import MongoClient
import pandas as pd

# Add parent directory to path to import shared modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We need minio for direct upload
try:
    from minio import Minio
except ImportError:
    print("Please install minio and pandas: pip install minio pandas pyarrow")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

def get_minio_client():
    endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    # For local docker-compose port mapping, MinIO API is often 9000
    return Minio(
        endpoint,
        access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123"),
        secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
    )

def build_xt_features():
    """Build Expected Threat (xT) feature dataset from match events."""
    mongo_url = os.getenv("MONGODB_URI", "mongodb://root:scoutpro123@localhost:27017/scoutpro?authSource=admin")
    client = MongoClient(mongo_url)
    db = client.get_default_database()
    
    logging.info("Querying MongoDB for match events...")
    events = list(db.match_events.find({
        # Only looking at passes and carries for threat
        "type_name": {"$in": ["Pass", "Carry"]}
    }).limit(50000)) # Limit for demonstration
    
    if not events:
        logging.warning("No events found in db.match_events.")
        return None

    logging.info(f"Processing {len(events)} events for xT features...")
    
    # Feature Engineering
    features = []
    for e in events:
        # Dummy logic for coordinates - adapt to actual schema
        start_x = e.get("x", 50.0)
        start_y = e.get("y", 50.0)
        end_x = e.get("end_x", 50.0)
        end_y = e.get("end_y", 50.0)
        
        # Threat indicator: e.g., leads to a shot, or enters penalty box (x > 80, y between 20-80)
        is_threat = 1 if (end_x > 80 and 20 < end_y < 80) else 0

        features.append({
            "event_id": str(e.get("_id", "")),
            "match_id": e.get("match_id", ""),
            "player_id": e.get("player_id", ""),
            "start_x": start_x,
            "start_y": start_y,
            "end_x": end_x,
            "end_y": end_y,
            "is_threat": is_threat
        })
        
    df = pd.DataFrame(features)
    return df

def upload_dataframe_to_minio(client, df, bucket, object_name):
    """Upload pandas DataFrame as Parquet directly to MinIO."""
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        
    parquet_buffer = BytesIO()
    df.to_parquet(parquet_buffer, index=False)
    parquet_buffer.seek(0)
    
    client.put_object(
        bucket,
        object_name,
        parquet_buffer,
        length=parquet_buffer.getbuffer().nbytes,
        content_type="application/octet-stream"
    )
    logging.info(f"✅ Successfully uploaded {object_name} to MinIO bucket '{bucket}'. Size: {parquet_buffer.getbuffer().nbytes} bytes.")

def main():
    try:
        minio_client = get_minio_client()
        df_xt = build_xt_features()
        if df_xt is not None and not df_xt.empty:
            upload_dataframe_to_minio(minio_client, df_xt, "scoutpro-ml-features", "xt_training_features_2026.parquet")
    except Exception as e:
        logging.error(f"Feature building failed: {e}")

if __name__ == "__main__":
    main()
