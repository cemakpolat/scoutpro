"""
Feature Extractor - Bootstrap player_features from player_statistics
"""
import logging
import math
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://root:scoutpro123@mongo:27017/scoutpro")


async def bootstrap_player_features() -> int:
    """
    Read player_statistics and upsert 15-dimensional derived features into player_features.
    Returns the count of upserted documents.
    """
    try:
        from motor.motor_asyncio import AsyncIOMotorClient

        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        db = client.get_default_database()
        stats_col = db["player_statistics"]
        features_col = db["player_features"]

        count = 0
        async for doc in stats_col.find({}):
            player_id = doc.get("playerID") or doc.get("player_id")
            if not player_id:
                continue

            passes = int(doc.get("passes", 0) or 0)
            passes_completed = int(doc.get("passes_completed", 0) or 0)
            shots = int(doc.get("shots", 0) or 0)
            goals = int(doc.get("goals", 0) or 0)
            fouls = int(doc.get("fouls", 0) or 0)
            duels = int(doc.get("duels", 0) or 0)
            duels_won = int(doc.get("duels_won", 0) or 0)
            tackles = int(doc.get("tackles", 0) or 0)
            tackles_won = int(doc.get("tackles_won", 0) or 0)
            take_ons = int(doc.get("take_ons", 0) or 0)
            take_ons_won = int(doc.get("take_ons_won", 0) or 0)
            interceptions = int(doc.get("interceptions", 0) or 0)
            saves = int(doc.get("saves", 0) or 0)
            goalkeeper_actions = int(doc.get("goalkeeper_actions", 0) or 0)
            total_events = int(doc.get("total_events", 1) or 1)
            matches = int(doc.get("matches_played", 1) or 1)

            features = {
                # 1. pass_accuracy
                "pass_accuracy": passes_completed / passes if passes > 0 else 0.0,
                # 2. shot_accuracy
                "shot_accuracy": goals / shots if shots > 0 else 0.0,
                # 3. shot_conversion
                "shot_conversion": goals / shots if shots > 0 else 0.0,
                # 4. duel_win_rate
                "duel_win_rate": duels_won / duels if duels > 0 else 0.0,
                # 5. tackle_success_rate
                "tackle_success_rate": tackles_won / tackles if tackles > 0 else 0.0,
                # 6. take_on_success_rate
                "take_on_success_rate": take_ons_won / take_ons if take_ons > 0 else 0.0,
                # 7. aerial_win_rate (placeholder)
                "aerial_win_rate": 0.0,
                # 8. goals_per_90 (proxy: total_events as minute proxy)
                "goals_per_90": goals / (total_events / 1000.0) if total_events > 0 else 0.0,
                # 9. assists_per_90 (placeholder)
                "assists_per_90": 0.0,
                # 10. key_passes_per_90 (placeholder)
                "key_passes_per_90": 0.0,
                # 11. pressures_applied
                "pressures_applied": float(doc.get("event_pressure", 0) or 0),
                # 12. save_rate
                "save_rate": saves / goalkeeper_actions if goalkeeper_actions > 0 else 0.0,
                # 13. interception_rate
                "interception_rate": interceptions / total_events if total_events > 0 else 0.0,
                # 14. foul_rate
                "foul_rate": fouls / total_events if total_events > 0 else 0.0,
                # 15. matches_played
                "matches_played": matches,
            }

            await features_col.update_one(
                {"playerID": str(player_id)},
                {
                    "$set": {
                        "playerID": str(player_id),
                        "features": features,
                        # Keep flat fields for backward compatibility with existing ML queries
                        **features,
                        "updated_at": datetime.now(timezone.utc),
                        "updatedAt": datetime.now(timezone.utc),
                    }
                },
                upsert=True,
            )
            count += 1

        client.close()
        logger.info(f"Bootstrapped {count} player feature documents (15 dimensions) from player_statistics")
        return count

    except Exception as e:
        logger.error(f"Feature bootstrap failed: {e}")
        return 0


async def compute_player_xg_total(player_id: str) -> dict:
    """
    Read all shot events for a given player_id from match_events,
    compute analytical xG for each (distance-based fallback), sum them,
    and update player_features with xG_total and xA_total.

    Returns a dict with player_id, xG_total, shot_count.
    """
    try:
        from motor.motor_asyncio import AsyncIOMotorClient

        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        db = client.get_default_database()
        events_col = db["match_events"]
        features_col = db["player_features"]

        xg_total = 0.0
        shot_count = 0

        query = {
            "type_name": "shot",
            "$or": [{"player_id": player_id}, {"player_id": int(player_id) if str(player_id).isdigit() else None}],
        }
        async for shot in events_col.find(query, {"location": 1, "raw_event": 1}):
            loc = shot.get("location") or {}
            try:
                x = float(loc.get("x", 50))
                y = float(loc.get("y", 50))
                dx = (100.0 - x) / 100.0 * 105.0
                dy = (50.0 - y) / 100.0 * 68.0
                distance = math.sqrt(dx ** 2 + dy ** 2)
                raw = shot.get("raw_event") or {}
                body_part = str(raw.get("body_part", "")).lower()
                shot_type = str(raw.get("shot_type", "")).lower()
                base_xg = 0.35 * math.exp(-0.1 * max(distance, 1.0))
                if "head" in body_part:
                    base_xg *= 0.6
                if shot_type == "penalty":
                    base_xg = 0.76
                xg_total += base_xg
                shot_count += 1
            except Exception:
                continue

        xg_total = round(xg_total, 4)

        await features_col.update_one(
            {"playerID": str(player_id)},
            {
                "$set": {
                    "xG_total": xg_total,
                    "xA_total": 0.0,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )

        client.close()
        return {"player_id": player_id, "xG_total": xg_total, "shot_count": shot_count}

    except Exception as e:
        logger.error(f"compute_player_xg_total failed for {player_id}: {e}")
        return {"player_id": player_id, "xG_total": 0.0, "shot_count": 0, "error": str(e)}
