"""
Elasticsearch client for search operations
"""
import logging
from typing import List, Dict, Any, Optional
from elasticsearch import AsyncElasticsearch

logger = logging.getLogger(__name__)


class SearchClient:
    """Elasticsearch search client"""

    def __init__(self, es_url: str):
        self.es = AsyncElasticsearch([es_url])

    async def search_players(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        size: int = 20
    ) -> List[Dict[str, Any]]:
        """Search players"""
        try:
            # Build search query
            search_query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["name^3", "first^2", "last^2", "position"],
                                    "fuzziness": "AUTO"
                                }
                            }
                        ]
                    }
                },
                "size": size
            }

            # Add filters
            if filters:
                filter_clauses = []
                if 'position' in filters:
                    filter_clauses.append({"term": {"position": filters['position']}})
                if 'club' in filters:
                    filter_clauses.append({"term": {"club": filters['club']}})

                if filter_clauses:
                    search_query["query"]["bool"]["filter"] = filter_clauses

            # Execute search
            response = await self.es.search(
                index="players",
                body=search_query
            )

            # Extract results
            hits = response.get('hits', {}).get('hits', [])
            results = [hit['_source'] for hit in hits]

            return results

        except Exception as e:
            logger.error(f"Error searching players: {e}")
            return []

    async def search_teams(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        size: int = 20
    ) -> List[Dict[str, Any]]:
        """Search teams"""
        try:
            search_query = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["name^3", "shortName^2", "country"],
                        "fuzziness": "AUTO"
                    }
                },
                "size": size
            }

            response = await self.es.search(
                index="teams",
                body=search_query
            )

            hits = response.get('hits', {}).get('hits', [])
            results = [hit['_source'] for hit in hits]

            return results

        except Exception as e:
            logger.error(f"Error searching teams: {e}")
            return []

    async def search_all(
        self,
        query: str,
        size: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Search across all indices"""
        try:
            results = {
                "players": await self.search_players(query, size=size),
                "teams": await self.search_teams(query, size=size)
            }

            return results

        except Exception as e:
            logger.error(f"Error in global search: {e}")
            return {"players": [], "teams": []}

    async def index_player(self, player_id: str, player_data: Dict[str, Any]):
        """Index a player document"""
        try:
            await self.es.index(
                index="players",
                id=player_id,
                document=player_data
            )
            logger.debug(f"Indexed player {player_id}")
        except Exception as e:
            logger.error(f"Error indexing player: {e}")

    async def index_team(self, team_id: str, team_data: Dict[str, Any]):
        """Index a team document"""
        try:
            await self.es.index(
                index="teams",
                id=team_id,
                document=team_data
            )
            logger.debug(f"Indexed team {team_id}")
        except Exception as e:
            logger.error(f"Error indexing team: {e}")

    async def close(self):
        """Close Elasticsearch connection"""
        await self.es.close()
