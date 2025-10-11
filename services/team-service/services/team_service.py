"""
Team Service - Business Logic Layer
"""
from typing import Optional, List, Dict, Any
import json
import logging
from redis import Redis
from aiokafka import AIOKafkaProducer
import sys
sys.path.append('/app')
from shared.models.base import Team
from repository.interfaces import ITeamRepository

logger = logging.getLogger(__name__)


class TeamService:
    """Team service with caching and event publishing"""

    def __init__(
        self,
        repository: ITeamRepository,
        redis_client: Redis,
        kafka_producer: Optional[AIOKafkaProducer] = None,
        cache_ttl: int = 600
    ):
        self.repository = repository
        self.redis = redis_client
        self.kafka = kafka_producer
        self.cache_ttl = cache_ttl

    async def get_team(self, team_id: str) -> Optional[Team]:
        """Get team by ID with caching"""
        try:
            cache_key = f"team:{team_id}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for team {team_id}")
                return Team(**json.loads(cached))

            team = await self.repository.get_by_id(team_id)

            if team:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl,
                    team.json()
                )

            return team
        except Exception as e:
            logger.error(f"Error in get_team({team_id}): {e}")
            raise

    async def list_teams(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Team]:
        """List teams with filters"""
        try:
            filters = filters or {}

            cache_key = f"teams:list:{json.dumps(filters, sort_keys=True)}:{limit}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug("Cache hit for team list")
                return [Team(**t) for t in json.loads(cached)]

            teams = await self.repository.find_by_filters(filters, limit)

            if teams:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps([t.dict() for t in teams])
                )

            return teams
        except Exception as e:
            logger.error(f"Error in list_teams: {e}")
            raise

    async def search_teams(self, query: str, limit: int = 20) -> List[Team]:
        """Search teams by name"""
        try:
            cache_key = f"teams:search:{query}:{limit}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for search '{query}'")
                return [Team(**t) for t in json.loads(cached)]

            teams = await self.repository.search(query, limit)

            if teams:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl // 2,
                    json.dumps([t.dict() for t in teams])
                )

            return teams
        except Exception as e:
            logger.error(f"Error in search_teams('{query}'): {e}")
            raise

    async def get_squad(self, team_id: str) -> List[Dict[str, Any]]:
        """Get team squad with caching"""
        try:
            cache_key = f"team:squad:{team_id}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for team {team_id} squad")
                return json.loads(cached)

            squad = await self.repository.get_squad(team_id)

            if squad:
                await self.redis.setex(
                    cache_key,
                    self.cache_ttl // 2,
                    json.dumps(squad)
                )

            return squad
        except Exception as e:
            logger.error(f"Error in get_squad({team_id}): {e}")
            raise

    async def create_team(self, team: Team) -> str:
        """Create new team and publish event"""
        try:
            team_id = await self.repository.create(team)

            await self._invalidate_list_cache()

            if self.kafka:
                await self._publish_event('team.created', {
                    'team_id': team_id,
                    'team': team.dict()
                })

            logger.info(f"Created team {team_id}")
            return team_id
        except Exception as e:
            logger.error(f"Error in create_team: {e}")
            raise

    async def update_team(self, team_id: str, team: Team) -> bool:
        """Update team and publish event"""
        try:
            success = await self.repository.update(team_id, team)

            if success:
                await self.redis.delete(f"team:{team_id}")
                await self._invalidate_list_cache()

                if self.kafka:
                    await self._publish_event('team.updated', {
                        'team_id': team_id,
                        'team': team.dict()
                    })

                logger.info(f"Updated team {team_id}")

            return success
        except Exception as e:
            logger.error(f"Error in update_team({team_id}): {e}")
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
                'team.events',
                value=json.dumps(event).encode('utf-8')
            )
            logger.debug(f"Published event: {event_type}")
        except Exception as e:
            logger.error(f"Error publishing event {event_type}: {e}")

    async def _invalidate_list_cache(self):
        """Invalidate all list caches"""
        try:
            cursor = 0
            pattern = "teams:list:*"

            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break

            logger.debug("Invalidated team list cache")
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
