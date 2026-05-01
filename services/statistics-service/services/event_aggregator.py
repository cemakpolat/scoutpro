"""
Event Aggregator - Computes event-type-specific statistics
Implements Feed API event evaluation pattern from archive

Matches legacy architecture event classes:
- AerialEvent, PassEvent, ShotandGoalEvent, DuelEvent, TakeOnEvent
- CardEvent, FoulEvent, GoalkeeperEvent, BallControlEvent, TouchEvent
- AssistEvent
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from redis import Redis
from motor.motor_asyncio import AsyncIOMotorClient
import json

logger = logging.getLogger(__name__)


class EventAggregator:
    """Event-type-specific aggregation using MongoDB aggregation pipelines"""

    def __init__(self, db_client: AsyncIOMotorClient, redis_client: Redis):
        self.db = db_client
        self.redis = redis_client
        self.cache_ttl = 300  # 5 minutes for event aggregations

    # ==================== PASS EVENTS ====================
    
    async def get_pass_statistics(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None,
        include_per_90: bool = True
    ) -> Dict[str, Any]:
        """
        Aggregate pass event statistics
        Equivalent to legacy PassEvent class
        Analyzes Opta F24 pass events with qualifiers
        """
        cache_key = f"event:pass:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        filters = self._build_match_filters(player_id, team_id, competition_id, season_id)
        filters["type_name"] = "pass"

        # Simplified pipeline - start without complex $toDouble operations
        pipeline = [
            {"$match": filters},
            {
                "$group": {
                    "_id": "$player_id" if player_id else "$team_id",
                    "total_attempts": {"$sum": 1},
                    "forward_count": {"$sum": {"$cond": [{"$eq": [{"$getField": {"field": {"$literal": "56"}, "input": "$qualifiers"}}, "F"]}, 1, 0]}},
                    "backward_count": {"$sum": {"$cond": [{"$eq": [{"$getField": {"field": {"$literal": "56"}, "input": "$qualifiers"}}, "B"]}, 1, 0]}},
                    "lateral_count": {"$sum": {"$cond": [{"$in": [{"$getField": {"field": {"$literal": "56"}, "input": "$qualifiers"}}, ["L", "R"]]}, 1, 0]}},
                    "cross_count": {"$sum": {"$cond": [{"$gt": [{"$getField": {"field": {"$literal": "50"}, "input": "$qualifiers"}}, None]}, 1, 0]}},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total_attempts": 1,
                    "forward_passes": "$forward_count",
                    "backward_passes": "$backward_count",
                    "lateral_passes": "$lateral_count",
                    "crosses": "$cross_count",
                    "pass_length_avg": {"$literal": 0},
                }
            }
        ]

        try:
            result = await self.db.scoutpro.match_events.aggregate(pipeline).to_list(None)
            logger.info(f"Pass aggregation result: player_id={player_id}, team_id={team_id}, result={result}")
            
            if result and len(result) > 0:
                stats = result[0]
                await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats, default=str))
                return stats
            else:
                logger.warning(f"No pass results for player_id={player_id}, team_id={team_id}")
                return {
                    "total_attempts": 0,
                    "pass_length_avg": 0,
                    "forward_passes": 0,
                    "backward_passes": 0,
                    "lateral_passes": 0,
                    "crosses": 0
                }
        except Exception as e:
            logger.error(f"Error aggregating pass statistics: {e}", exc_info=True)
            return {}

    # ==================== AERIAL DUEL EVENTS ====================

    async def get_aerial_statistics(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Aggregate aerial duel statistics
        Equivalent to legacy AerialEvent class
        """
        cache_key = f"event:aerial:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        pipeline = [
            {
                "$match": {
                    "type_name": "aerial",
                    **self._build_match_filters(player_id, team_id, competition_id, season_id)
                }
            },
            {
                "$group": {
                    "_id": "$player_id" if player_id else "$team_id",
                    "total_duels": {"$sum": 1},
                    "won": {"$sum": {"$cond": ["$is_successful", 1, 0]}},
                    "lost": {"$sum": {"$cond": [{"$not": ["$is_successful"]}, 1, 0]}},
                    "won_in_attacking_half": {"$sum": {"$cond": [
                        {"$and": ["$is_successful", {"$gte": ["$location.x", 50]}]},
                        1, 0
                    ]}},
                    "won_in_defensive_half": {"$sum": {"$cond": [
                        {"$and": ["$is_successful", {"$lt": ["$location.x", 50]}]},
                        1, 0
                    ]}},
                }
            },
            {
                "$project": {
                    "total_duels": 1,
                    "won": 1,
                    "lost": 1,
                    "win_percentage": {
                        "$cond": [
                            {"$eq": ["$total_duels", 0]},
                            0,
                            {"$multiply": [{"$divide": ["$won", "$total_duels"]}, 100]}
                        ]
                    },
                    "won_in_attacking_half": 1,
                    "won_in_defensive_half": 1,
                }
            }
        ]

        try:
            result = await self.db.scoutpro.match_events.aggregate(pipeline).to_list(None)
            stats = result[0] if result else {}
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats))
            return stats
        except Exception as e:
            logger.error(f"Error aggregating aerial statistics: {e}")
            return {}

    # ==================== SHOT/GOAL EVENTS ====================

    async def get_shot_statistics(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Aggregate shot and goal statistics
        Equivalent to legacy ShotandGoalEvent class
        """
        cache_key = f"event:shot:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        pipeline = [
            {
                "$match": {
                    "type_name": {"$in": ["shot", "goal"]},
                    **self._build_match_filters(player_id, team_id, competition_id, season_id)
                }
            },
            {
                "$group": {
                    "_id": "$player_id" if player_id else "$team_id",
                    "total_shots": {"$sum": 1},
                    "goals": {"$sum": {"$cond": ["$is_goal", 1, 0]}},
                    "shots_on_target": {"$sum": {"$cond": ["$is_on_target", 1, 0]}},
                    "headed_shots": {"$sum": {"$cond": ["$is_head", 1, 0]}},
                    "left_foot_shots": {"$sum": {"$cond": ["$is_left_foot", 1, 0]}},
                    "right_foot_shots": {"$sum": {"$cond": ["$is_right_foot", 1, 0]}},
                    "shots_from_box": {"$sum": {"$cond": ["$is_in_box", 1, 0]}},
                    "shots_from_outside_box": {"$sum": {"$cond": [{"$not": ["$is_in_box"]}, 1, 0]}},
                }
            },
            {
                "$project": {
                    "total_shots": 1,
                    "goals": 1,
                    "shots_on_target": 1,
                    "conversion_rate": {
                        "$cond": [
                            {"$eq": ["$total_shots", 0]},
                            0,
                            {"$multiply": [{"$divide": ["$goals", "$total_shots"]}, 100]}
                        ]
                    },
                    "shot_accuracy": {
                        "$cond": [
                            {"$eq": ["$total_shots", 0]},
                            0,
                            {"$multiply": [{"$divide": ["$shots_on_target", "$total_shots"]}, 100]}
                        ]
                    },
                    "headed_shots": 1,
                    "left_foot_shots": 1,
                    "right_foot_shots": 1,
                    "shots_from_box": 1,
                    "shots_from_outside_box": 1,
                }
            }
        ]

        try:
            result = await self.db.scoutpro.match_events.aggregate(pipeline).to_list(None)
            stats = result[0] if result else {}
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats))
            return stats
        except Exception as e:
            logger.error(f"Error aggregating shot statistics: {e}")
            return {}

    # ==================== TACKLE/DUEL EVENTS ====================

    async def get_tackle_statistics(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Aggregate tackle and duel statistics
        Equivalent to legacy DuelEvent class
        """
        cache_key = f"event:tackle:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        pipeline = [
            {
                "$match": {
                    "type_name": {"$in": ["tackle", "duel", "50/50", "challenge"]},
                    **self._build_match_filters(player_id, team_id, competition_id, season_id)
                }
            },
            {
                "$group": {
                    "_id": "$player_id" if player_id else "$team_id",
                    "total_duels": {"$sum": 1},
                    "successful_tackles": {"$sum": {"$cond": ["$is_successful", 1, 0]}},
                    "failed_tackles": {"$sum": {"$cond": [{"$not": ["$is_successful"]}, 1, 0]}},
                    "by_type": {
                        "$push": {
                            "type": "$type_name",
                            "success": "$is_successful"
                        }
                    }
                }
            },
            {
                "$project": {
                    "total_duels": 1,
                    "successful_tackles": 1,
                    "failed_tackles": 1,
                    "tackle_success_rate": {
                        "$cond": [
                            {"$eq": ["$total_duels", 0]},
                            0,
                            {"$multiply": [{"$divide": ["$successful_tackles", "$total_duels"]}, 100]}
                        ]
                    },
                }
            }
        ]

        try:
            result = await self.db.scoutpro.match_events.aggregate(pipeline).to_list(None)
            stats = result[0] if result else {}
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats))
            return stats
        except Exception as e:
            logger.error(f"Error aggregating tackle statistics: {e}")
            return {}

    # ==================== DRIBBLE/TAKE-ON EVENTS ====================

    async def get_takeon_statistics(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Aggregate take-on/dribble statistics
        Equivalent to legacy TakeOnEvent class
        """
        cache_key = f"event:takeon:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        pipeline = [
            {
                "$match": {
                    "type_name": {"$in": ["take_on", "dribble"]},
                    **self._build_match_filters(player_id, team_id, competition_id, season_id)
                }
            },
            {
                "$group": {
                    "_id": "$player_id" if player_id else "$team_id",
                    "total_take_ons": {"$sum": 1},
                    "successful_take_ons": {"$sum": {"$cond": ["$is_successful", 1, 0]}},
                    "failed_take_ons": {"$sum": {"$cond": [{"$not": ["$is_successful"]}, 1, 0]}},
                }
            },
            {
                "$project": {
                    "total_take_ons": 1,
                    "successful_take_ons": 1,
                    "failed_take_ons": 1,
                    "take_on_success_rate": {
                        "$cond": [
                            {"$eq": ["$total_take_ons", 0]},
                            0,
                            {"$multiply": [{"$divide": ["$successful_take_ons", "$total_take_ons"]}, 100]}
                        ]
                    },
                }
            }
        ]

        try:
            result = await self.db.scoutpro.match_events.aggregate(pipeline).to_list(None)
            stats = result[0] if result else {}
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats))
            return stats
        except Exception as e:
            logger.error(f"Error aggregating take-on statistics: {e}")
            return {}

    # ==================== GOALKEEPER EVENTS ====================

    async def get_goalkeeper_statistics(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Aggregate goalkeeper-specific statistics
        Equivalent to legacy GoalkeeperEvent class
        """
        cache_key = f"event:goalkeeper:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        pipeline = [
            {
                "$match": {
                    "type_name": {"$in": ["save", "claim", "punch", "clearance", "keeper_throw"]},
                    **self._build_match_filters(player_id, team_id, competition_id, season_id)
                }
            },
            {
                "$group": {
                    "_id": "$player_id" if player_id else "$team_id",
                    "total_gk_actions": {"$sum": 1},
                    "saves": {"$sum": {"$cond": [{"$eq": ["$type_name", "save"]}, 1, 0]}},
                    "claims": {"$sum": {"$cond": [{"$eq": ["$type_name", "claim"]}, 1, 0]}},
                    "punches": {"$sum": {"$cond": [{"$eq": ["$type_name", "punch"]}, 1, 0]}},
                    "clearances": {"$sum": {"$cond": [{"$eq": ["$type_name", "clearance"]}, 1, 0]}},
                    "throws": {"$sum": {"$cond": [{"$eq": ["$type_name", "keeper_throw"]}, 1, 0]}},
                }
            }
        ]

        try:
            result = await self.db.scoutpro.match_events.aggregate(pipeline).to_list(None)
            stats = result[0] if result else {}
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats))
            return stats
        except Exception as e:
            logger.error(f"Error aggregating goalkeeper statistics: {e}")
            return {}

    # ==================== CARD EVENTS ====================

    async def get_card_statistics(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Aggregate card (yellow/red) statistics
        Equivalent to legacy CardEvent class
        """
        cache_key = f"event:card:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        pipeline = [
            {
                "$match": {
                    "type_name": "card",
                    **self._build_match_filters(player_id, team_id, competition_id, season_id)
                }
            },
            {
                "$group": {
                    "_id": "$player_id" if player_id else "$team_id",
                    "total_cards": {"$sum": 1},
                    "yellow_cards": {"$sum": {"$cond": ["$is_yellow", 1, 0]}},
                    "red_cards": {"$sum": {"$cond": ["$is_red", 1, 0]}},
                }
            }
        ]

        try:
            result = await self.db.scoutpro.match_events.aggregate(pipeline).to_list(None)
            stats = result[0] if result else {}
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats))
            return stats
        except Exception as e:
            logger.error(f"Error aggregating card statistics: {e}")
            return {}

    # ==================== FOUL EVENTS ====================

    async def get_foul_statistics(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Aggregate foul statistics
        Equivalent to legacy FoulEvent class
        """
        cache_key = f"event:foul:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        pipeline = [
            {
                "$match": {
                    "type_name": "foul",
                    **self._build_match_filters(player_id, team_id, competition_id, season_id)
                }
            },
            {
                "$group": {
                    "_id": "$player_id" if player_id else "$team_id",
                    "total_fouls": {"$sum": 1},
                    "fouls_committed": {"$sum": {"$cond": ["$is_committed", 1, 0]}},
                    "fouls_suffered": {"$sum": {"$cond": [{"$not": ["$is_committed"]}, 1, 0]}},
                }
            }
        ]

        try:
            result = await self.db.scoutpro.match_events.aggregate(pipeline).to_list(None)
            stats = result[0] if result else {}
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats))
            return stats
        except Exception as e:
            logger.error(f"Error aggregating foul statistics: {e}")
            return {}

    # ==================== ASSIST/KEY PASS EVENTS ====================

    async def get_assist_statistics(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Aggregate assist and key pass statistics
        Equivalent to legacy AssistEvent class
        """
        cache_key = f"event:assist:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        pipeline = [
            {
                "$match": {
                    "type_name": {"$in": ["pass", "cross"]},
                    "is_assist": True,
                    **self._build_match_filters(player_id, team_id, competition_id, season_id)
                }
            },
            {
                "$group": {
                    "_id": "$player_id" if player_id else "$team_id",
                    "total_assists": {"$sum": 1},
                    "assists_from_open_play": {"$sum": {"$cond": ["$is_open_play", 1, 0]}},
                    "assists_from_set_play": {"$sum": {"$cond": [{"$not": ["$is_open_play"]}, 1, 0]}},
                    "assists_from_corners": {"$sum": {"$cond": ["$is_corner", 1, 0]}},
                    "assists_from_crosses": {"$sum": {"$cond": ["$is_cross", 1, 0]}},
                }
            }
        ]

        try:
            result = await self.db.scoutpro.match_events.aggregate(pipeline).to_list(None)
            stats = result[0] if result else {}
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats))
            return stats
        except Exception as e:
            logger.error(f"Error aggregating assist statistics: {e}")
            return {}

    # ==================== BALL CONTROL EVENTS ====================

    async def get_ball_control_statistics(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Aggregate ball control statistics (touches, receptions)
        Equivalent to legacy BallControlEvent class
        """
        cache_key = f"event:ball_control:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        pipeline = [
            {
                "$match": {
                    "type_name": {"$in": ["touch", "reception", "ball_recovery"]},
                    **self._build_match_filters(player_id, team_id, competition_id, season_id)
                }
            },
            {
                "$group": {
                    "_id": "$player_id" if player_id else "$team_id",
                    "total_touches": {"$sum": 1},
                    "successful_receptions": {"$sum": {"$cond": [
                        {"$and": [{"$eq": ["$type_name", "reception"]}, "$is_successful"]},
                        1, 0
                    ]}},
                    "ball_recoveries": {"$sum": {"$cond": [{"$eq": ["$type_name", "ball_recovery"]}, 1, 0]}},
                }
            }
        ]

        try:
            result = await self.db.scoutpro.match_events.aggregate(pipeline).to_list(None)
            stats = result[0] if result else {}
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats))
            return stats
        except Exception as e:
            logger.error(f"Error aggregating ball control statistics: {e}")
            return {}

    # ==================== HELPER METHODS ====================

    def _build_match_filters(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Build MongoDB match filters from optional parameters"""
        filters = {}
        
        if player_id:
            try:
                filters["player_id"] = int(player_id) if isinstance(player_id, str) else player_id
            except (ValueError, TypeError):
                filters["player_id"] = player_id
        if team_id:
            try:
                filters["team_id"] = int(team_id) if isinstance(team_id, str) else team_id
            except (ValueError, TypeError):
                filters["team_id"] = team_id
        if competition_id:
            filters["competition_id"] = competition_id
        if season_id:
            filters["season_id"] = season_id
        
        return filters

    async def get_all_event_types(self) -> List[str]:
        """Get list of all event types available in the database"""
        cache_key = "event:types:all"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        try:
            types = await self.db.scoutpro.match_events.distinct("type_name")
            await self.redis.setex(cache_key, 3600, json.dumps(types))
            return types
        except Exception as e:
            logger.error(f"Error getting event types: {e}")
            return []

    async def clear_cache(self, pattern: str = "event:*"):
        """Clear event aggregation cache"""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
