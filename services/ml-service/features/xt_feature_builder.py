"""Expected Threat (xT) feature engineering pipeline — Gold Medallion tier.

Replaces: scripts/build_ml_features.py

Reads enriched events from the ``match_events`` MongoDB collection,
computes xT-relevant features for each event, and uploads the resulting
feature table to MinIO as Parquet so that downstream model training jobs
can consume it without direct database access.

Usage
-----
Run directly (e.g. from a Kubernetes CronJob or the batch pipeline)::

    python -m features.xt_feature_builder

Or call programmatically from the ml-service engine::

    from features.xt_feature_builder import XTFeatureBuilder

    builder = XTFeatureBuilder()
    result = builder.run(output_object="xt_features_2025.parquet")
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_MONGO_URL_DEFAULT = (
    "mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin"
)
_MINIO_BUCKET = "scoutpro-ml-features"

# Pitch area thresholds (0-100 scale, same as ScoutPro canonical coordinates)
_THREAT_ZONE_X_MIN = 80.0   # final fifth of the pitch
_THREAT_ZONE_Y_MIN = 20.0
_THREAT_ZONE_Y_MAX = 80.0

_PASS_CARRY_TYPES = {"pass", "carry", "cross", "dribble"}
_SHOT_TYPES = {"shot", "miss", "post", "attempt_saved", "goal"}


class XTFeatureBuilder:
    """Build an xT feature table from ``match_events`` and upload to MinIO.

    Args:
        mongo_uri:   Override MongoDB URI (defaults to env ``MONGODB_URL``).
        minio_endpoint: Override MinIO endpoint (defaults to env ``MINIO_ENDPOINT``).
        db_name:     Mongo database (default: ``scoutpro``).
        event_limit: Max events fetched in one run (for memory safety; 0 = unlimited).
    """

    def __init__(
        self,
        mongo_uri: Optional[str] = None,
        minio_endpoint: Optional[str] = None,
        db_name: str = "scoutpro",
        event_limit: int = 100_000,
    ) -> None:
        self.mongo_uri = mongo_uri or os.getenv("MONGODB_URL", _MONGO_URL_DEFAULT)
        self.minio_endpoint = minio_endpoint or os.getenv("MINIO_ENDPOINT", "minio:9000")
        self.db_name = db_name
        self.event_limit = event_limit

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    def run(
        self,
        output_object: str = "xt_features_latest.parquet",
        bucket: str = _MINIO_BUCKET,
        match_id: Optional[str] = None,
        season_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build features and upload to MinIO.

        Args:
            output_object: MinIO object name (key) for the uploaded Parquet file.
            bucket:        MinIO bucket.
            match_id:      Limit to one match (optional).
            season_id:     Limit to one season (optional).

        Returns:
            Dict with ``rows``, ``bucket``, ``object``, and ``bytes_uploaded``.
        """
        try:
            import pandas as pd
        except ImportError as e:
            raise RuntimeError(
                "pandas is required for feature building. "
                "Install with: pip install pandas pyarrow"
            ) from e

        events = self._fetch_events(match_id=match_id, season_id=season_id)
        if not events:
            logger.warning("XTFeatureBuilder: no events found, aborting")
            return {"rows": 0, "bucket": bucket, "object": output_object}

        df = self._build_features(events, pd)
        bytes_uploaded = self._upload(df, bucket, output_object)

        logger.info(
            "XTFeatureBuilder: %d rows → s3://%s/%s (%d bytes)",
            len(df),
            bucket,
            output_object,
            bytes_uploaded,
        )
        return {
            "rows": len(df),
            "bucket": bucket,
            "object": output_object,
            "bytes_uploaded": bytes_uploaded,
        }

    # ------------------------------------------------------------------
    # Internal: data fetch
    # ------------------------------------------------------------------

    def _fetch_events(
        self,
        match_id: Optional[str] = None,
        season_id: Optional[str] = None,
    ) -> List[Dict]:
        from pymongo import MongoClient

        query: Dict[str, Any] = {
            "type_name": {"$in": sorted(_PASS_CARRY_TYPES | _SHOT_TYPES)},
        }
        if match_id:
            query["$or"] = [{"matchID": match_id}, {"match_id": match_id}]
        if season_id:
            query["season_id"] = season_id

        client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
        try:
            db = client[self.db_name]
            cursor = db.match_events.find(query)
            if self.event_limit:
                cursor = cursor.limit(self.event_limit)
            return list(cursor)
        finally:
            client.close()

    # ------------------------------------------------------------------
    # Internal: feature engineering
    # ------------------------------------------------------------------

    def _build_features(self, events: List[Dict], pd: Any) -> Any:
        rows = []
        for ev in events:
            loc = ev.get("location") or {}
            start_x = float(loc.get("x") or ev.get("x") or 50)
            start_y = float(loc.get("y") or ev.get("y") or 50)
            end_x = float(ev.get("end_x") or ev.get("end_location", {}).get("x") or start_x)
            end_y = float(ev.get("end_y") or ev.get("end_location", {}).get("y") or start_y)

            type_name = str(ev.get("type_name", "")).lower()
            is_shot = int(type_name in _SHOT_TYPES)
            is_goal = int(bool(ev.get("is_goal")))

            # Distance moved toward goal (positive = progressive)
            delta_x = end_x - start_x

            # Whether the action ends inside the threat zone
            enters_threat_zone = int(
                end_x >= _THREAT_ZONE_X_MIN
                and _THREAT_ZONE_Y_MIN <= end_y <= _THREAT_ZONE_Y_MAX
            )

            # Analytical xG from the enrichment layer (may be absent)
            analytical_xg = float(ev.get("analytical_xg") or 0)

            rows.append(
                {
                    "event_id": str(ev.get("event_id") or ev.get("_id", "")),
                    "scoutpro_event_id": ev.get("scoutpro_event_id") or "",
                    "match_id": ev.get("matchID") or ev.get("match_id") or "",
                    "scoutpro_match_id": ev.get("scoutpro_match_id") or "",
                    "player_id": ev.get("player_id") or "",
                    "scoutpro_player_id": ev.get("scoutpro_player_id") or "",
                    "team_id": ev.get("team_id") or "",
                    "type_name": type_name,
                    "period": int(ev.get("period") or 1),
                    "minute": int(ev.get("minute") or 0),
                    "start_x": start_x,
                    "start_y": start_y,
                    "end_x": end_x,
                    "end_y": end_y,
                    "delta_x": delta_x,
                    "enters_threat_zone": enters_threat_zone,
                    "progressive_pass": int(bool(ev.get("progressive_pass"))),
                    "entered_final_third": int(bool(ev.get("entered_final_third"))),
                    "entered_box": int(bool(ev.get("entered_box"))),
                    "high_regain": int(bool(ev.get("high_regain"))),
                    "is_shot": is_shot,
                    "is_goal": is_goal,
                    "analytical_xg": analytical_xg,
                    "is_successful": int(bool(ev.get("is_successful"))),
                    "competition_id": ev.get("competition_id") or "",
                    "season_id": ev.get("season_id") or "",
                    "event_source": ev.get("event_source") or "",
                }
            )

        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Internal: MinIO upload
    # ------------------------------------------------------------------

    def _upload(self, df: Any, bucket: str, object_name: str) -> int:
        try:
            from minio import Minio
        except ImportError as e:
            raise RuntimeError(
                "minio-py is required for feature upload. "
                "Install with: pip install minio"
            ) from e

        client = Minio(
            self.minio_endpoint,
            access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
            secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
        )

        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)

        buf = BytesIO()
        df.to_parquet(buf, index=False, engine="pyarrow")
        size = buf.tell()
        buf.seek(0)

        client.put_object(
            bucket,
            object_name,
            buf,
            length=size,
            content_type="application/octet-stream",
        )
        return size


# ---------------------------------------------------------------------------
# CLI entry-point (python -m features.xt_feature_builder)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    season = sys.argv[1] if len(sys.argv) > 1 else None
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    obj_name = f"xt_features_{season or 'latest'}_{timestamp}.parquet"

    builder = XTFeatureBuilder()
    result = builder.run(output_object=obj_name, season_id=season)
    print(result)
