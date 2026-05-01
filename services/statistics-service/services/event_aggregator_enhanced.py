"""
Enhanced Event Aggregator - Phase 1 & 2 Enrichments
Implements Feed API patterns with regional analysis, qualifiers, and context awareness

Architecture:
- Uses Motor find() for guaranteed data access (no aggregation issues)
- Computes enrichments in Python for flexibility
- Regional zones (thirds, halves, box) for spatial analytics
- Qualifier extraction for pass types, foul contexts, etc.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from redis import Redis
from motor.motor_asyncio import AsyncIOMotorClient
import json
import math

logger = logging.getLogger(__name__)


class FieldZones:
    """Spatial field zones for regional analysis"""
    
    @staticmethod
    def get_region(x: float, y: float = None) -> str:
        """Get field region by x coordinate"""
        if x <= 33.3:
            return "defensive_third"
        elif x <= 66.6:
            return "middle_third"
        else:
            return "attacking_third"
    
    @staticmethod
    def get_half(x: float) -> str:
        """Get field half"""
        return "own_half" if x <= 50 else "opponent_half"
    
    @staticmethod
    def in_box(location: Dict) -> bool:
        """Check if location is in penalty box"""
        if not location or 'x' not in location or 'y' not in location:
            return False
        x, y = location['x'], location['y']
        return x >= 83.3 and 21.1 <= y <= 78.9
    
    @staticmethod
    def in_defensive_box(location: Dict) -> bool:
        """Check if location is in defensive box"""
        if not location or 'x' not in location or 'y' not in location:
            return False
        x, y = location['x'], location['y']
        return x <= 16.7 and 21.1 <= y <= 78.9


class QualifierExtractor:
    """Extract meaningful data from Opta qualifier system"""
    
    # Qualifier ID mappings
    PASS_DIRECTION = "56"          # F=Forward, B=Back, L/R=Lateral, S=Straight
    CROSS_INDICATOR = "50"          # Presence indicates cross
    LONG_PASS = "1"                # Presence indicates long pass
    THROUGH_BALL = "4"             # Presence indicates through ball
    CHIPPED_PASS = "155"           # Presence indicates chipped pass
    CORNER_CROSS = "6"             # Presence indicates corner cross
    THROW_IN = "107"               # Presence indicates throw-in
    GOAL_KICK = "123"              # Presence indicates goal kick
    
    # Set piece indicators
    FREE_KICK = "24"               # Direct free kick
    FREE_KICK_INDIRECT = "25"      # Indirect free kick
    CORNER = "26"                  # Corner
    
    # Shot qualifiers
    BIG_CHANCE = "87"              # Big chance indicator
    PENALTY = "39"                 # Penalty indicator
    BLOCKED_SHOT = "355"           # Blocked shot
    
    # Defensive qualifiers
    DANGEROUS_FOUL = "13"          # Dangerous foul
    HAND_FOUL = "265"              # Hand foul
    PENALTY_FOUL = "152"           # Foul in penalty area
    
    # Duel qualifiers
    DUEL_DIRECTION = "233"         # Distance in duel
    DUEL_OUTCOME = "285"           # Won/lost indicator
    
    @staticmethod
    def has_qualifier(qualifiers: Dict, qualifier_id: str) -> bool:
        """Check if qualifier exists and has value"""
        return qualifier_id in qualifiers and qualifiers[qualifier_id]
    
    @staticmethod
    def get_pass_direction(qualifiers: Dict) -> str:
        """Extract pass direction from qualifier"""
        direction = qualifiers.get("56", "")
        return {
            "F": "forward",
            "B": "backward",
            "L": "lateral",
            "R": "lateral",
            "S": "straight"
        }.get(direction, "unknown")
    
    @staticmethod
    def get_all_pass_types(qualifiers: Dict) -> List[str]:
        """Extract all applicable pass type qualifiers"""
        types = []
        if QualifierExtractor.has_qualifier(qualifiers, "1"):
            types.append("long_pass")
        if QualifierExtractor.has_qualifier(qualifiers, "4"):
            types.append("through_ball")
        if QualifierExtractor.has_qualifier(qualifiers, "155"):
            types.append("chipped_pass")
        if QualifierExtractor.has_qualifier(qualifiers, "50"):
            types.append("cross")
        if QualifierExtractor.has_qualifier(qualifiers, "6"):
            types.append("corner_cross")
        if QualifierExtractor.has_qualifier(qualifiers, "107"):
            types.append("throw_in")
        if QualifierExtractor.has_qualifier(qualifiers, "123"):
            types.append("goal_kick")
        
        # Set piece indicators
        if QualifierExtractor.has_qualifier(qualifiers, "24"):
            types.append("free_kick_direct")
        if QualifierExtractor.has_qualifier(qualifiers, "25"):
            types.append("free_kick_indirect")
        if QualifierExtractor.has_qualifier(qualifiers, "26"):
            types.append("from_corner")
        
        return types


class EnhancedEventAggregator:
    """Enhanced event aggregation with enrichments using find() + Python"""

    def __init__(self, db_client: AsyncIOMotorClient, redis_client: Redis):
        self.db = db_client
        self.redis = redis_client
        self.cache_ttl = 300  # 5 minutes
        self.zones = FieldZones()
        self.qualifiers = QualifierExtractor()

    def _build_match_filters(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Build MongoDB match filters from parameters"""
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
            try:
                filters["competition_id"] = int(competition_id) if isinstance(competition_id, str) else competition_id
            except (ValueError, TypeError):
                pass
        
        if season_id:
            try:
                filters["season_id"] = int(season_id) if isinstance(season_id, str) else season_id
            except (ValueError, TypeError):
                pass
        
        return filters

    # ==================== PASS STATISTICS (ENHANCED) ====================

    async def get_pass_statistics_enhanced(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enhanced pass statistics with:
        - Regional breakdown (thirds, halves)
        - Pass type classification
        - Context (open play vs set piece)
        """
        cache_key = f"event:pass:enhanced:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        filters = self._build_match_filters(player_id, team_id, competition_id, season_id)
        filters["type_name"] = "pass"

        try:
            docs = await self.db.scoutpro.match_events.find(filters).to_list(None)
            
            # Initialize aggregation buckets
            stats = {
                "total_passes": len(docs),
                "by_region": {
                    "defensive_third": {"attempts": 0, "forward": 0, "backward": 0, "lateral": 0},
                    "middle_third": {"attempts": 0, "forward": 0, "backward": 0, "lateral": 0},
                    "attacking_third": {"attempts": 0, "forward": 0, "backward": 0, "lateral": 0},
                },
                "by_half": {
                    "own_half": {"attempts": 0},
                    "opponent_half": {"attempts": 0},
                },
                "pass_types": {
                    "long_passes": 0,
                    "through_balls": 0,
                    "crosses": 0,
                    "corner_crosses": 0,
                    "chipped_passes": 0,
                    "throw_ins": 0,
                    "goal_kicks": 0,
                },
                "set_piece_passes": 0,
                "open_play_passes": 0,
                "passes_in_box": 0,
                "passes_into_box": 0,
                "crosses_completed": 0,
            }
            
            # Process each pass event
            for doc in docs:
                location = doc.get("location", {})
                qualifiers = doc.get("qualifiers", {})
                
                # Regional analysis
                if location and "x" in location:
                    x = location["x"]
                    region = self.zones.get_region(x)
                    stats["by_region"][region]["attempts"] += 1
                    
                    # Direction breakdown by region
                    direction = self.qualifiers.get_pass_direction(qualifiers)
                    if direction in ["forward", "backward", "lateral"]:
                        stats["by_region"][region][direction] += 1
                    
                    # Half analysis
                    half = self.zones.get_half(x)
                    stats["by_half"][half]["attempts"] += 1
                    
                    # Box analysis
                    if self.zones.in_box(location):
                        stats["passes_in_box"] += 1
                
                # Pass type extraction
                pass_types = self.qualifiers.get_all_pass_types(qualifiers)
                for pass_type in pass_types:
                    if pass_type in stats["pass_types"]:
                        stats["pass_types"][pass_type] += 1
                
                # Set piece vs open play
                is_set_piece = any(t in pass_types for t in [
                    "free_kick_direct", "free_kick_indirect", "from_corner", 
                    "throw_in", "goal_kick", "corner_cross"
                ])
                if is_set_piece:
                    stats["set_piece_passes"] += 1
                else:
                    stats["open_play_passes"] += 1
                
                # Cross tracking
                if self.qualifiers.has_qualifier(qualifiers, "50"):
                    if doc.get("is_successful"):
                        stats["crosses_completed"] += 1
            
            # Calculate completion rates
            stats["open_play_completion"] = (
                stats["open_play_passes"] / stats["total_passes"] * 100
                if stats["total_passes"] > 0 else 0
            )
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats, default=str))
            return stats
            
        except Exception as e:
            logger.error(f"Error in enhanced pass statistics: {e}", exc_info=True)
            return {"error": str(e), "total_passes": 0}

    # ==================== SHOT STATISTICS (ENHANCED) ====================

    async def get_shot_statistics_enhanced(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enhanced shot statistics with:
        - Location analysis (box vs outside)
        - Goal tracking
        - Shot quality metrics
        """
        cache_key = f"event:shot:enhanced:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        filters = self._build_match_filters(player_id, team_id, competition_id, season_id)
        filters["type_name"] = "shot"

        try:
            docs = await self.db.scoutpro.match_events.find(filters).to_list(None)
            
            stats = {
                "total_shots": len(docs),
                "goals": 0,
                "shots_on_target": 0,
                "shots_off_target": 0,
                "blocked_shots": 0,
                
                "by_location": {
                    "inside_box": 0,
                    "outside_box": 0,
                    "inside_box_goals": 0,
                    "outside_box_goals": 0,
                },
                
                "by_foot": {
                    "right_foot": 0,
                    "left_foot": 0,
                    "header": 0,
                    "other": 0,
                },
                
                "big_chances": 0,
                "big_chance_conversion": 0,
                "penalty_shots": 0,
                "penalty_goals": 0,
                
                "avg_distance_to_goal": 0,
                "shot_accuracy": 0,
            }
            
            distances = []
            
            # Process each shot
            for doc in docs:
                location = doc.get("location", {})
                qualifiers = doc.get("qualifiers", {})
                is_goal = doc.get("is_goal", False)
                
                # Goal tracking
                if is_goal:
                    stats["goals"] += 1
                
                # Location analysis
                if location and "x" in location and "y" in location:
                    x, y = location["x"], location["y"]
                    
                    # Distance to goal line
                    dist_to_goal = 100 - x  # Approximate
                    distances.append(dist_to_goal)
                    
                    if self.zones.in_box(location):
                        stats["by_location"]["inside_box"] += 1
                        if is_goal:
                            stats["by_location"]["inside_box_goals"] += 1
                    else:
                        stats["by_location"]["outside_box"] += 1
                        if is_goal:
                            stats["by_location"]["outside_box_goals"] += 1
                
                # Shot type analysis
                shot_type = qualifiers.get("56", "")  # Direction/body part
                if "right" in str(shot_type).lower():
                    stats["by_foot"]["right_foot"] += 1
                elif "left" in str(shot_type).lower():
                    stats["by_foot"]["left_foot"] += 1
                elif "head" in str(shot_type).lower():
                    stats["by_foot"]["header"] += 1
                
                # Big chance indicator
                if self.qualifiers.has_qualifier(qualifiers, "87"):
                    stats["big_chances"] += 1
                    if is_goal:
                        stats["big_chance_conversion"] += 1
                
                # Penalty tracking
                if self.qualifiers.has_qualifier(qualifiers, "39"):
                    stats["penalty_shots"] += 1
                    if is_goal:
                        stats["penalty_goals"] += 1
            
            # Calculate rates
            if stats["total_shots"] > 0:
                stats["shot_accuracy"] = stats["goals"] / stats["total_shots"] * 100
            
            if stats["big_chances"] > 0:
                stats["big_chance_conversion"] = stats["big_chance_conversion"] / stats["big_chances"] * 100
            
            if distances:
                stats["avg_distance_to_goal"] = sum(distances) / len(distances)
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats, default=str))
            return stats
            
        except Exception as e:
            logger.error(f"Error in enhanced shot statistics: {e}", exc_info=True)
            return {"error": str(e), "total_shots": 0}

    # ==================== DUEL STATISTICS (ENHANCED) ====================

    async def get_duel_statistics_enhanced(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enhanced duel statistics with:
        - Success rate tracking
        - Regional breakdown
        """
        cache_key = f"event:duel:enhanced:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        filters = self._build_match_filters(player_id, team_id, competition_id, season_id)
        filters["type_name"] = "duel"

        try:
            docs = await self.db.scoutpro.match_events.find(filters).to_list(None)
            
            stats = {
                "total_duels": len(docs),
                "duels_won": 0,
                "duels_lost": 0,
                "duel_success_rate": 0,
                
                "by_region": {
                    "defensive_third": 0,
                    "middle_third": 0,
                    "attacking_third": 0,
                },
                
                "by_half": {
                    "own_half": 0,
                    "opponent_half": 0,
                },
            }
            
            # Process duels
            for doc in docs:
                location = doc.get("location", {})
                
                # Success tracking
                if doc.get("is_successful"):
                    stats["duels_won"] += 1
                else:
                    stats["duels_lost"] += 1
                
                # Regional breakdown
                if location and "x" in location:
                    x = location["x"]
                    region = self.zones.get_region(x)
                    stats["by_region"][region] += 1
                    
                    half = self.zones.get_half(x)
                    stats["by_half"][half] += 1
            
            # Calculate success rate
            if stats["total_duels"] > 0:
                stats["duel_success_rate"] = stats["duels_won"] / stats["total_duels"] * 100
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats, default=str))
            return stats
            
        except Exception as e:
            logger.error(f"Error in enhanced duel statistics: {e}", exc_info=True)
            return {"error": str(e), "total_duels": 0}

    # ==================== TACKLE STATISTICS (ENHANCED) ====================

    async def get_tackle_statistics_enhanced(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enhanced tackle statistics with regional analysis
        """
        cache_key = f"event:tackle:enhanced:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        filters = self._build_match_filters(player_id, team_id, competition_id, season_id)
        filters["type_name"] = "tackle"

        try:
            docs = await self.db.scoutpro.match_events.find(filters).to_list(None)
            
            stats = {
                "total_tackles": len(docs),
                "successful_tackles": 0,
                "tackle_success_rate": 0,
                
                "by_region": {
                    "defensive_third": 0,
                    "middle_third": 0,
                    "attacking_third": 0,
                },
                
                "by_direction": {
                    "forward": 0,
                    "backward": 0,
                    "lateral": 0,
                },
            }
            
            # Process tackles
            for doc in docs:
                location = doc.get("location", {})
                qualifiers = doc.get("qualifiers", {})
                
                # Success tracking
                if doc.get("is_successful"):
                    stats["successful_tackles"] += 1
                
                # Regional breakdown
                if location and "x" in location:
                    x = location["x"]
                    region = self.zones.get_region(x)
                    stats["by_region"][region] += 1
                
                # Direction from qualifiers
                direction = self.qualifiers.get_pass_direction(qualifiers)
                if direction in stats["by_direction"]:
                    stats["by_direction"][direction] += 1
            
            # Calculate success rate
            if stats["total_tackles"] > 0:
                stats["tackle_success_rate"] = stats["successful_tackles"] / stats["total_tackles"] * 100
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats, default=str))
            return stats
            
        except Exception as e:
            logger.error(f"Error in enhanced tackle statistics: {e}", exc_info=True)
            return {"error": str(e), "total_tackles": 0}

    # ==================== BALL CONTROL STATISTICS ====================

    async def get_ball_control_statistics_enhanced(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Ball control/touch statistics with regional analysis
        """
        cache_key = f"event:ball_control:enhanced:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        filters = self._build_match_filters(player_id, team_id, competition_id, season_id)
        filters["type_name"] = "ball_control"

        try:
            docs = await self.db.scoutpro.match_events.find(filters).to_list(None)
            
            stats = {
                "total_touches": len(docs),
                "successful_touches": 0,
                "touch_accuracy": 0,
                
                "by_region": {
                    "defensive_third": 0,
                    "middle_third": 0,
                    "attacking_third": 0,
                },
                
                "by_half": {
                    "own_half": 0,
                    "opponent_half": 0,
                },
                
                "touches_in_box": 0,
            }
            
            # Process touches
            for doc in docs:
                location = doc.get("location", {})
                
                # Success tracking
                if doc.get("is_successful"):
                    stats["successful_touches"] += 1
                
                # Regional breakdown
                if location and "x" in location:
                    x = location["x"]
                    region = self.zones.get_region(x)
                    stats["by_region"][region] += 1
                    
                    half = self.zones.get_half(x)
                    stats["by_half"][half] += 1
                    
                    if self.zones.in_box(location):
                        stats["touches_in_box"] += 1
            
            # Calculate accuracy
            if stats["total_touches"] > 0:
                stats["touch_accuracy"] = stats["successful_touches"] / stats["total_touches"] * 100
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats, default=str))
            return stats
            
        except Exception as e:
            logger.error(f"Error in ball control statistics: {e}", exc_info=True)
            return {"error": str(e), "total_touches": 0}

    # ==================== FOUL STATISTICS ====================

    async def get_foul_statistics_enhanced(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enhanced foul statistics with type breakdown
        """
        cache_key = f"event:foul:enhanced:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        filters = self._build_match_filters(player_id, team_id, competition_id, season_id)
        filters["type_name"] = "foul"

        try:
            docs = await self.db.scoutpro.match_events.find(filters).to_list(None)
            
            stats = {
                "total_fouls": len(docs),
                "dangerous_fouls": 0,
                "handball_fouls": 0,
                "penalty_fouls": 0,
                
                "by_region": {
                    "defensive_third": 0,
                    "middle_third": 0,
                    "attacking_third": 0,
                },
                
                "in_penalty_box": 0,
            }
            
            # Process fouls
            for doc in docs:
                location = doc.get("location", {})
                qualifiers = doc.get("qualifiers", {})
                
                # Foul type analysis
                if self.qualifiers.has_qualifier(qualifiers, "13"):
                    stats["dangerous_fouls"] += 1
                if self.qualifiers.has_qualifier(qualifiers, "265"):
                    stats["handball_fouls"] += 1
                if self.qualifiers.has_qualifier(qualifiers, "152"):
                    stats["penalty_fouls"] += 1
                
                # Regional breakdown
                if location and "x" in location:
                    x = location["x"]
                    region = self.zones.get_region(x)
                    stats["by_region"][region] += 1
                    
                    if self.zones.in_box(location) or self.zones.in_defensive_box(location):
                        stats["in_penalty_box"] += 1
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats, default=str))
            return stats
            
        except Exception as e:
            logger.error(f"Error in foul statistics: {e}", exc_info=True)
            return {"error": str(e), "total_fouls": 0}

    # ==================== TAKE-ON STATISTICS ====================

    async def get_takeon_statistics_enhanced(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enhanced take-on/dribble statistics with regional analysis
        """
        cache_key = f"event:takeon:enhanced:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        filters = self._build_match_filters(player_id, team_id, competition_id, season_id)
        filters["type_name"] = "take_on"

        try:
            docs = await self.db.scoutpro.match_events.find(filters).to_list(None)
            
            stats = {
                "total_take_ons": len(docs),
                "successful_take_ons": 0,
                "take_on_success_rate": 0,
                
                "by_region": {
                    "defensive_third": 0,
                    "middle_third": 0,
                    "attacking_third": 0,
                },
                
                "in_own_half": 0,
                "in_opponent_half": 0,
                "in_box": 0,
                "into_box": 0,
            }
            
            # Process take-ons
            for doc in docs:
                location = doc.get("location", {})
                
                # Success tracking
                if doc.get("is_successful"):
                    stats["successful_take_ons"] += 1
                
                # Regional breakdown
                if location and "x" in location:
                    x = location["x"]
                    region = self.zones.get_region(x)
                    stats["by_region"][region] += 1
                    
                    # Half analysis
                    if x <= 50:
                        stats["in_own_half"] += 1
                    else:
                        stats["in_opponent_half"] += 1
                    
                    # Box analysis
                    if self.zones.in_box(location):
                        stats["in_box"] += 1
            
            # Calculate success rate
            if stats["total_take_ons"] > 0:
                stats["take_on_success_rate"] = stats["successful_take_ons"] / stats["total_take_ons"] * 100
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats, default=str))
            return stats
            
        except Exception as e:
            logger.error(f"Error in take-on statistics: {e}", exc_info=True)
            return {"error": str(e), "total_take_ons": 0}
    # ==================== BALL RECOVERY STATISTICS ====================

    async def get_ball_recovery_statistics_enhanced(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Ball recovery statistics with regional breakdown
        """
        cache_key = f"event:recovery:enhanced:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        filters = self._build_match_filters(player_id, team_id, competition_id, season_id)
        filters["type_name"] = {"$in": ["ball recovery", "recovery"]}

        try:
            docs = await self.db.scoutpro.match_events.find(filters).to_list(None)
            
            stats = {
                "total_recoveries": len(docs),
                
                "by_region": {
                    "defensive_third": 0,
                    "middle_third": 0,
                    "attacking_third": 0,
                },
                
                "by_half": {
                    "own_half": 0,
                    "opponent_half": 0,
                },
            }
            
            for doc in docs:
                location = doc.get("location", {})
                if location and "x" in location:
                    x = location["x"]
                    region = self.zones.get_region(x)
                    stats["by_region"][region] += 1
                    
                    half = self.zones.get_half(x)
                    stats["by_half"][half] += 1
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats, default=str))
            return stats
            
        except Exception as e:
            logger.error(f"Error in ball recovery statistics: {e}", exc_info=True)
            return {"error": str(e), "total_recoveries": 0}

    # ==================== INTERCEPTION STATISTICS ====================

    async def get_interception_statistics_enhanced(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Interception statistics with regional breakdown
        """
        cache_key = f"event:interception:enhanced:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        filters = self._build_match_filters(player_id, team_id, competition_id, season_id)
        filters["type_name"] = "interception"

        try:
            docs = await self.db.scoutpro.match_events.find(filters).to_list(None)
            
            stats = {
                "total_interceptions": len(docs),
                
                "by_region": {
                    "defensive_third": 0,
                    "middle_third": 0,
                    "attacking_third": 0,
                },
                
                "by_half": {
                    "own_half": 0,
                    "opponent_half": 0,
                },
            }
            
            for doc in docs:
                location = doc.get("location", {})
                if location and "x" in location:
                    x = location["x"]
                    region = self.zones.get_region(x)
                    stats["by_region"][region] += 1
                    
                    half = self.zones.get_half(x)
                    stats["by_half"][half] += 1
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats, default=str))
            return stats
            
        except Exception as e:
            logger.error(f"Error in interception statistics: {e}", exc_info=True)
            return {"error": str(e), "total_interceptions": 0}

    # ==================== GOALKEEPER STATISTICS ====================

    async def get_goalkeeper_statistics_enhanced(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Goalkeeper statistics tracking saves and distribution
        """
        cache_key = f"event:goalkeeper:enhanced:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        filters = self._build_match_filters(player_id, team_id, competition_id, season_id)
        filters["type_name"] = {"$in": ["goalkeeper", "goalkeeper_save", "keeper sweeper"]}

        try:
            docs = await self.db.scoutpro.match_events.find(filters).to_list(None)
            
            stats = {
                "total_events": len(docs),
                "saves": 0,
                "claims": 0,
                "punches": 0,
                "smothers": 0,
                "sweeper_actions": 0,
                "distribution_events": 0,
            }
            
            for doc in docs:
                event_type = doc.get("type_name")
                qualifiers = doc.get("qualifiers", {})
                
                if event_type == "goalkeeper_save" or (event_type == "goalkeeper" and self.qualifiers.has_qualifier(qualifiers, "82")): # 82 inside opta might mean save
                    stats["saves"] += 1
                elif event_type == "keeper sweeper":
                    stats["sweeper_actions"] += 1
                
                if self.qualifiers.has_qualifier(qualifiers, "11"): # 11 usually means claim
                    stats["claims"] += 1
                if self.qualifiers.has_qualifier(qualifiers, "41"): # 41 usually means punch
                    stats["punches"] += 1
                if self.qualifiers.has_qualifier(qualifiers, "10"): # distribution?
                    stats["distribution_events"] += 1
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats, default=str))
            return stats
            
        except Exception as e:
            logger.error(f"Error in goalkeeper statistics: {e}", exc_info=True)
            return {"error": str(e), "total_events": 0}

    # ==================== CREATIVE STATISTICS (EVENT LINKING) ====================

    async def get_creative_statistics_enhanced(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Creative statistics finding passes leading to shots or goals
        """
        cache_key = f"event:creative:enhanced:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # To find key passes / assists, we can look for passes that have the key pass or assist qualifier, OR we find shots and link back
        # Let's use qualifiers for Key Pass (210) and Assist (211), OR just return overall creative metrics
        filters = self._build_match_filters(player_id, team_id, competition_id, season_id)
        filters["type_name"] = "pass"

        try:
            docs = await self.db.scoutpro.match_events.find(filters).to_list(None)
            
            stats = {
                "key_passes": 0,
                "assists": 0,
                "chances_created": 0
            }
            
            for doc in docs:
                qualifiers = doc.get("qualifiers", {})
                
                # Check for assist (211) and key pass (210) or similar Opta ones
                has_assist = self.qualifiers.has_qualifier(qualifiers, "211")
                has_key_pass = self.qualifiers.has_qualifier(qualifiers, "210")
                
                if has_assist:
                    stats["assists"] += 1
                    stats["chances_created"] += 1
                elif has_key_pass:
                    stats["key_passes"] += 1
                    stats["chances_created"] += 1
                elif doc.get("is_assist"): # Alternative schema check
                    stats["assists"] += 1
                    stats["chances_created"] += 1
                elif doc.get("is_key_pass"): 
                    stats["key_passes"] += 1
                    stats["chances_created"] += 1
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats, default=str))
            return stats
            
        except Exception as e:
            logger.error(f"Error in creative statistics: {e}", exc_info=True)
            return {"error": str(e), "chances_created": 0}

    # ==================== PHASE 3 ENRICHMENTS ====================

    async def get_spatial_density_heatmap(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None,
        event_type: Optional[str] = None,
        grid_cols: int = 10,
        grid_rows: int = 10
    ) -> Dict[str, Any]:
        """
        Generate a spatial density heatmap for events.
        Divides the pitch (100x100) into a grid and counts events in each cell.
        """
        cache_key = f"event:heatmap:{player_id}:{team_id}:{competition_id}:{season_id}:{event_type}:{grid_cols}:{grid_rows}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        filters = self._build_match_filters(player_id, team_id, competition_id, season_id)
        if event_type:
            filters["type_name"] = event_type

        try:
            docs = await self.db.scoutpro.match_events.find(filters).to_list(None)
            
            grid = [[0 for _ in range(grid_rows)] for _ in range(grid_cols)]
            x_step = 100.0 / grid_cols
            y_step = 100.0 / grid_rows
            
            total_events = 0

            for doc in docs:
                location = doc.get("location", {})
                if location and "x" in location and "y" in location:
                    x, y = location["x"], location["y"]
                    # Boundary protection
                    col = min(int(x / x_step), grid_cols - 1)
                    row = min(int(y / y_step), grid_rows - 1)
                    grid[col][row] += 1
                    total_events += 1

            stats = {
                "total_events": total_events,
                "grid_cols": grid_cols,
                "grid_rows": grid_rows,
                "matrix": grid
            }
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats, default=str))
            return stats
            
        except Exception as e:
            logger.error(f"Error in generating heatmap: {e}", exc_info=True)
            return {"error": str(e), "total_events": 0}

    async def get_player_composite_index(
        self,
        player_id: str,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate an overall player rating/index based on aggregated stats.
        Combines passing, shooting, duels, etc. into a single score.
        """
        cache_key = f"event:composite:{player_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
            
        try:
            passes = await self.get_pass_statistics_enhanced(player_id=player_id, competition_id=competition_id, season_id=season_id)
            shots = await self.get_shot_statistics_enhanced(player_id=player_id, competition_id=competition_id, season_id=season_id)
            duels = await self.get_duel_statistics_enhanced(player_id=player_id, competition_id=competition_id, season_id=season_id)
            
            # Simple weighting mechanism for composite score
            # These weights would need tuning in a real system
            pass_score = (passes.get("open_play_completion", 0) / 100.0) * min(passes.get("total_passes", 0) / 50.0, 1.0) * 30
            shot_score = (shots.get("shot_accuracy", 0) / 100.0) * min(shots.get("total_shots", 0) / 5.0, 1.0) * 30
            duel_score = (duels.get("duel_success_rate", 0) / 100.0) * min(duels.get("total_duels", 0) / 15.0, 1.0) * 40
            
            # Additional boost for goals
            goal_boost = min(shots.get("goals", 0) * 5, 20)
            
            overall_index = min(max(pass_score + shot_score + duel_score + goal_boost, 0), 100)
            
            stats = {
                "player_id": player_id,
                "composite_index": round(overall_index, 2),
                "components": {
                    "passing_contribution": round(pass_score, 2),
                    "shooting_contribution": round(shot_score + goal_boost, 2),
                    "duel_contribution": round(duel_score, 2)
                }
            }
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats, default=str))
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating composite index: {e}", exc_info=True)
            return {"error": str(e), "composite_index": 0}

    async def get_expected_metrics(
        self,
        player_id: Optional[str] = None,
        team_id: Optional[str] = None,
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate expected metrics (xG, xA) from enriched events.
        """
        cache_key = f"event:expected:{player_id}:{team_id}:{competition_id}:{season_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        filters = self._build_match_filters(player_id, team_id, competition_id, season_id)
        # Get shots and passes to extract xG and xA
        filters["type_name"] = {"$in": ["shot", "pass"]}

        try:
            docs = await self.db.scoutpro.match_events.find(filters).to_list(None)
            
            stats = {
                "total_xg": 0.0,
                "total_xa": 0.0,
                "shots_with_xg": 0,
                "passes_with_xa": 0
            }
            
            for doc in docs:
                t_name = doc.get("type_name")
                xg = doc.get("analytical_xg")
                xa = doc.get("analytical_xa") # Assuming similar field for xA
                
                if t_name == "shot" and xg is not None:
                    stats["total_xg"] += float(xg)
                    stats["shots_with_xg"] += 1
                    
                if t_name == "pass" and xa is not None:
                    stats["total_xa"] += float(xa)
                    stats["passes_with_xa"] += 1

            stats["total_xg"] = round(stats["total_xg"], 3)
            stats["total_xa"] = round(stats["total_xa"], 3)
            
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(stats, default=str))
            return stats
            
        except Exception as e:
            logger.error(f"Error extracting expected metrics: {e}", exc_info=True)
            return {"error": str(e), "total_xg": 0.0, "total_xa": 0.0}

    async def get_player_similarity(
        self,
        player_id: str,
        target_player_ids: List[str],
        competition_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate similarity score between a primary player and target players based on a stat vector.
        """
        try:
            primary_stats = await self.get_player_composite_index(player_id, competition_id, season_id)
            if "error" in primary_stats:
                return primary_stats
                
            p_comp = primary_stats.get("components", {})
            p_vec = [
                p_comp.get("passing_contribution", 0),
                p_comp.get("shooting_contribution", 0),
                p_comp.get("duel_contribution", 0)
            ]
            
            p_mag = math.sqrt(sum(v*v for v in p_vec)) or 1.0
            
            similarities = []
            for t_id in target_player_ids:
                t_stats = await self.get_player_composite_index(t_id, competition_id, season_id)
                if "error" in t_stats:
                    continue
                    
                t_comp = t_stats.get("components", {})
                t_vec = [
                    t_comp.get("passing_contribution", 0),
                    t_comp.get("shooting_contribution", 0),
                    t_comp.get("duel_contribution", 0)
                ]
                
                t_mag = math.sqrt(sum(v*v for v in t_vec)) or 1.0
                dot = sum(p*t for p, t in zip(p_vec, t_vec))
                
                cosine_sim = dot / (p_mag * t_mag)
                similarities.append({
                    "player_id": t_id,
                    "similarity_score": round(cosine_sim * 100, 2),
                    "composite_index": t_stats.get("composite_index")
                })
                
            similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            return {
                "base_player_id": player_id,
                "base_composite_index": primary_stats.get("composite_index"),
                "similar_players": similarities
            }
            
        except Exception as e:
            logger.error(f"Error calculating player similarity: {e}", exc_info=True)
            return {"error": str(e)}
