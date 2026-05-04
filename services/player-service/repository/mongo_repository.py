"""
MongoDB implementation of Player Repository
"""
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .interfaces import IPlayerRepository
import sys
sys.path.append('/app')
from shared.models.base import Player, PlayerStatistics
import logging

logger = logging.getLogger(__name__)


class MongoPlayerRepository(IPlayerRepository):
    """MongoDB implementation of player repository"""

    POSITION_ALIAS_MAP = {
        'GK': ['GK'],
        'CB': ['DF'],
        'LB': ['DF'],
        'RB': ['DF'],
        'LWB': ['DF'],
        'RWB': ['DF'],
        'DF': ['DF'],
        'CDM': ['MF'],
        'CM': ['MF'],
        'CAM': ['MF'],
        'LM': ['MF'],
        'RM': ['MF'],
        'MF': ['MF'],
        'LW': ['FW'],
        'RW': ['FW'],
        'ST': ['FW'],
        'CF': ['FW'],
        'FW': ['FW'],
    }

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.players_collection = db['players']
        self.stats_collection = db['player_statistics']

    def _has_value(self, value: Any) -> bool:
        return value not in (None, '', [], {})

    def _prepare_doc_for_player(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize a raw MongoDB document before passing to Player().

        - Removes _id (not in model)
        - Removes duplicate 'id' when 'scoutpro_id' is present (Pydantic v2 alias conflict)
        - Converts BSON Int64 / int scoutpro_id to str (Player.id is declared as str)
        """
        doc = dict(doc)
        doc.pop('_id', None)
        if 'scoutpro_id' in doc and 'id' in doc:
            doc.pop('id')
        # Motor returns BSON Int64 as Python int; Player.id is str
        if 'scoutpro_id' in doc and not isinstance(doc['scoutpro_id'], str):
            doc['scoutpro_id'] = str(doc['scoutpro_id'])
        return doc

    def _normalize_identity_value(self, value: Any) -> str:
        if value is None:
            return ''
        return str(value).strip()

    def _player_identity_key(self, doc: Dict[str, Any]) -> Optional[str]:
        scoutpro_id = self._normalize_identity_value(doc.get('scoutpro_id'))
        if scoutpro_id:
            return f"scoutpro:{scoutpro_id}"

        provider_ids = doc.get('provider_ids') or {}
        opta_id = self._normalize_identity_value(provider_ids.get('opta'))
        if opta_id:
            return f"opta:{opta_id.lstrip('p')}"

        opta_uid = self._normalize_identity_value(doc.get('uID'))
        if opta_uid:
            return f"uid:{opta_uid.lstrip('p')}"

        name = self._normalize_identity_value(doc.get('name'))
        if not name:
            return None

        club = self._normalize_identity_value(
            doc.get('club') or doc.get('teamName') or doc.get('current_team_name')
        )
        return f"name:{name.lower()}:{club.lower()}"

    def _player_quality_score(self, doc: Dict[str, Any]) -> int:
        score = 0

        if self._has_value(doc.get('scoutpro_id')):
            score += 10

        provider_ids = doc.get('provider_ids') or {}
        score += sum(2 for value in provider_ids.values() if self._has_value(value))

        opta_uid = self._normalize_identity_value(doc.get('uID'))
        if opta_uid:
            score += 2
            if opta_uid.isdigit():
                score += 4
            elif opta_uid.startswith('p') and opta_uid[1:].isdigit():
                score += 1

        for field in (
            'name',
            'first',
            'last',
            'position',
            'nationality',
            'club',
            'teamName',
            'teamID',
            'shirtNumber',
            'birthDate',
            'age',
            'height',
            'weight',
            'preferredFoot',
            'detailedPosition',
        ):
            if self._has_value(doc.get(field)):
                score += 1

        if self._has_value(doc.get('statsbombEnrichment')):
            score += 2

        return score

    def _deduplicate_player_docs(
        self,
        docs: List[Dict[str, Any]],
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        best_docs: Dict[str, Dict[str, Any]] = {}
        ordered_keys: List[str] = []

        for index, doc in enumerate(docs):
            identity_key = self._player_identity_key(doc) or f"anonymous:{index}"

            if identity_key not in best_docs:
                best_docs[identity_key] = doc
                ordered_keys.append(identity_key)
                continue

            existing_doc = best_docs[identity_key]
            if self._player_quality_score(doc) > self._player_quality_score(existing_doc):
                best_docs[identity_key] = doc

        deduplicated_docs = [best_docs[key] for key in ordered_keys]
        if limit is not None:
            return deduplicated_docs[:limit]
        return deduplicated_docs

    def _expand_position_filters(self, position_filter: Any) -> List[str]:
        if isinstance(position_filter, list):
            values = position_filter
        else:
            values = [position_filter]

        expanded: List[str] = []
        for value in values:
            normalized = self._normalize_identity_value(value).upper()
            if not normalized:
                continue

            for candidate in self.POSITION_ALIAS_MAP.get(normalized, [normalized]):
                if candidate not in expanded:
                    expanded.append(candidate)

        return expanded

    def _derive_player_age(self, doc: Dict[str, Any]) -> Optional[int]:
        raw_age = doc.get('age')
        if raw_age not in (None, ''):
            try:
                age = int(raw_age)
                if age >= 0:
                    return age
            except (TypeError, ValueError):
                pass

        raw_birth_date = doc.get('birth_date') or doc.get('birthDate')
        if not raw_birth_date:
            return None

        normalized_birth_date = self._normalize_identity_value(raw_birth_date)
        if not normalized_birth_date:
            return None

        parsed_birth_date = None
        try:
            parsed_birth_date = datetime.fromisoformat(normalized_birth_date.replace('Z', '+00:00')).date()
        except ValueError:
            try:
                parsed_birth_date = datetime.strptime(normalized_birth_date[:10], '%Y-%m-%d').date()
            except ValueError:
                return None

        today = date.today()
        age = today.year - parsed_birth_date.year - (
            (today.month, today.day) < (parsed_birth_date.month, parsed_birth_date.day)
        )
        return age if age >= 0 else None

    async def _find_best_player_doc(
        self,
        query: Dict[str, Any],
        limit: int = 10
    ) -> Optional[Dict[str, Any]]:
        docs = await self.players_collection.find(query).to_list(length=limit)
        deduplicated_docs = self._deduplicate_player_docs(docs, limit=1)
        if not deduplicated_docs:
            return None
        return deduplicated_docs[0]

    async def get_by_id(self, player_id: str) -> Optional[Player]:
        """
        Get player by ID from MongoDB.

        Lookup priority:
          1. scoutpro_id  (canonical golden-record ID, e.g. "sp_a90234fbdf23")
          2. provider_ids.opta  (numeric Opta ID, e.g. "184522")
          3. uID legacy field   (for backward compat during transition)
        """
        try:
            # 1. Canonical ScoutPro ID — stored as BSON Long (integer).
            # Query with both int and string so either storage format matches.
            sp_id_values: List[Any] = [player_id]
            try:
                sp_id_values.append(int(player_id))
            except (ValueError, TypeError):
                pass
            doc = await self._find_best_player_doc({"scoutpro_id": {"$in": sp_id_values}})

            if not doc:
                # 2. Provider reference – Opta numeric ID; DB stores either "p184522" or "184522"
                numeric_opta = player_id.lstrip("p")
                doc = await self._find_best_player_doc(
                    {"provider_ids.opta": {"$in": [numeric_opta, f"p{numeric_opta}"]}}
                )

            if not doc:
                # 3. Legacy uID – covers "p184522" or "184522" stored directly
                query_values: List[Any] = [player_id]
                if not player_id.startswith("p"):
                    query_values.append(f"p{player_id}")
                try:
                    query_values.append(int(player_id))
                except (ValueError, TypeError):
                    pass
                doc = await self._find_best_player_doc({"uID": {"$in": query_values}})

            if doc:
                return Player(**self._prepare_doc_for_player(doc))

            return None
        except Exception as e:
            logger.error(f"Error getting player {player_id}: {e}")
            return None

    async def find_by_filters(self, filters: Dict[str, Any], limit: int = 100) -> List[Player]:
        """Find players by filters"""
        try:
            query = {}
            age_min = filters.get('age_min')
            age_max = filters.get('age_max')

            if 'position' in filters and filters['position']:
                expanded_positions = self._expand_position_filters(filters['position'])
                if len(expanded_positions) == 1:
                    query['position'] = expanded_positions[0]
                elif expanded_positions:
                    query['position'] = {'$in': expanded_positions}

            if 'club' in filters and filters['club']:
                if isinstance(filters['club'], list):
                    query['club'] = {'$in': filters['club']}
                else:
                    query['club'] = filters['club']

            if 'nationality' in filters and filters['nationality']:
                query['nationality'] = filters['nationality']

            if 'search' in filters and filters['search']:
                search_value = filters['search']
                query['$or'] = [
                    {'name': {'$regex': search_value, '$options': 'i'}},
                    {'first': {'$regex': search_value, '$options': 'i'}},
                    {'last': {'$regex': search_value, '$options': 'i'}},
                    {'club': {'$regex': search_value, '$options': 'i'}},
                    {'nationality': {'$regex': search_value, '$options': 'i'}},
                ]

            raw_limit = min(max(limit * 5, limit), 1000)
            cursor = self.players_collection.find(query).limit(raw_limit)
            docs = await cursor.to_list(length=raw_limit)
            docs = self._deduplicate_player_docs(docs, limit=limit)

            players = []
            for doc in docs:
                effective_age = self._derive_player_age(doc)
                if age_min is not None and (effective_age is None or effective_age < age_min):
                    continue
                if age_max is not None and (effective_age is None or effective_age > age_max):
                    continue

                clean = self._prepare_doc_for_player(doc)
                if effective_age is not None and not self._has_value(clean.get('age')):
                    clean['age'] = effective_age

                try:
                    players.append(Player(**clean))
                    if len(players) >= limit:
                        break
                except Exception as e:
                    logger.warning(f"Skipping invalid player doc: {e}")
                    continue

            return players
        except Exception as e:
            logger.error(f"Error finding players: {e}")
            return []

    async def search(self, query: str, limit: int = 20) -> List[Player]:
        """Search players by name"""
        try:
            search_filter = {
                '$or': [
                    {'name': {'$regex': query, '$options': 'i'}},
                    {'first': {'$regex': query, '$options': 'i'}},
                    {'last': {'$regex': query, '$options': 'i'}}
                ]
            }

            raw_limit = min(max(limit * 5, limit), 500)
            cursor = self.players_collection.find(search_filter).limit(raw_limit)
            docs = await cursor.to_list(length=raw_limit)
            docs = self._deduplicate_player_docs(docs, limit=limit)

            players = []
            for doc in docs:
                try:
                    players.append(Player(**self._prepare_doc_for_player(doc)))
                except Exception as e:
                    logger.warning(f"Skipping invalid player doc: {e}")
                    continue

            return players
        except Exception as e:
            logger.error(f"Error searching players: {e}")
            return []

    async def get_statistics(
        self,
        player_id: str,
        stat_type: Optional[str] = None,
        per_90: bool = False
    ) -> Optional[PlayerStatistics]:
        """Get player statistics"""
        try:
            raw = str(player_id).strip()
            id_values: List[Any] = [raw]
            if raw.isdigit():
                id_values.append(int(raw))
            elif raw.lower().startswith('p') and raw[1:].isdigit():
                id_values.append(int(raw[1:]))
            query = {'$or': [
                {'playerID': {'$in': id_values}},
                {'player_id': {'$in': id_values}},
            ]}

            collection_name = 'player_statistics'
            if per_90:
                collection_name = 'player_statistics_per90'

            doc = await self.db[collection_name].find_one(query)

            if doc:
                if '_id' in doc:
                    doc.pop('_id')

                # Extract stats based on type
                stats = {}
                if stat_type:
                    # Get specific stat type (e.g., 'shotEvent', 'passEvent')
                    if stat_type in doc:
                        stats_ref = doc[stat_type]
                        if stats_ref:
                            # Dereference if it's a DBRef
                            stat_doc = await self.db[stat_type.lower()].find_one({'_id': stats_ref.id})
                            if stat_doc:
                                if '_id' in stat_doc:
                                    stat_doc.pop('_id')
                                stats = stat_doc
                else:
                    # Get all stats
                    stats = doc

                return PlayerStatistics(
                    player_id=player_id,
                    player_name=doc.get('playerName'),
                    competition_id=doc.get('competitionID'),
                    season_id=doc.get('seasonID'),
                    stats=stats
                )

            return None
        except Exception as e:
            logger.error(f"Error getting statistics for player {player_id}: {e}")
            return None

    async def create(self, player: Player) -> str:
        """Create new player"""
        try:
            await self.players_collection.insert_one(player.dict(by_alias=True))
            return str(player.id)
        except Exception as e:
            logger.error(f"Error creating player: {e}")
            raise

    async def update(self, player_id: str, player: Player) -> bool:
        """Update player"""
        try:
            result = await self.players_collection.update_one(
                {'uID': int(player_id)},
                {'$set': player.dict()}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating player {player_id}: {e}")
            return False
