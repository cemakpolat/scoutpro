import asyncio
import logging
import os
from datetime import datetime, timezone
from shared.messaging.kafka_consumer import KafkaConsumerClient
from config.settings import get_settings
from services.feature_pipeline import FeatureEngineeringPipeline

logger = logging.getLogger(__name__)
settings = get_settings()

_MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://root:scoutpro123@mongo:27017/scoutpro")


class MLFeatureStreamProcessor:
    def __init__(self):
        self.settings = get_settings()
        self.consumer = KafkaConsumerClient(
            topics=['raw.events'],
            group_id='ml_service_feature_engineering'
        )
        self.pipeline = FeatureEngineeringPipeline()
        self.running = False
        self._db_client = None
        self._features_col = None
        
    async def start(self):
        self.running = True
        logger.info("Starting ML Feature Stream Processor...")
        await self.consumer.start()
        
        try:
            async for message in self.consumer.consume():
                if not self.running:
                    break
                    
                await self.process_event(message)
                    
        except Exception as e:
            logger.error(f"Error in ML feature stream: {e}")
            raise

    async def stop(self):
        self.running = False
        if self.consumer:
            await self.consumer.stop()
        if self._db_client:
            self._db_client.close()
        logger.info("ML Feature Stream Processor stopped")

    async def _get_features_col(self):
        if self._features_col is None:
            from motor.motor_asyncio import AsyncIOMotorClient
            self._db_client = AsyncIOMotorClient(_MONGODB_URL, serverSelectionTimeoutMS=3000)
            db = self._db_client.get_default_database()
            self._features_col = db["player_features"]
        return self._features_col

    async def _persist_player_feature(self, player_id: str, event_type_name: str, event_data: dict):
        """Increment per-player feature counters in MongoDB based on event type."""
        event_lower = event_type_name.lower()
        inc = {}

        if event_lower == "pass":
            inc["total_passes"] = 1
            pass_data = event_data.get("pass") or {}
            outcome_name = (pass_data.get("outcome") or {}).get("name", "")
            if outcome_name == "Complete":
                inc["passes_completed"] = 1
        elif event_lower == "shot":
            inc["total_shots"] = 1
            shot_data = event_data.get("shot") or {}
            outcome_name = (shot_data.get("outcome") or {}).get("name", "")
            if outcome_name == "Goal":
                inc["goals"] = 1
        elif event_lower in ("duel", "tackle"):
            inc["total_duels"] = 1
            duel_data = event_data.get("duel") or {}
            outcome_name = (duel_data.get("outcome") or {}).get("name", "").lower()
            if "won" in outcome_name or "success" in outcome_name:
                inc["duels_won"] = 1
            if event_lower == "tackle":
                inc["total_tackles"] = 1

        if not inc:
            return

        try:
            col = await self._get_features_col()
            await col.update_one(
                {"playerID": player_id},
                {
                    "$inc": inc,
                    "$set": {"playerID": player_id, "updatedAt": datetime.now(timezone.utc)},
                    "$setOnInsert": {"matches_played": 1},
                },
                upsert=True,
            )
            # Recompute derived accuracy fields
            doc = await col.find_one({"playerID": player_id}, {"total_passes": 1, "passes_completed": 1,
                                                                 "total_shots": 1, "goals": 1,
                                                                 "total_duels": 1, "duels_won": 1})
            if doc:
                total_passes = doc.get("total_passes", 0) or 0
                passes_completed = doc.get("passes_completed", 0) or 0
                total_shots = doc.get("total_shots", 0) or 0
                goals = doc.get("goals", 0) or 0
                total_duels = doc.get("total_duels", 0) or 0
                duels_won = doc.get("duels_won", 0) or 0

                await col.update_one(
                    {"playerID": player_id},
                    {"$set": {
                        "pass_accuracy": passes_completed / total_passes if total_passes > 0 else 0.0,
                        "shot_accuracy": goals / total_shots if total_shots > 0 else 0.0,
                        "duel_win_rate": duels_won / total_duels if total_duels > 0 else 0.0,
                    }},
                )
        except Exception as e:
            logger.error(f"Failed to persist player feature for {player_id}: {e}")

    async def process_event(self, event_data: dict):
        """
        Consume raw event, extract features into tensors, and persist to player_features.
        """
        match_id = event_data.get('match_id')
        event_type = event_data.get('type')

        if not match_id or not event_type:
            return

        # Resolve event type name (StatsBomb sends type as {"id": ..., "name": "Pass"})
        if isinstance(event_type, dict):
            event_type_name = event_type.get("name", "")
        else:
            event_type_name = str(event_type)

        # Resolve player_id
        player = event_data.get("player") or {}
        if isinstance(player, dict):
            player_id = str(player.get("id") or "")
        else:
            player_id = str(event_data.get("player_id") or "")

        try:
            # Apply feature engineering to create standardized tensors
            features = self.pipeline.process_event_to_features(event_data)

            if 'pass_tensor' in features:
                tensor = features['pass_tensor']
                # For Phase 2, this is a placeholder where you would invoke a PyTorch model:
                # pass_prob = self.model.predict(tensor)
                pass

            # Persist per-player feature increments to MongoDB
            if player_id:
                await self._persist_player_feature(player_id, event_type_name, event_data)

        except Exception as e:
            logger.error(f"Failed to extract features for event {event_type_name}: {e}")
