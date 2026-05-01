"""
Match Service - Business Logic Layer
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import logging
from redis import Redis
from aiokafka import AIOKafkaProducer
import sys
sys.path.append('/app')
from shared.models.base import Match
from repository.interfaces import IMatchRepository

logger = logging.getLogger(__name__)


class MatchService:
    """Match service with caching and event publishing"""

    @staticmethod
    def _is_stale_cached_match(match_data: Dict[str, Any]) -> bool:
        status = str(match_data.get('status', '')).lower()
        home_team_id = str(match_data.get('home_team_id') or '').strip()
        away_team_id = str(match_data.get('away_team_id') or '').strip()
        home_team_name = str(match_data.get('home_team_name') or '').strip()
        away_team_name = str(match_data.get('away_team_name') or '').strip()

        if status == 'live' and (home_team_id in ('', '0') or away_team_id in ('', '0')):
            return True

        if status == 'live' and (not home_team_name or not away_team_name):
            return True

        return False

    def __init__(
        self,
        repository: IMatchRepository,
        redis_client: Redis,
        kafka_producer: Optional[AIOKafkaProducer] = None,
        cache_ttl: int = 60
    ):
        self.repository = repository
        self.redis = redis_client
        self.kafka = kafka_producer
        self.cache_ttl = cache_ttl

    async def get_match(self, match_id: str) -> Optional[Match]:
        """Get match by ID with caching"""
        try:
            cache_key = f"match:{match_id}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for match {match_id}")
                cached_match = json.loads(cached)
                if not self._is_stale_cached_match(cached_match):
                    return Match(**cached_match)

                logger.info("Ignoring stale cached match snapshot for %s", match_id)
                await self.redis.delete(cache_key)

            match = await self.repository.get_by_id(match_id)

            if match:
                # Shorter TTL for live matches
                ttl = self.cache_ttl if match.status != 'live' else self.cache_ttl // 2
                await self.redis.setex(
                    cache_key,
                    ttl,
                    match.json()
                )

            return match
        except Exception as e:
            logger.error(f"Error in get_match({match_id}): {e}")
            raise

    async def list_matches(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Match]:
        """List matches with filters"""
        try:
            filters = filters or {}

            cache_key = f"matches:list:{json.dumps(filters, sort_keys=True)}:{limit}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug("Cache hit for match list")
                return [Match(**m) for m in json.loads(cached)]

            matches = await self.repository.find_by_filters(filters, limit)

            if matches:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps([m.dict() for m in matches])
                )

            return matches
        except Exception as e:
            logger.error(f"Error in list_matches: {e}")
            raise

    async def get_team_matches(self, team_id: str, limit: int = 20) -> List[Match]:
        """Get matches for a team"""
        try:
            cache_key = f"matches:team:{team_id}:{limit}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for team {team_id} matches")
                return [Match(**m) for m in json.loads(cached)]

            matches = await self.repository.get_by_team(team_id, limit)

            if matches:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps([m.dict() for m in matches])
                )

            return matches
        except Exception as e:
            logger.error(f"Error in get_team_matches({team_id}): {e}")
            raise

    async def get_matches_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100
    ) -> List[Match]:
        """Get matches in date range"""
        try:
            matches = await self.repository.get_by_date_range(start_date, end_date, limit)
            return matches
        except Exception as e:
            logger.error(f"Error in get_matches_by_date_range: {e}")
            raise

    async def get_live_matches(self) -> List[Match]:
        """Get currently live matches (no caching for live data)"""
        try:
            matches = await self.repository.get_live_matches()
            return matches
        except Exception as e:
            logger.error(f"Error in get_live_matches: {e}")
            raise

    async def get_match_events(self, match_id: str) -> List[Dict[str, Any]]:
        """Get all events for a match"""
        try:
            cache_key = f"match:events:{match_id}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for match {match_id} events")
                return json.loads(cached)

            events = await self.repository.get_match_events(match_id)

            if events:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl // 2,
                    json.dumps(events)
                )

            return events
        except Exception as e:
            logger.error(f"Error in get_match_events({match_id}): {e}")
            raise

    async def create_match(self, match: Match) -> str:
        """Create new match and publish event"""
        try:
            match_id = await self.repository.create(match)

            await self._invalidate_list_cache()

            if self.kafka:
                await self._publish_event('match.created', {
                    'match_id': match_id,
                    'match': match.dict()
                })

            logger.info(f"Created match {match_id}")
            return match_id
        except Exception as e:
            logger.error(f"Error in create_match: {e}")
            raise

    async def update_match(self, match_id: str, match: Match) -> bool:
        """Update match and publish event"""
        try:
            success = await self.repository.update(match_id, match)

            if success:
                await self.redis.delete(f"match:{match_id}")
                await self._invalidate_list_cache()

                if self.kafka:
                    await self._publish_event('match.updated', {
                        'match_id': match_id,
                        'match': match.dict()
                    })

                logger.info(f"Updated match {match_id}")

            return success
        except Exception as e:
            logger.error(f"Error in update_match({match_id}): {e}")
            raise

    async def update_live_data(self, match_id: str, live_data: Dict[str, Any]) -> bool:
        """Update live match data"""
        try:
            success = await self.repository.update_live_data(match_id, live_data)

            if success:
                # Invalidate cache for live data
                await self.redis.delete(f"match:{match_id}")

                if self.kafka:
                    await self._publish_event('match.live_update', {
                        'match_id': match_id,
                        'data': live_data
                    })

                logger.debug(f"Updated live data for match {match_id}")

            return success
        except Exception as e:
            logger.error(f"Error in update_live_data({match_id}): {e}")
            raise

    async def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish event to Kafka"""
        try:
            if not self.kafka:
                return

            event = {
                'type': event_type,
                'data': data
            }

            await self.kafka.send(
                'match.events',
                value=json.dumps(event).encode('utf-8')
            )
            logger.debug(f"Published event: {event_type}")
        except Exception as e:
            logger.error(f"Error publishing event {event_type}: {e}")

    async def _invalidate_list_cache(self):
        """Invalidate all list caches"""
        try:
            cursor = 0
            pattern = "matches:list:*"

            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break

            logger.debug("Invalidated match list cache")
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
