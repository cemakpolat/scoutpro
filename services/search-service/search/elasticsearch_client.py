"""
Search client with Elasticsearch primary and MongoDB text-index fallback.
Falls back automatically when Elasticsearch is unavailable.
"""
import logging
from typing import Any, Dict, List, Optional

from elasticsearch import AsyncElasticsearch, ConnectionError as ESConnectionError, NotFoundError
import motor.motor_asyncio

logger = logging.getLogger(__name__)


class SearchClient:
    """
    Dual-mode search: Elasticsearch (primary) with MongoDB text-index (fallback).
    Auto-detects ES availability and switches gracefully.
    """

    def __init__(self, es_url: str, mongodb_url: str, database: str = "scoutpro"):
        self.es_url = es_url
        self.mongodb_url = mongodb_url
        self.database = database
        self.es: Optional[AsyncElasticsearch] = None
        self._es_available = False
        self._mongo_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None

    async def connect(self):
        """Initialize connections and determine which backend is available."""
        # Try Elasticsearch
        try:
            self.es = AsyncElasticsearch([self.es_url], request_timeout=5)
            info = await self.es.info()
            self._es_available = True
            logger.info(f"Elasticsearch connected: {info['version']['number']}")
            await self._ensure_indices()
        except Exception as e:
            logger.warning(f"Elasticsearch unavailable ({e}), using MongoDB text-index fallback")
            self._es_available = False
            if self.es:
                await self.es.close()
                self.es = None

        # MongoDB is always initialised (fallback + indexing source)
        self._mongo_client = motor.motor_asyncio.AsyncIOMotorClient(self.mongodb_url)
        db = self._mongo_client[self.database]
        # Ensure MongoDB text indices exist for fallback
        try:
            await db.players.create_index([("name", "text"), ("position", "text"), ("nationality", "text")], background=True)
            await db.teams.create_index([("name", "text"), ("country", "text")], background=True)
            await db.matches.create_index([("homeTeamName", "text"), ("awayTeamName", "text"), ("competition", "text")], background=True)
            logger.info("MongoDB text indices ensured")
        except Exception as e:
            logger.debug(f"Text index creation (may already exist): {e}")

    async def _ensure_indices(self):
        """Create ES indices with proper mappings if they don't exist."""
        players_mapping = {
            "mappings": {
                "properties": {
                    "player_id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "standard", "fields": {"keyword": {"type": "keyword"}}},
                    "position": {"type": "keyword"},
                    "nationality": {"type": "keyword"},
                    "team_id": {"type": "keyword"},
                    "age": {"type": "integer"},
                }
            }
        }
        teams_mapping = {
            "mappings": {
                "properties": {
                    "team_id": {"type": "keyword"},
                    "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "country": {"type": "keyword"},
                }
            }
        }
        for index, mapping in [("players", players_mapping), ("teams", teams_mapping)]:
            try:
                if not await self.es.indices.exists(index=index):
                    await self.es.indices.create(index=index, body=mapping)
                    logger.info(f"Created ES index: {index}")
            except Exception as e:
                logger.warning(f"ES index creation for {index}: {e}")

    async def close(self):
        if self.es:
            await self.es.close()
        if self._mongo_client:
            self._mongo_client.close()

    @property
    def backend(self) -> str:
        return "elasticsearch" if self._es_available else "mongodb"

    # ---- INDEX operations ----

    async def index_player(self, player_id: str, player_data: Dict[str, Any]) -> bool:
        if not self._es_available or not self.es:
            return False
        try:
            await self.es.index(index="players", id=player_id, document=player_data)
            return True
        except Exception as e:
            logger.error(f"ES index player error: {e}")
            return False

    async def index_team(self, team_id: str, team_data: Dict[str, Any]) -> bool:
        if not self._es_available or not self.es:
            return False
        try:
            await self.es.index(index="teams", id=team_id, document=team_data)
            return True
        except Exception as e:
            logger.error(f"ES index team error: {e}")
            return False

    async def index_document(self, index: str, document_id: str, document: Dict[str, Any]):
        """Compatibility wrapper used by the event consumer."""
        if not self._es_available or not self.es:
            return
        try:
            await self.es.index(index=index, id=document_id, document=document, refresh=True)
            logger.debug(f"Indexed {index} document {document_id}")
        except Exception as e:
            logger.error(f"Error indexing {index} document {document_id}: {e}")

    async def update_document(self, index: str, document_id: str, document: Dict[str, Any]):
        """Compatibility wrapper used by the event consumer."""
        if not self._es_available or not self.es:
            return
        try:
            await self.es.update(index=index, id=document_id, doc=document, doc_as_upsert=True, refresh=True)
            logger.debug(f"Updated {index} document {document_id}")
        except Exception as e:
            logger.error(f"Error updating {index} document {document_id}: {e}")

    # ---- SEARCH operations ----


    async def _enrich_and_deduplicate_players(self, results: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        deduped = []
        seen = set()
        
        db = self._get_db()
        
        for p in results:
            name = p.get("name", "").strip().lower()
            team = p.get("teamName", p.get("club", "")).strip().lower()
            key = (name, team)
            
            if key not in seen:
                seen.add(key)
                
                uid_str = str(p.get("uID", p.get("id", ""))).replace("p", "")
                
                if uid_str.isdigit():
                    stats = await db.player_statistics.find_one({"player_id": int(uid_str)}, {"_id": 0})
                    if stats:
                        p["goals"] = stats.get("goals", 0)
                        p["assists"] = stats.get("assists", 0)
                        p["passAccuracy"] = stats.get("pass_accuracy", 0)
                        p["rating"] = stats.get("rating", stats.get("overall_rating", 7.0))
                        p["matches"] = stats.get("match_count", 0)

                deduped.append(p)
                if len(deduped) >= limit:
                    break
                    
        return deduped

    async def search_players(self, query: str, position: Optional[str] = None, nationality: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        get_limit = limit * 2
        if self._es_available and self.es:
            results = await self._es_search_players(query, position, nationality, get_limit)
        else:
            results = await self._mongo_search_players(query, position, nationality, get_limit)
        return await self._enrich_and_deduplicate_players(results, limit)


    async def search_teams(self, query: str, country: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        if self._es_available and self.es:
            return await self._es_search_teams(query, country, limit)
        return await self._mongo_search_teams(query, country, limit)

    async def search_matches(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        if self._es_available and self.es:
            return await self._es_search_matches(query, limit)
        return await self._mongo_search_matches(query, limit)

    async def search_all(self, query: str, size: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Search across all entity types."""
        return {
            "players": await self.search_players(query, limit=size),
            "teams": await self.search_teams(query, limit=size),
            "matches": await self.search_matches(query, limit=size),
        }

    # ---- Elasticsearch implementations ----

    async def _es_search_players(self, query: str, position: Optional[str], nationality: Optional[str], limit: int) -> List[Dict[str, Any]]:
        try:
            must = [{"multi_match": {"query": query, "fields": ["name^3", "position", "nationality"]}}]
            filter_clauses = []
            if position:
                filter_clauses.append({"term": {"position": position}})
            if nationality:
                filter_clauses.append({"term": {"nationality": nationality}})
            body = {"query": {"bool": {"must": must, "filter": filter_clauses}}, "size": limit}
            resp = await self.es.search(index="players", body=body)
            return [{"_score": h["_score"], **h["_source"]} for h in resp["hits"]["hits"]]
        except Exception as e:
            logger.error(f"ES player search error: {e}")
            return await self._mongo_search_players(query, position, nationality, limit)

    async def _es_search_teams(self, query: str, country: Optional[str], limit: int) -> List[Dict[str, Any]]:
        try:
            body = {"query": {"multi_match": {"query": query, "fields": ["name^3", "country"]}}, "size": limit}
            resp = await self.es.search(index="teams", body=body)
            return [{"_score": h["_score"], **h["_source"]} for h in resp["hits"]["hits"]]
        except Exception as e:
            logger.error(f"ES team search error: {e}")
            return await self._mongo_search_teams(query, country, limit)

    async def _es_search_matches(self, query: str, limit: int) -> List[Dict[str, Any]]:
        try:
            body = {"query": {"multi_match": {"query": query, "fields": ["homeTeamName", "awayTeamName", "competition"]}}, "size": limit}
            resp = await self.es.search(index="matches", body=body)
            return [{"_score": h["_score"], **h["_source"]} for h in resp["hits"]["hits"]]
        except Exception as e:
            logger.error(f"ES match search error: {e}")
            return await self._mongo_search_matches(query, limit)

    # ---- MongoDB fallback implementations ----

    def _get_db(self):
        return self._mongo_client[self.database]

    async def _mongo_search_players(self, query: str, position: Optional[str], nationality: Optional[str], limit: int) -> List[Dict[str, Any]]:
        try:
            db = self._get_db()
            mongo_filter: Dict[str, Any] = {}
            if query:
                mongo_filter["$text"] = {"$search": query}
            if position:
                mongo_filter["position"] = {"$regex": position, "$options": "i"}
            if nationality:
                mongo_filter["nationality"] = {"$regex": nationality, "$options": "i"}
            cursor = db.players.find(mongo_filter, {"_id": 0}).limit(limit)
            results = await cursor.to_list(length=limit)
            # Fallback to regex if text search returns nothing
            if not results and query:
                regex_filter: Dict[str, Any] = {"$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"position": {"$regex": query, "$options": "i"}},
                ]}
                if position:
                    regex_filter["position"] = {"$regex": position, "$options": "i"}
                cursor2 = db.players.find(regex_filter, {"_id": 0}).limit(limit)
                results = await cursor2.to_list(length=limit)
            return results
        except Exception as e:
            logger.error(f"MongoDB player search error: {e}")
            return []

    async def _mongo_search_teams(self, query: str, country: Optional[str], limit: int) -> List[Dict[str, Any]]:
        try:
            db = self._get_db()
            mongo_filter: Dict[str, Any] = {}
            if query:
                mongo_filter["$or"] = [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"country": {"$regex": query, "$options": "i"}},
                ]
            if country:
                mongo_filter["country"] = {"$regex": country, "$options": "i"}
            cursor = db.teams.find(mongo_filter, {"_id": 0}).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"MongoDB team search error: {e}")
            return []

    async def _mongo_search_matches(self, query: str, limit: int) -> List[Dict[str, Any]]:
        try:
            db = self._get_db()
            mongo_filter: Dict[str, Any] = {}
            if query:
                mongo_filter["$or"] = [
                    {"homeTeamName": {"$regex": query, "$options": "i"}},
                    {"awayTeamName": {"$regex": query, "$options": "i"}},
                    {"competition": {"$regex": query, "$options": "i"}},
                ]
            cursor = db.matches.find(mongo_filter, {"_id": 0}).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"MongoDB match search error: {e}")
            return []

    async def bulk_index_from_mongo(self) -> Dict[str, int]:
        """Bootstrap ES index from MongoDB collections."""
        if not self._es_available or not self.es:
            return {"skipped": 1, "reason": "elasticsearch_unavailable"}
        counts = {}
        db = self._get_db()
        # Index players
        count = 0
        async for doc in db.players.find({}, {"_id": 0}):
            pid = str(doc.get("id") or doc.get("uID") or doc.get("player_id") or count)
            await self.index_player(pid, doc)
            count += 1
        counts["players"] = count
        # Index teams
        count = 0
        async for doc in db.teams.find({}, {"_id": 0}):
            tid = str(doc.get("uID") or doc.get("id") or count)
            await self.index_team(tid, doc)
            count += 1
        counts["teams"] = count
        return counts
        self.es = AsyncElasticsearch([es_url])
