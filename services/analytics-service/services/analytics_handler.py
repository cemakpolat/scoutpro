import httpx
import logging
import asyncio
from collections import Counter, defaultdict
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import get_settings

logger = logging.getLogger(__name__)

class CacheEntry:
    """Simple cache entry with TTL."""
    def __init__(self, data: Any, ttl_seconds: int = 300):
        self.data = data
        self.created_at = datetime.now()
        self.ttl_seconds = ttl_seconds
    
    def is_expired(self) -> bool:
        return (datetime.now() - self.created_at).total_seconds() > self.ttl_seconds

class AnalyticsHandler:
    def __init__(self):
        settings = get_settings()
        self.player_service_url = settings.player_service_url.rstrip('/')
        self.team_service_url = settings.team_service_url.rstrip('/')
        self.match_service_url = settings.match_service_url.rstrip('/')
        self.statistics_service_url = settings.statistics_service_url.rstrip('/')
        self.ml_service_url = settings.ml_service_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=10.0)
        
        # MongoDB client for direct event consumption
        self.mongo_client = AsyncIOMotorClient(settings.mongodb_url)
        self.db = self.mongo_client[settings.mongodb_database]
        
        # Response caches with TTL (5 minutes)
        self._player_dashboard_cache: Dict[str, CacheEntry] = {}
        self._player_sequence_cache: Dict[str, CacheEntry] = {}
        self._team_dashboard_cache: Dict[str, CacheEntry] = {}

    async def _get_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            response = await self.client.get(url, params=params)
            if response.status_code >= 400:
                logger.warning("Analytics upstream call failed: %s %s -> %s", response.request.method, url, response.status_code)
                return {}
            payload = response.json()
            return payload if isinstance(payload, dict) else {"data": payload}
        except Exception as exc:
            logger.error("Analytics upstream call errored for %s: %s", url, exc)
            return {}

    def _get_cached(self, cache: Dict[str, CacheEntry], key: str) -> Optional[Any]:
        """Retrieve from cache if not expired."""
        if key in cache:
            entry = cache[key]
            if not entry.is_expired():
                logger.debug(f"Cache hit for {key}")
                return entry.data
            else:
                del cache[key]
        return None
    
    def _set_cache(self, cache: Dict[str, CacheEntry], key: str, value: Any, ttl: int = 300) -> None:
        """Store in cache with TTL."""
        cache[key] = CacheEntry(value, ttl)
        logger.debug(f"Cached {key} for {ttl}s")

    async def _get_events_from_mongodb(self, match_id: str) -> List[Dict[str, Any]]:
        """
        Query events directly from MongoDB match_events collection.
        
        This provides faster event access without relying on the Match Service,
        enabling direct event consumption by analytics modules.
        """
        try:
            collection = self.db['match_events']
            
            # Support both numeric and string match IDs
            query = {
                '$or': [
                    {'matchID': match_id},
                    {'matchID': int(match_id)} if match_id.isdigit() else {'matchID': match_id}
                ]
            }
            
            events = await collection.find(query).sort('timestamp', 1).to_list(length=None)
            
            # Clean up MongoDB internal fields
            for event in events:
                event.pop('_id', None)
            
            logger.info(f"Loaded {len(events)} events from MongoDB for match {match_id}")
            return events
        except Exception as e:
            logger.error(f"Error fetching events from MongoDB: {e}")
            return []

    @staticmethod
    def _unwrap_data(payload: Dict[str, Any]) -> Any:
        if isinstance(payload, dict) and 'data' in payload:
            return payload['data']
        return payload

    def _extract_list(self, payload: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
        unwrapped = self._unwrap_data(payload)

        if isinstance(unwrapped, list):
            return unwrapped

        if isinstance(unwrapped, dict):
            items = unwrapped.get(key)
            if isinstance(items, list):
                return items

        return []

    def _extract_count(self, payload: Dict[str, Any], key: str) -> int:
        unwrapped = self._unwrap_data(payload)

        if isinstance(unwrapped, dict) and isinstance(unwrapped.get('total'), int):
            return unwrapped['total']

        return len(self._extract_list(payload, key))

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        if value in (None, '', 'None'):
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _to_int(value: Any, default: int = 0) -> int:
        if value in (None, '', 'None'):
            return default
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _derive_age(value: Any) -> Optional[int]:
        parsed = AnalyticsHandler._parse_date(value)
        if not parsed:
            return None

        today = datetime.utcnow()
        age = today.year - parsed.year - ((today.month, today.day) < (parsed.month, parsed.day))
        return age if age >= 0 else None

    @staticmethod
    def _player_stats_candidates(player_id: str, player: Dict[str, Any]) -> List[str]:
        candidates: List[str] = []

        def add(candidate: Any) -> None:
            if candidate in (None, '', 'None'):
                return

            normalized = str(candidate).strip()
            if normalized and normalized not in candidates:
                candidates.append(normalized)

            if normalized.lower().startswith('p') and normalized[1:].isdigit() and normalized[1:] not in candidates:
                candidates.append(normalized[1:])

        add(player_id)
        add(player.get('player_id'))
        add(player.get('uID'))
        add(player.get('opta_uid'))

        provider_ids = player.get('provider_ids') or {}
        if isinstance(provider_ids, dict):
            add(provider_ids.get('opta'))
            add(provider_ids.get('statsbomb'))

        return candidates

    @staticmethod
    def _identifier_variants(value: Any) -> List[str]:
        if value in (None, '', 'None'):
            return []

        normalized = str(value).strip()
        if not normalized:
            return []

        variants = [normalized]
        if normalized.isdigit():
            prefixed = f'p{normalized}'
            if prefixed not in variants:
                variants.append(prefixed)
        elif normalized.lower().startswith('p') and normalized[1:].isdigit():
            numeric_variant = normalized[1:]
            if numeric_variant not in variants:
                variants.append(numeric_variant)

        return variants

    @classmethod
    def _player_event_candidates(cls, player_id: str, player: Dict[str, Any]) -> List[Any]:
        candidates: List[Any] = []
        seen_strings = set()
        seen_numbers = set()

        def add(value: Any) -> None:
            for variant in cls._identifier_variants(value):
                if variant not in seen_strings:
                    seen_strings.add(variant)
                    candidates.append(variant)

                if variant.isdigit():
                    numeric_variant = int(variant)
                    if numeric_variant not in seen_numbers:
                        seen_numbers.add(numeric_variant)
                        candidates.append(numeric_variant)

        add(player_id)
        add(player.get('player_id'))
        add(player.get('uID'))
        add(player.get('opta_uid'))
        add(player.get('scoutpro_id'))
        add(player.get('id'))

        provider_ids = player.get('provider_ids') or {}
        if isinstance(provider_ids, dict):
            add(provider_ids.get('opta'))
            add(provider_ids.get('statsbomb'))

        return candidates

    @classmethod
    def _event_matches_player(cls, event: Dict[str, Any], candidate_identifiers: set[str]) -> bool:
        if not candidate_identifiers:
            return False

        raw_event = event.get('raw_event') if isinstance(event.get('raw_event'), dict) else {}
        event_identifiers = set()

        for value in (
            event.get('player_id'),
            event.get('playerID'),
            raw_event.get('player_id'),
            raw_event.get('playerID'),
        ):
            event_identifiers.update(cls._identifier_variants(value))

        return bool(event_identifiers & candidate_identifiers)

    async def _get_recent_player_matches(self, player_id: str, player: Dict[str, Any], limit: int = 6) -> List[Dict[str, Any]]:
        candidate_values = self._player_event_candidates(player_id, player)
        if not candidate_values:
            return []

        try:
            # Optimize by running two indexed queries instead of $or across different fields
            match_ids_set: set[str] = set()
            
            # Query 1: Use index on player_id
            pipeline1 = [
                {'$match': {'player_id': {'$in': candidate_values}}},
                {'$project': {'match_key': {'$ifNull': ['$matchID', {'$ifNull': ['$match_id', '$matchId']}]}}},
                {'$match': {'match_key': {'$nin': [None, '', 'None']}}},
                {'$group': {'_id': '$match_key'}},
            ]
            
            docs1 = await self.db['match_events'].aggregate(pipeline1).to_list(length=200)
            for doc in docs1:
                if doc.get('_id'):
                    match_ids_set.add(str(doc['_id']))
            
            # Query 2: Use index on playerID (if different field is populated)
            pipeline2 = [
                {'$match': {'playerID': {'$in': candidate_values}}},
                {'$project': {'match_key': {'$ifNull': ['$matchID', {'$ifNull': ['$match_id', '$matchId']}]}}},
                {'$match': {'match_key': {'$nin': [None, '', 'None']}}},
                {'$group': {'_id': '$match_key'}},
            ]
            
            docs2 = await self.db['match_events'].aggregate(pipeline2).to_list(length=200)
            for doc in docs2:
                if doc.get('_id'):
                    match_ids_set.add(str(doc['_id']))
            
            match_ids = list(match_ids_set)
            if not match_ids:
                return []

            # Build lookup values with variants
            match_lookup_values: List[Any] = []
            for match_id in match_ids:
                normalized = str(match_id).strip()
                if not normalized:
                    continue
                if normalized not in match_lookup_values:
                    match_lookup_values.append(normalized)
                if normalized.isdigit():
                    numeric_variant = int(normalized)
                    if numeric_variant not in match_lookup_values:
                        match_lookup_values.append(numeric_variant)

            matches_query = {
                '$or': [
                    {'matchID': {'$in': match_lookup_values}},
                    {'uID': {'$in': match_lookup_values}},
                    {'id': {'$in': match_lookup_values}},
                ]
            }

            matches = await self.db['matches'].find(matches_query).sort('date', -1).to_list(length=limit)
            for match in matches:
                match.pop('_id', None)

            if matches:
                return matches

            return [{'id': str(match_id)} for match_id in match_ids[:limit]]
        except Exception as exc:
            logger.error('Failed to resolve recent matches for player %s: %s', player_id, exc)
            return []

    @staticmethod
    def _stats_dict(payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {}

        unwrapped = payload.get('data', payload)
        if not isinstance(unwrapped, dict):
            return {}

        stats = unwrapped.get('stats')
        if isinstance(stats, dict):
            return stats

        return unwrapped

    @staticmethod
    def _parse_date(value: Any) -> Optional[datetime]:
        if value in (None, '', 'None'):
            return None

        text = str(value).replace('Z', '+00:00')
        for candidate in (text, text.replace(' ', 'T')):
            try:
                dt = datetime.fromisoformat(candidate)
                # Always return naive datetime so comparisons with datetime.min work
                return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt
            except ValueError:
                continue
        return None

    @staticmethod
    def _sort_matches(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(
            matches,
            key=lambda match: AnalyticsHandler._parse_date(match.get('date')) or datetime.min,
            reverse=True,
        )

    @staticmethod
    def _extract_stat_value(stats: Dict[str, Any], *keys: str) -> float:
        for key in keys:
            value = stats.get(key)
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    continue
        return 0.0

    @staticmethod
    def _pass_accuracy(stats: Dict[str, Any]) -> float:
        direct = AnalyticsHandler._extract_stat_value(stats, 'passAccuracy', 'pass_accuracy')
        if direct:
            return round(direct, 2)

        accurate = AnalyticsHandler._extract_stat_value(stats, 'accurate_pass')
        total = AnalyticsHandler._extract_stat_value(stats, 'total_pass')
        if total > 0:
            return round((accurate / total) * 100, 2)

        return 0.0

    @staticmethod
    def _bucket_minutes(time_bucket: str) -> int:
        if not time_bucket:
            return 5
        digits = ''.join(character for character in str(time_bucket) if character.isdigit())
        return max(1, int(digits)) if digits else 5

    @staticmethod
    def _optional_number(value: Any) -> Optional[float]:
        if value in (None, '', 'None'):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _normalize_coordinate(cls, value: Any, axis: str) -> Optional[float]:
        numeric = cls._optional_number(value)
        if numeric is None:
            return None

        normalized = (numeric / 120.0) * 100.0 if axis == 'x' and numeric > 100 else numeric
        if axis == 'y' and numeric > 100:
            normalized = (numeric / 80.0) * 100.0

        return max(0.0, min(100.0, normalized))

    @classmethod
    def _to_location(cls, location: Any) -> Optional[Dict[str, float]]:
        if not location:
            return None

        if isinstance(location, list) and len(location) >= 2:
            x_value = cls._normalize_coordinate(location[0], 'x')
            y_value = cls._normalize_coordinate(location[1], 'y')
        elif isinstance(location, dict):
            x_value = cls._normalize_coordinate(location.get('x'), 'x')
            y_value = cls._normalize_coordinate(location.get('y'), 'y')
        else:
            return None

        if x_value is None or y_value is None:
            return None

        return {
            'x': round(x_value, 2),
            'y': round(y_value, 2),
        }

    @classmethod
    def _get_qualifier_end_location(cls, event: Dict[str, Any]) -> Optional[Dict[str, float]]:
        raw_event = event.get('raw_event') if isinstance(event.get('raw_event'), dict) else {}
        qualifiers = raw_event.get('qualifiers') or event.get('qualifiers') or {}
        if not isinstance(qualifiers, dict):
            return None

        x_value = qualifiers.get(140) if 140 in qualifiers else qualifiers.get('140')
        y_value = qualifiers.get(141) if 141 in qualifiers else qualifiers.get('141')
        if x_value is None or y_value is None:
            return None

        return cls._to_location({'x': x_value, 'y': y_value})

    @staticmethod
    def _sequence_event_type(event: Dict[str, Any]) -> str:
        raw_event = event.get('raw_event') if isinstance(event.get('raw_event'), dict) else {}
        return str(raw_event.get('type_name') or event.get('type_name') or '').strip().lower()

    @classmethod
    def _sequence_event_timestamp(cls, event: Dict[str, Any]) -> float:
        explicit = cls._optional_number(event.get('timestamp'))
        if explicit is not None:
            return explicit

        timestamp_seconds = cls._optional_number(event.get('timestamp_seconds'))
        if timestamp_seconds is not None:
            return timestamp_seconds

        minute = cls._to_int(event.get('minute'))
        second = cls._to_int(event.get('second'))
        return float(minute * 60 + second)

    @classmethod
    def _sequence_start_location(cls, event: Dict[str, Any]) -> Optional[Dict[str, float]]:
        raw_event = event.get('raw_event') if isinstance(event.get('raw_event'), dict) else {}
        return cls._to_location(event.get('location') or raw_event.get('location'))

    @classmethod
    def _sequence_end_location(cls, event: Dict[str, Any]) -> Optional[Dict[str, float]]:
        raw_event = event.get('raw_event') if isinstance(event.get('raw_event'), dict) else {}
        return cls._to_location(
            event.get('end_location')
            or raw_event.get('end_location')
            or raw_event.get('pass_end_location')
            or raw_event.get('carry_end_location')
            or raw_event.get('shot_end_location')
        ) or cls._get_qualifier_end_location(event)

    @classmethod
    def _sequence_action_location(cls, event: Dict[str, Any]) -> Optional[Dict[str, float]]:
        return cls._sequence_end_location(event) or cls._sequence_start_location(event)

    @classmethod
    def _is_actionable_sequence_event(cls, event: Dict[str, Any]) -> bool:
        ignored_event_types = {
            'starting xi',
            'half start',
            'half end',
            'unknown',
            'lineup',
        }
        event_type = cls._sequence_event_type(event)
        if not event or event.get('team_id') in (None, '') or not event_type:
            return False

        if event_type in ignored_event_types:
            return False

        no_actor = event.get('player_id') in (None, '')
        if event_type.isdigit() and no_actor and not cls._sequence_start_location(event) and not cls._sequence_end_location(event):
            return False

        return True

    @staticmethod
    def _territory_lane(location: Optional[Dict[str, float]]) -> str:
        if not location or location.get('y') is None:
            return 'Central Lane'
        if location['y'] < 33:
            return 'Left Channel'
        if location['y'] > 66:
            return 'Right Channel'
        return 'Central Lane'

    @classmethod
    def _is_shot_like(cls, event: Dict[str, Any]) -> bool:
        event_type = cls._sequence_event_type(event)
        return bool(event.get('is_goal')) \
            or 'shot' in event_type \
            or 'goal' in event_type \
            or 'attempt saved' in event_type \
            or 'miss' in event_type \
            or 'post' in event_type

    @classmethod
    def _is_direct_play_event(cls, event: Dict[str, Any]) -> bool:
        event_type = cls._sequence_event_type(event)
        raw_event = event.get('raw_event') if isinstance(event.get('raw_event'), dict) else {}
        qualifiers = raw_event.get('qualifiers') or event.get('qualifiers') or {}
        pass_type = str(raw_event.get('pass_type') or event.get('pass_type') or '').lower()

        return 'clearance' in event_type \
            or 'cross' in event_type \
            or 'long' in pass_type \
            or 'cross' in pass_type \
            or (isinstance(qualifiers, dict) and any(key in qualifiers for key in (1, '1', 2, '2')))

    @staticmethod
    def _match_team_context(match: Dict[str, Any]) -> Dict[str, str]:
        home_team = match.get('homeTeam') if isinstance(match.get('homeTeam'), dict) else {}
        away_team = match.get('awayTeam') if isinstance(match.get('awayTeam'), dict) else {}

        home_team_id = str(
            match.get('home_team_id')
            or match.get('homeTeamID')
            or match.get('homeTeamId')
            or home_team.get('id')
            or 'home'
        )
        away_team_id = str(
            match.get('away_team_id')
            or match.get('awayTeamID')
            or match.get('awayTeamId')
            or away_team.get('id')
            or 'away'
        )

        home_team_name = match.get('home_team_name') or match.get('home_team') or match.get('homeTeamName')
        if not home_team_name and isinstance(match.get('homeTeam'), str):
            home_team_name = match.get('homeTeam')
        if not home_team_name:
            home_team_name = home_team.get('name') or (f'Team {home_team_id}' if home_team_id != 'home' else 'Home')

        away_team_name = match.get('away_team_name') or match.get('away_team') or match.get('awayTeamName')
        if not away_team_name and isinstance(match.get('awayTeam'), str):
            away_team_name = match.get('awayTeam')
        if not away_team_name:
            away_team_name = away_team.get('name') or (f'Team {away_team_id}' if away_team_id != 'away' else 'Away')

        return {
            'home_team_id': home_team_id,
            'away_team_id': away_team_id,
            'home_team_name': str(home_team_name),
            'away_team_name': str(away_team_name),
        }

    @classmethod
    def _create_sequence(cls, event: Dict[str, Any], match_context: Dict[str, Any]) -> Dict[str, Any]:
        start_location = cls._sequence_start_location(event) or cls._sequence_action_location(event)
        team_id = str(event.get('team_id'))

        return {
            'teamId': team_id,
            'teamName': match_context['teamNames'].get(team_id, f'Team {team_id}'),
            'period': cls._to_int(event.get('period')),
            'startTimestamp': cls._sequence_event_timestamp(event),
            'endTimestamp': cls._sequence_event_timestamp(event),
            'startMinute': cls._to_int(event.get('minute')),
            'endMinute': cls._to_int(event.get('minute')),
            'startLocation': start_location,
            'endLocation': cls._sequence_action_location(event) or start_location,
            'directPlay': cls._is_direct_play_event(event),
            'events': [event],
        }

    @classmethod
    def _finalize_sequence(cls, sequence: Dict[str, Any], include_event_refs: bool = False) -> Dict[str, Any]:
        start_location = sequence.get('startLocation') or sequence.get('endLocation') or {'x': 50, 'y': 50}
        end_location = sequence.get('endLocation') or start_location
        duration_seconds = max(1, round(sequence['endTimestamp'] - sequence['startTimestamp']))
        territory_gain = round((end_location.get('x') or 0) - (start_location.get('x') or 0))
        final_third_entry = (start_location.get('x') or 0) < 66 and (end_location.get('x') or 0) >= 66
        box_entry = (start_location.get('x') or 0) < 83 and (end_location.get('x') or 0) >= 83
        ended_with_shot = any(cls._is_shot_like(event) for event in sequence['events'])
        ended_with_goal = any(bool(event.get('is_goal')) for event in sequence['events'])

        payload = {
            'teamId': sequence['teamId'],
            'teamName': sequence['teamName'],
            'actions': len(sequence['events']),
            'durationSeconds': duration_seconds,
            'startTimestamp': sequence['startTimestamp'],
            'endTimestamp': sequence['endTimestamp'],
            'startMinute': sequence['startMinute'],
            'endMinute': sequence['endMinute'],
            'territoryGain': territory_gain,
            'route': cls._territory_lane(end_location),
            'directPlay': sequence['directPlay'],
            'directAttack': duration_seconds <= 15 and territory_gain >= 15 and len(sequence['events']) >= 3,
            'sustainedPressure': len(sequence['events']) >= 5 and (end_location.get('x') or 0) >= 66,
            'finalThirdEntry': final_third_entry,
            'boxEntry': box_entry,
            'endedWithShot': ended_with_shot,
            'endedWithGoal': ended_with_goal,
        }

        if include_event_refs:
            payload['events'] = list(sequence['events'])

        return payload

    @classmethod
    def _build_sequences(cls, events: List[Dict[str, Any]], match: Dict[str, Any], include_event_refs: bool = False) -> List[Dict[str, Any]]:
        match_context_values = cls._match_team_context(match)
        match_context = {
            'teamNames': {
                match_context_values['home_team_id']: match_context_values['home_team_name'],
                match_context_values['away_team_id']: match_context_values['away_team_name'],
            }
        }

        actionable_events = sorted(
            [event for event in events if cls._is_actionable_sequence_event(event)],
            key=cls._sequence_event_timestamp,
        )

        sequences: List[Dict[str, Any]] = []
        current_sequence: Optional[Dict[str, Any]] = None

        for event in actionable_events:
            team_id = str(event.get('team_id'))
            timestamp = cls._sequence_event_timestamp(event)
            event_period = cls._to_int(event.get('period'))
            action_location = cls._sequence_action_location(event) or cls._sequence_start_location(event)

            should_start_new_sequence = current_sequence is None \
                or current_sequence['teamId'] != team_id \
                or current_sequence['period'] != event_period \
                or timestamp - current_sequence['endTimestamp'] > 12

            if should_start_new_sequence:
                if current_sequence and current_sequence['events']:
                    sequences.append(cls._finalize_sequence(current_sequence, include_event_refs=include_event_refs))
                current_sequence = cls._create_sequence(event, match_context)
                continue

            current_sequence['events'].append(event)
            current_sequence['endTimestamp'] = timestamp
            current_sequence['endMinute'] = cls._to_int(event.get('minute')) or current_sequence['endMinute']
            current_sequence['endLocation'] = action_location or current_sequence['endLocation']
            current_sequence['directPlay'] = current_sequence['directPlay'] or cls._is_direct_play_event(event)

        if current_sequence and current_sequence['events']:
            sequences.append(cls._finalize_sequence(current_sequence, include_event_refs=include_event_refs))

        return sequences

    @staticmethod
    def _build_rapid_regain_index(sequences: List[Dict[str, Any]]) -> Dict[str, int]:
        rapid_regains: Dict[str, int] = {}

        for index in range(2, len(sequences)):
            previous_own_sequence = sequences[index - 2]
            opponent_sequence = sequences[index - 1]
            regained_sequence = sequences[index]

            if previous_own_sequence['teamId'] != regained_sequence['teamId'] or previous_own_sequence['teamId'] == opponent_sequence['teamId']:
                continue

            regain_window = max(0, regained_sequence['startTimestamp'] - previous_own_sequence['endTimestamp'])
            regained_quickly = regained_sequence['durationSeconds'] <= 8 or opponent_sequence['durationSeconds'] <= 5
            if regain_window <= 8 and regained_quickly:
                rapid_regains[regained_sequence['teamId']] = rapid_regains.get(regained_sequence['teamId'], 0) + 1

        return rapid_regains

    @staticmethod
    def _round_average(total: float, count: int) -> float:
        if not count:
            return 0.0
        return round((total / count) * 10) / 10

    @classmethod
    def _build_team_sequence_summary(cls, team_id: str, team_name: str, sequences: List[Dict[str, Any]], rapid_regains: Dict[str, int]) -> Optional[Dict[str, Any]]:
        team_sequences = [sequence for sequence in sequences if sequence['teamId'] == team_id]
        total_sequences = len(team_sequences)
        if not total_sequences:
            return None

        return {
            'teamId': team_id,
            'teamName': team_name,
            'totalSequences': total_sequences,
            'directAttacks': len([sequence for sequence in team_sequences if sequence['directAttack']]),
            'sustainedPressure': len([sequence for sequence in team_sequences if sequence['sustainedPressure']]),
            'finalThirdEntries': len([sequence for sequence in team_sequences if sequence['finalThirdEntry']]),
            'boxEntries': len([sequence for sequence in team_sequences if sequence['boxEntry']]),
            'shotEndings': len([sequence for sequence in team_sequences if sequence['endedWithShot']]),
            'goals': len([sequence for sequence in team_sequences if sequence['endedWithGoal']]),
            'rapidRegains': rapid_regains.get(team_id, 0),
            'averageActions': cls._round_average(sum(sequence['actions'] for sequence in team_sequences), total_sequences),
            'averageDurationSeconds': cls._round_average(sum(sequence['durationSeconds'] for sequence in team_sequences), total_sequences),
        }

    @staticmethod
    def _score_sequence(sequence: Dict[str, Any]) -> int:
        return sequence['territoryGain'] \
            + sequence['actions'] * 4 \
            + (12 if sequence['finalThirdEntry'] else 0) \
            + (16 if sequence['boxEntry'] else 0) \
            + (20 if sequence['endedWithShot'] else 0) \
            + (40 if sequence['endedWithGoal'] else 0)

    async def get_sequence_insights(self, match_id: str) -> Optional[Dict[str, Any]]:
        match_payload = await self._get_json(f"{self.match_service_url}/api/v2/matches/{match_id}")
        match = self._unwrap_data(match_payload) or {}

        events = await self._get_events_from_mongodb(match_id)
        if not events:
            events_payload = await self._get_json(f"{self.match_service_url}/api/v2/matches/{match_id}/events")
            events = self._unwrap_data(events_payload)

        if not isinstance(events, list) or not events:
            return None

        sequences = self._build_sequences(events, match if isinstance(match, dict) else {})
        if not sequences:
            return None

        match_context = self._match_team_context(match if isinstance(match, dict) else {})
        team_ids_in_sequences = list(dict.fromkeys(sequence['teamId'] for sequence in sequences if sequence.get('teamId')))
        home_team_id = match_context['home_team_id'] if match_context['home_team_id'] not in ('home', '') else (team_ids_in_sequences[0] if team_ids_in_sequences else 'home')
        away_team_id = match_context['away_team_id'] if match_context['away_team_id'] not in ('away', '') else (team_ids_in_sequences[1] if len(team_ids_in_sequences) > 1 else 'away')
        home_team_name = match_context['home_team_name'] if match_context['home_team_name'] not in ('Home', '') else (f'Team {home_team_id}' if home_team_id not in ('home', '') else 'Home')
        away_team_name = match_context['away_team_name'] if match_context['away_team_name'] not in ('Away', '') else (f'Team {away_team_id}' if away_team_id not in ('away', '') else 'Away')
        rapid_regains = self._build_rapid_regain_index(sequences)

        return {
            'matchId': str(match.get('id') or match.get('uID') or match_id),
            'matchLabel': f'{home_team_name} vs {away_team_name}',
            'providers': sorted(set(str(event.get('provider')) for event in events if event.get('provider'))),
            'teamSummaries': [
                summary for summary in [
                    self._build_team_sequence_summary(home_team_id, home_team_name, sequences, rapid_regains),
                    self._build_team_sequence_summary(away_team_id, away_team_name, sequences, rapid_regains),
                ] if summary
            ],
            'topSequences': [
                sequence for sequence in sorted(
                    [sequence for sequence in sequences if sequence['actions'] >= 3 or sequence['endedWithShot'] or sequence['finalThirdEntry']],
                    key=self._score_sequence,
                    reverse=True,
                )[:4]
            ],
            'last_updated': datetime.now().isoformat(),
        }

    async def get_player_sequence_insights(self, player_id: str, match_limit: int = 6) -> Dict[str, Any]:
        cache_key = f"{player_id}#sequences#{match_limit}"
        
        # Check cache first
        cached = self._get_cached(self._player_sequence_cache, cache_key)
        if cached:
            return cached
        
        dashboard = await self.get_player_dashboard(player_id)
        player = dashboard.get('player', {})
        candidate_values = self._player_event_candidates(player_id, player)
        candidate_identifiers: set[str] = set()
        for candidate in candidate_values:
            candidate_identifiers.update(self._identifier_variants(candidate))

        recent_matches = await self._get_recent_player_matches(player_id, player, limit=match_limit)
        player_sequences: List[Dict[str, Any]] = []
        match_summaries: List[Dict[str, Any]] = []

        for match in recent_matches:
            match_identifier = str(
                match.get('id')
                or match.get('uID')
                or match.get('matchID')
                or match.get('match_id')
                or ''
            ).strip()
            if not match_identifier:
                continue

            events = await self._get_events_from_mongodb(match_identifier)
            if not events:
                continue

            sequences = self._build_sequences(events, match if isinstance(match, dict) else {}, include_event_refs=True)
            if not sequences:
                continue

            match_context = self._match_team_context(match if isinstance(match, dict) else {})
            match_label = f"{match_context['home_team_name']} vs {match_context['away_team_name']}"
            match_player_sequences: List[Dict[str, Any]] = []

            for sequence in sequences:
                raw_sequence_events = sequence.get('events') or []
                player_actions = sum(
                    1
                    for event in raw_sequence_events
                    if self._event_matches_player(event, candidate_identifiers)
                )
                if player_actions == 0:
                    continue

                sequence_payload = {
                    key: value
                    for key, value in sequence.items()
                    if key != 'events'
                }
                sequence_payload.update({
                    'matchId': match_identifier,
                    'matchLabel': match_label,
                    'playerActions': player_actions,
                })
                match_player_sequences.append(sequence_payload)

            if not match_player_sequences:
                continue

            player_sequences.extend(match_player_sequences)
            match_summaries.append({
                'matchId': match_identifier,
                'matchLabel': match_label,
                'date': match.get('date'),
                'teamId': match_player_sequences[0].get('teamId'),
                'teamName': match_player_sequences[0].get('teamName'),
                'totalSequences': len(match_player_sequences),
                'directAttacks': len([sequence for sequence in match_player_sequences if sequence.get('directAttack')]),
                'boxEntries': len([sequence for sequence in match_player_sequences if sequence.get('boxEntry')]),
                'shotEndings': len([sequence for sequence in match_player_sequences if sequence.get('endedWithShot')]),
                'goals': len([sequence for sequence in match_player_sequences if sequence.get('endedWithGoal')]),
            })

        total_sequences = len(player_sequences)
        summary = {
            'matchesAnalyzed': len(match_summaries),
            'totalSequences': total_sequences,
            'totalPlayerActions': sum(sequence.get('playerActions', 0) for sequence in player_sequences),
            'directAttacks': len([sequence for sequence in player_sequences if sequence.get('directAttack')]),
            'sustainedPressure': len([sequence for sequence in player_sequences if sequence.get('sustainedPressure')]),
            'finalThirdEntries': len([sequence for sequence in player_sequences if sequence.get('finalThirdEntry')]),
            'boxEntries': len([sequence for sequence in player_sequences if sequence.get('boxEntry')]),
            'shotEndings': len([sequence for sequence in player_sequences if sequence.get('endedWithShot')]),
            'goals': len([sequence for sequence in player_sequences if sequence.get('endedWithGoal')]),
            'averageActions': self._round_average(sum(sequence.get('actions', 0) for sequence in player_sequences), total_sequences),
            'averageDurationSeconds': self._round_average(sum(sequence.get('durationSeconds', 0) for sequence in player_sequences), total_sequences),
            'averageTerritoryGain': self._round_average(sum(sequence.get('territoryGain', 0) for sequence in player_sequences), total_sequences),
        }

        top_sequences = sorted(
            player_sequences,
            key=lambda sequence: (self._score_sequence(sequence), sequence.get('playerActions', 0)),
            reverse=True,
        )[:5]

        result = {
            'player_id': player_id,
            'player': player,
            'summary': summary,
            'matchSummaries': match_summaries,
            'topSequences': top_sequences,
            'last_updated': datetime.now().isoformat(),
        }
        
        # Cache for 5 minutes
        self._set_cache(self._player_sequence_cache, cache_key, result, ttl=300)
        return result

    async def get_player_sequence_coverage(self, player_ids: List[str]) -> Dict[str, Any]:
        normalized_player_ids: List[str] = []
        seen = set()

        for player_id in player_ids[:100]:
            normalized = str(player_id).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            normalized_player_ids.append(normalized)

        semaphore = asyncio.Semaphore(8)

        async def build_item(player_id: str) -> Dict[str, Any]:
            async with semaphore:
                payload = await self.get_player_sequence_insights(player_id)

            summary = payload.get('summary', {}) if isinstance(payload, dict) else {}
            player = payload.get('player', {}) if isinstance(payload, dict) else {}
            matches_analyzed = self._to_int(summary.get('matchesAnalyzed'))
            total_sequences = self._to_int(summary.get('totalSequences'))
            has_coverage = matches_analyzed > 0 and total_sequences > 0

            return {
                'player_id': player_id,
                'playerName': player.get('name') if isinstance(player, dict) else None,
                'hasCoverage': has_coverage,
                'coverageState': 'sequence-ready' if has_coverage else 'profile-only',
                'matchesAnalyzed': matches_analyzed,
                'totalSequences': total_sequences,
                'shotEndings': self._to_int(summary.get('shotEndings')),
                'goals': self._to_int(summary.get('goals')),
            }

        items = await asyncio.gather(*(build_item(player_id) for player_id in normalized_player_ids))

        return {
            'items': items,
            'last_updated': datetime.now().isoformat(),
        }

    @staticmethod
    def _event_type(raw_event: Dict[str, Any]) -> str:
        return str(raw_event.get('type_name') or '').lower()

    def _player_metrics(self, player: Dict[str, Any], stats: Dict[str, Any]) -> Dict[str, Any]:
        goals = self._to_int(self._extract_stat_value(stats, 'goals'))
        assists = self._to_int(self._extract_stat_value(stats, 'goal_assist', 'assists'))
        appearances = self._to_int(self._extract_stat_value(stats, 'appearances', 'matches', 'games_played'))
        pass_accuracy = self._pass_accuracy(stats)
        has_event_signal = appearances > 0 or goals > 0 or assists > 0 or pass_accuracy > 0
        rating = round(
            max(
                0.0,
                min(
                    10.0,
                    6.0 + (goals * 0.35) + (assists * 0.25) + ((pass_accuracy / 100) * 2.0),
                ),
            ),
            2,
        ) if has_event_signal else None

        return {
            'goals': goals,
            'assists': assists,
            'appearances': appearances,
            'passAccuracy': pass_accuracy,
            'rating': rating,
            'club': player.get('club') or player.get('team_name') or player.get('teamName'),
            'position': player.get('position') or player.get('detailed_position') or player.get('detailedPosition'),
            'age': player.get('age') or self._derive_age(player.get('birth_date') or player.get('birthDate')),
        }

    def _team_metrics(self, team: Dict[str, Any], stats: Dict[str, Any], matches: List[Dict[str, Any]], team_id: str) -> Dict[str, Any]:
        form = self._team_form(matches, team_id)
        goals_for = 0
        goals_against = 0
        counted_matches = 0

        for match in matches:
            goals = self._team_goals(match, team_id)
            if goals is None:
                continue
            goals_for += goals[0]
            goals_against += goals[1]
            counted_matches += 1

        return {
            'matchesAnalyzed': counted_matches,
            'avgGoalsFor': round(goals_for / counted_matches, 2) if counted_matches else 0.0,
            'avgGoalsAgainst': round(goals_against / counted_matches, 2) if counted_matches else 0.0,
            'form': form,
            'passAccuracy': self._pass_accuracy(stats),
            'manager': team.get('manager'),
        }

    @staticmethod
    def _team_goals(match: Dict[str, Any], team_id: str) -> Optional[tuple[int, int]]:
        home_team_id = str(match.get('homeTeamID', match.get('home_team_id', '')))
        away_team_id = str(match.get('awayTeamID', match.get('away_team_id', '')))
        home_score = AnalyticsHandler._to_int(match.get('homeScore', match.get('home_score')))
        away_score = AnalyticsHandler._to_int(match.get('awayScore', match.get('away_score')))

        if team_id == home_team_id:
            return home_score, away_score
        if team_id == away_team_id:
            return away_score, home_score
        return None

    def _team_form(self, matches: List[Dict[str, Any]], team_id: str) -> List[str]:
        form: List[str] = []
        for match in self._sort_matches(matches)[:5]:
            goals = self._team_goals(match, team_id)
            if goals is None:
                continue
            if goals[0] > goals[1]:
                form.append('W')
            elif goals[0] < goals[1]:
                form.append('L')
            else:
                form.append('D')
        return form

    @staticmethod
    def _filter_matches(matches: List[Dict[str, Any]], competition: Optional[str]) -> List[Dict[str, Any]]:
        if not competition or competition == 'all':
            return matches

        if competition.isdigit():
            return [
                match for match in matches
                if str(match.get('competitionID', match.get('competition_id', ''))) == competition
            ]

        competition_lower = competition.lower()
        return [
            match for match in matches
            if competition_lower in str(match.get('competition', '')).lower()
        ]

    @staticmethod
    def _trend_label(match: Dict[str, Any], period: str) -> str:
        parsed = AnalyticsHandler._parse_date(match.get('date'))
        if not parsed:
            return 'unknown'
        if period == 'week':
            iso_year, iso_week, _ = parsed.isocalendar()
            return f'{iso_year}-W{iso_week:02d}'
        return parsed.strftime('%Y-%m')

    @staticmethod
    def _compute_average_goals(matches: List[Dict[str, Any]]) -> Optional[float]:
        if not matches:
            return None

        total_goals = 0
        counted_matches = 0

        for match in matches:
            home_goals = match.get('homeScore', match.get('home_score'))
            away_goals = match.get('awayScore', match.get('away_score'))

            if isinstance(home_goals, (int, float)) and isinstance(away_goals, (int, float)):
                total_goals += home_goals + away_goals
                counted_matches += 1

        if counted_matches == 0:
            return None

        return round(total_goals / counted_matches, 2)

    async def _enrich_players_with_details(self, players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich player data with names, positions, and team info from player service"""
        if not players:
            return players
        
        # Extract player IDs
        player_ids = set()
        for player in players:
            pid = player.get('player_id')
            if pid:
                player_ids.add(str(pid))
        
        if not player_ids:
            return players
        
        # Fetch player details in parallel for all IDs
        player_details = {}
        tasks = []
        for pid in list(player_ids)[:20]:  # Limit to 20 concurrent requests
            tasks.append(self._get_json(f"{self.player_service_url}/api/v2/players/{pid}"))
        
        if tasks:
            results = await asyncio.gather(*tasks)
            for i, pid in enumerate(list(player_ids)[:20]):
                detail = self._unwrap_data(results[i]) if i < len(results) else {}
                player_details[str(pid)] = detail
        
        # Enrich players with fetched details
        enriched = []
        for player in players:
            pid = str(player.get('player_id', ''))
            details = player_details.get(pid, {})
            
            enriched_player = {
                **player,
                'player_name': details.get('name') or player.get('player_name'),
                'player_position': details.get('position') or player.get('player_position'),
                'player_team': details.get('team') or details.get('teamName') or player.get('player_team'),
            }
            enriched.append(enriched_player)
        
        return enriched

    async def _enrich_matches_with_team_names(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich match data with team names from team service"""
        if not matches:
            return matches
        
        # Extract team IDs
        team_ids = set()
        for match in matches:
            home_id = match.get('home_team_id', match.get('homeTeamID'))
            away_id = match.get('away_team_id', match.get('awayTeamID'))
            if home_id:
                team_ids.add(str(home_id))
            if away_id:
                team_ids.add(str(away_id))
        
        if not team_ids:
            return matches
        
        # Fetch team details
        team_details = {}
        tasks = []
        for tid in list(team_ids)[:30]:  # Limit to 30 concurrent requests
            tasks.append(self._get_json(f"{self.team_service_url}/api/v2/teams/{tid}"))
        
        if tasks:
            results = await asyncio.gather(*tasks)
            for i, tid in enumerate(list(team_ids)[:30]):
                detail = self._unwrap_data(results[i]) if i < len(results) else {}
                team_details[str(tid)] = detail
        
        # Enrich matches with team names
        enriched = []
        for match in matches:
            home_id = str(match.get('home_team_id', match.get('homeTeamID', '')))
            away_id = str(match.get('away_team_id', match.get('awayTeamID', '')))
            
            home_detail = team_details.get(home_id, {})
            away_detail = team_details.get(away_id, {})
            
            enriched_match = {
                **match,
                'home_team_name': home_detail.get('name') or match.get('home_team_name'),
                'away_team_name': away_detail.get('name') or match.get('away_team_name'),
            }
            enriched.append(enriched_match)
        
        return enriched

    async def get_overview(self, season: Optional[str] = None) -> Dict[str, Any]:
        started = datetime.now()
        players_payload, matches_payload, teams_payload, top_players_payload, top_teams_payload = await asyncio.gather(
            self._get_json(f"{self.player_service_url}/api/v2/players", params={"limit": 500}),
            self._get_json(f"{self.match_service_url}/api/v2/matches", params={"limit": 500}),
            self._get_json(f"{self.team_service_url}/api/v2/teams", params={"limit": 500}),
            self._get_json(f"{self.statistics_service_url}/api/v2/statistics/rankings/players", params={"stat_name": "goals", "limit": 5}),
            self._get_json(f"{self.statistics_service_url}/api/v2/statistics/rankings/teams", params={"stat_name": "goals", "limit": 5}),
        )

        players = self._extract_list(players_payload, 'players')
        teams = self._extract_list(teams_payload, 'teams')
        matches = self._extract_list(matches_payload, 'matches')
        top_players = self._unwrap_data(top_players_payload) or []
        top_teams = self._unwrap_data(top_teams_payload) or []

        if not isinstance(top_players, list):
            top_players = []
        if not isinstance(top_teams, list):
            top_teams = []

        if not top_players:
            top_players = [{"name": player.get("name"), "value": 0, "club": player.get("club")} for player in players[:5]]
        if not top_teams:
            top_teams = [{"name": team.get("name"), "value": 0} for team in teams[:5]]

        # Enrich top players with detailed information
        top_players = await self._enrich_players_with_details(top_players)
        
        # Sort and get recent matches, then enrich with team names
        recent_matches_raw = self._sort_matches(matches)[:5]
        recent_matches = await self._enrich_matches_with_team_names(recent_matches_raw)
        
        live_matches = [match for match in matches if str(match.get('status', '')).lower() == 'live']
        complete_players = [player for player in players if player.get('name') and player.get('position') and player.get('club')]
        model_accuracy = round((len(complete_players) / len(players)) * 100, 2) if players else 0.0
        transfer_predictions = len(top_players)
        response_time = int((datetime.now() - started).total_seconds() * 1000)

        summary = {
            "totalPlayers": len(players),
            "totalTeams": len(teams),
            "totalMatches": len(matches),
            "avgGoalsPerMatch": self._compute_average_goals(matches) or 0.0,
            "liveMatches": len(live_matches),
            "recentActivity": len(recent_matches),
            "activeScouts": len(teams),
            "scoutingReports": len(top_players) + len(top_teams),
            "modelAccuracy": model_accuracy,
            "transferPredictions": transfer_predictions,
            "responseTime": response_time,
            "season": season,
        }

        return {
            "title": "Overview Dashboard",
            "summary": summary,
            "data": summary,
            "topPlayers": top_players,
            "topTeams": top_teams,
            "recentMatches": recent_matches,
            "predictions": {
                "total": transfer_predictions,
                "accuracy": model_accuracy,
            },
            "modelAccuracy": model_accuracy,
            "activeScouts": summary["activeScouts"],
            "transferPredictions": transfer_predictions,
            "responseTime": response_time,
            "sources": {
                "players": "player-service",
                "teams": "team-service",
                "matches": "match-service",
            },
            "last_updated": datetime.now().isoformat()
        }

    async def get_team_dashboard(self, team_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        team_payload, stats_payload, matches_payload, squad_payload = await asyncio.gather(
            self._get_json(f"{self.team_service_url}/api/v2/teams/{team_id}"),
            self._get_json(f"{self.statistics_service_url}/api/v2/statistics/team/{team_id}"),
            self._get_json(f"{self.match_service_url}/api/v2/matches/team/{team_id}", params={"limit": 20}),
            self._get_json(f"{self.team_service_url}/api/v2/teams/{team_id}/squad"),
        )

        team = self._unwrap_data(team_payload) or {}
        stats = self._stats_dict(stats_payload)
        matches = self._extract_list(matches_payload, 'matches')
        squad = self._unwrap_data(squad_payload)
        squad = squad if isinstance(squad, list) else []
        summary = self._team_metrics(team, stats, matches, team_id)

        return {
            "team_id": team_id,
            "season": season or "2023-2024",
            "team": team,
            "statistics": stats,
            "recentMatches": self._sort_matches(matches)[:5],
            "squad": squad,
            "summary": {
                **summary,
                "squadSize": len(squad),
            },
            "last_updated": datetime.now().isoformat(),
        }

    async def get_player_dashboard(self, player_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        cache_key = f"{player_id}#{season or 'current'}"
        
        # Check cache first
        cached = self._get_cached(self._player_dashboard_cache, cache_key)
        if cached:
            return cached
        
        player_payload = await self._get_json(f"{self.player_service_url}/api/v2/players/{player_id}")
        player = self._unwrap_data(player_payload) or {}

        stats_payload: Dict[str, Any] = {}
        for stats_player_id in self._player_stats_candidates(player_id, player):
            stats_payload = await self._get_json(f"{self.statistics_service_url}/api/v2/statistics/player/{stats_player_id}")
            if self._stats_dict(stats_payload):
                break

        stats = self._stats_dict(stats_payload)
        summary = self._player_metrics(player, stats)

        result = {
            "player_id": player_id,
            "season": season or "2023-2024",
            "player": player,
            "statistics": stats,
            "summary": summary,
            "last_updated": datetime.now().isoformat(),
        }
        
        # Cache for 5 minutes
        self._set_cache(self._player_dashboard_cache, cache_key, result, ttl=300)
        return result

    async def get_league_trends(self, competition: str, metric: str, period: str) -> Dict[str, Any]:
        matches_payload = await self._get_json(
            f"{self.match_service_url}/api/v2/matches",
            params={"limit": 500},
        )
        matches = self._filter_matches(self._extract_list(matches_payload, 'matches'), competition)
        buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for match in matches:
            buckets[self._trend_label(match, period)].append(match)

        trends = []
        for label, bucket_matches in sorted(buckets.items()):
            total_home = sum(self._to_int(match.get('homeScore', match.get('home_score'))) for match in bucket_matches)
            total_away = sum(self._to_int(match.get('awayScore', match.get('away_score'))) for match in bucket_matches)
            match_count = len(bucket_matches)
            trends.append({
                'name': label,
                'league': competition,
                'metric': metric,
                'matchCount': match_count,
                'avgGoals': round((total_home + total_away) / match_count, 2) if match_count else 0.0,
                'avgHomeGoals': round(total_home / match_count, 2) if match_count else 0.0,
                'avgAwayGoals': round(total_away / match_count, 2) if match_count else 0.0,
            })

        return {
            'competition': competition,
            'metric': metric,
            'period': period,
            'trends': trends,
            'summary': {
                'matchCount': len(matches),
                'avgGoals': self._compute_average_goals(matches) or 0.0,
            },
            'last_updated': datetime.now().isoformat(),
        }
            
    async def get_team_rankings(self, competition: str, metric: str, limit: int) -> Dict[str, Any]:
        params: Dict[str, Any] = {"stat_name": metric, "limit": limit}
        if competition.isdigit():
            params["competition_id"] = int(competition)

        payload = await self._get_json(
            f"{self.statistics_service_url}/api/v2/statistics/rankings/teams",
            params=params,
        )
        return {
            "competition": competition,
            "metric": metric,
            "rankings": self._unwrap_data(payload) or [],
        }
            
    async def get_player_rankings(self, metric: str, position: Optional[str], limit: int) -> Dict[str, Any]:
        params: Dict[str, Any] = {"stat_name": metric, "limit": limit}
        if position:
            params["position"] = position

        payload = await self._get_json(
            f"{self.statistics_service_url}/api/v2/statistics/rankings/players",
            params=params,
        )
        return {
            "metric": metric,
            "position": position,
            "rankings": self._unwrap_data(payload) or [],
        }

    async def get_advanced_metrics(self, match_id: str, time_bucket: str = "5m") -> Dict[str, Any]:
        # Get match data in parallel with events
        match_payload = await self._get_json(f"{self.match_service_url}/api/v2/matches/{match_id}")
        
        # Try direct MongoDB access for events first for better performance
        events = await self._get_events_from_mongodb(match_id)
        
        # Fall back to Match Service if MongoDB unavailable
        if not events:
            logger.info(f"Falling back to Match Service for events in match {match_id}")
            events_payload = await self._get_json(f"{self.match_service_url}/api/v2/matches/{match_id}/events")
            events = self._unwrap_data(events_payload)

        match = self._unwrap_data(match_payload) or {}
        if not isinstance(events, list):
            events = []

        bucket_minutes = self._bucket_minutes(time_bucket)
        event_types = Counter()
        team_counts = Counter()
        timeline: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
            'events': 0,
            'goals': 0,
            'shots': 0,
            'passes': 0,
            'cards': 0,
        })

        goals = shots = passes = cards = fouls = substitutions = 0
        player_ids = set()
        team_ids = set()

        for event in events:
            event_type = self._event_type(event)
            event_types[event_type] += 1
            if event.get('player_id') is not None:
                player_ids.add(str(event.get('player_id')))
            if event.get('team_id') is not None:
                team_id = str(event.get('team_id'))
                team_ids.add(team_id)
                team_counts[team_id] += 1

            minute = self._to_int(event.get('minute'))
            bucket = (minute // bucket_minutes) * bucket_minutes
            timeline_bucket = timeline[bucket]
            timeline_bucket['events'] += 1

            if 'goal' in event_type or bool(event.get('is_goal')):
                goals += 1
                timeline_bucket['goals'] += 1
            if 'shot' in event_type:
                shots += 1
                timeline_bucket['shots'] += 1
            if 'pass' in event_type:
                passes += 1
                timeline_bucket['passes'] += 1
            if 'card' in event_type or event_type in {'yellow card', 'red card'}:
                cards += 1
                timeline_bucket['cards'] += 1
            if 'foul' in event_type:
                fouls += 1
            if 'substitution' in event_type:
                substitutions += 1

        timeline_rows = [
            {
                'bucketStartMinute': bucket,
                'bucketEndMinute': bucket + bucket_minutes,
                **values,
            }
            for bucket, values in sorted(timeline.items())
        ]

        return {
            "match_id": match_id,
            "time_bucket": time_bucket,
            "match": match,
            "event_count": len(events),
            "events_available": bool(events),
            "metrics": {
                'goals': goals,
                'shots': shots,
                'passes': passes,
                'cards': cards,
                'fouls': fouls,
                'substitutions': substitutions,
                'uniquePlayers': len(player_ids),
                'uniqueTeams': len(team_ids),
                'eventsByType': dict(event_types.most_common(10)),
                'eventsByTeam': dict(team_counts),
                'timeline': timeline_rows,
            },
            'last_updated': datetime.now().isoformat(),
        }

    async def get_team_insights(self, team_id: str) -> Dict[str, Any]:
        dashboard = await self.get_team_dashboard(team_id)
        summary = dashboard.get('summary', {})
        team = dashboard.get('team', {})
        insights = [
            {
                'title': 'Recent Form',
                'value': ''.join(summary.get('form', [])) or 'N/A',
                'description': f"Recent results for {team.get('name', team_id)} across the latest tracked matches.",
            },
            {
                'title': 'Attack vs Defence',
                'value': f"{summary.get('avgGoalsFor', 0)} / {summary.get('avgGoalsAgainst', 0)}",
                'description': 'Average goals scored and conceded per tracked match.',
            },
            {
                'title': 'Squad Depth',
                'value': summary.get('squadSize', 0),
                'description': 'Number of players currently available in the team read model.',
            },
        ]

        return {
            'team_id': team_id,
            'team': team,
            'summary': summary,
            'insights': insights,
            'last_updated': datetime.now().isoformat(),
        }

    async def get_player_insights(self, player_id: str) -> Dict[str, Any]:
        dashboard = await self.get_player_dashboard(player_id)
        summary = dashboard.get('summary', {})
        player = dashboard.get('player', {})
        insights = [
            {
                'title': 'Role Projection',
                'value': player.get('position') or player.get('detailed_position') or player.get('detailedPosition') or 'Unknown',
                'description': 'Primary role inferred from the canonical player read model.',
            },
            {
                'title': 'Contribution Output',
                'value': summary.get('goals', 0) + summary.get('assists', 0),
                'description': 'Combined goals and assists from tracked statistics.',
            },
            {
                'title': 'Distribution Quality',
                'value': summary.get('passAccuracy', 0),
                'description': 'Pass accuracy derived from tracked player statistics when available.',
            },
        ]

        return {
            'player_id': player_id,
            'player': player,
            'summary': summary,
            'insights': insights,
            'last_updated': datetime.now().isoformat(),
        }

    async def compare_players(self, player_ids: List[str], metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        metrics = metrics or ['goals', 'assists', 'passAccuracy', 'rating']
        profiles = []

        for player_id in player_ids:
            dashboard = await self.get_player_dashboard(player_id)
            profiles.append({
                'player_id': player_id,
                'player': dashboard.get('player', {}),
                'summary': dashboard.get('summary', {}),
            })

        metric_rows = []
        for metric in metrics:
            metric_rows.append({
                'metric': metric,
                'values': [profile.get('summary', {}).get(metric, 0) for profile in profiles],
            })

        return {
            'player_ids': player_ids,
            'players': profiles,
            'metrics': metric_rows,
            'last_updated': datetime.now().isoformat(),
        }

    async def compare_teams(self, team_ids: List[str], metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        metrics = metrics or ['avgGoalsFor', 'avgGoalsAgainst', 'squadSize']
        profiles = []

        for team_id in team_ids:
            dashboard = await self.get_team_dashboard(team_id)
            profiles.append({
                'team_id': team_id,
                'team': dashboard.get('team', {}),
                'summary': dashboard.get('summary', {}),
            })

        metric_rows = []
        for metric in metrics:
            metric_rows.append({
                'metric': metric,
                'values': [profile.get('summary', {}).get(metric, 0) for profile in profiles],
            })

        return {
            'team_ids': team_ids,
            'teams': profiles,
            'metrics': metric_rows,
            'last_updated': datetime.now().isoformat(),
        }

    async def get_pass_network(self, match_id: str) -> Dict[str, Any]:
        """
        Build a directed pass network for a match.

        Uses sequential event analysis: for consecutive same-team events within
        15 game-seconds, infers passer → receiver relationship.
        
        Queries events directly from MongoDB for better performance.
        Falls back to Match Service if MongoDB unavailable.
        """
        # Try direct MongoDB access first for better performance
        events = await self._get_events_from_mongodb(match_id)
        
        # Fall back to Match Service if MongoDB unavailable
        if not events:
            logger.info(f"Falling back to Match Service for events in match {match_id}")
            events_payload = await self._get_json(
                f"{self.match_service_url}/api/v2/matches/{match_id}/events"
            )
            events = self._unwrap_data(events_payload)
        if not isinstance(events, list):
            events = []

        # Collect and sort all events by game time
        timed_events = []
        for e in events:
            period = self._to_int(e.get("period"), default=1)
            minute = self._to_int(e.get("minute"), default=0)
            second = self._to_int(e.get("second"), default=0)
            game_second = (period - 1) * 5400 + minute * 60 + second
            timed_events.append({
                "player_id": str(e.get("player_id") or ""),
                "team_id": str(e.get("team_id") or ""),
                "minute": minute,
                "game_second": game_second,
                "type_name": str(e.get("type_name") or "").lower(),
            })
        timed_events.sort(key=lambda ev: ev["game_second"])

        # Filter to pass events only for zone/passer stats
        pass_events = [ev for ev in timed_events if ev["type_name"] == "pass"]

        # Build directed edges: for each pass, next same-team event within 15s = receiver
        edges: Dict[tuple, int] = defaultdict(int)
        player_pass_count: Dict[str, int] = defaultdict(int)
        player_team: Dict[str, str] = {}

        for i, evt in enumerate(timed_events):
            if evt["type_name"] != "pass":
                continue
            pid = evt["player_id"]
            tid = evt["team_id"]
            if pid:
                player_pass_count[pid] += 1
                player_team[pid] = tid

            # Search next events from same team
            for j in range(i + 1, min(i + 8, len(timed_events))):
                next_evt = timed_events[j]
                if next_evt["team_id"] != tid:
                    break  # possession changed
                if next_evt["game_second"] - evt["game_second"] > 15:
                    break
                receiver = next_evt["player_id"]
                if receiver and receiver != pid:
                    edges[(pid, receiver, tid)] += 1
                    break

        # Team pass totals
        team_passes: Dict[str, int] = defaultdict(int)
        for ev in pass_events:
            if ev["team_id"]:
                team_passes[ev["team_id"]] += 1

        total_passes = max(sum(team_passes.values()), 1)

        nodes = [
            {
                "player_id": pid,
                "team_id": player_team.get(pid, ""),
                "pass_count": count,
                "pass_share": round(count / total_passes, 3),
            }
            for pid, count in sorted(player_pass_count.items(), key=lambda x: -x[1])[:30]
        ]

        edge_list = [
            {
                "from_player": passer,
                "to_player": receiver,
                "team_id": tid,
                "weight": count,
            }
            for (passer, receiver, tid), count in sorted(edges.items(), key=lambda x: -x[1])
            if count >= 2
        ]

        possession = {
            tid: round(count / total_passes * 100, 1)
            for tid, count in team_passes.items()
        }

        return {
            "match_id": match_id,
            "total_passes": len(pass_events),
            "nodes": nodes,
            "edges": edge_list,
            "possession_pct": possession,
            "top_passers": nodes[:5],
            "last_updated": datetime.now().isoformat(),
        }

    async def get_tactical_metrics(self, match_id: str) -> Dict[str, Any]:
        """
        Compute tactical metrics from match events:
        - PPDA (Passes Per Defensive Action) per team
        - Possession zones: share of passes in each third of the pitch
        - Pressing intensity: pressure events per team
        """
        events_payload = await self._get_json(
            f"{self.match_service_url}/api/v2/matches/{match_id}/events"
        )
        events = self._unwrap_data(events_payload)
        if not isinstance(events, list):
            events = []

        # Discover teams
        team_ids: set = set()
        for e in events:
            tid = str(e.get("team_id") or "")
            if tid:
                team_ids.add(tid)
        teams = list(team_ids)

        DEFENSIVE_ACTIONS = {"tackle", "interception", "foul"}

        def _zone(x: float) -> str:
            if x <= 33:
                return "defensive"
            elif x <= 66:
                return "middle"
            else:
                return "attacking"

        team_stats: Dict[str, Dict[str, Any]] = {
            t: {
                "passes": 0,
                "passes_in_opp_half": 0,
                "def_actions": 0,
                "def_actions_in_opp_half": 0,
                "pressures": 0,
                "zones": {"defensive": 0, "middle": 0, "attacking": 0},
            }
            for t in teams
        }

        for e in events:
            tid = str(e.get("team_id") or "")
            if tid not in team_stats:
                continue
            loc = e.get("location") or {}
            x = self._to_float(loc.get("x"), default=50.0)
            evt_type = str(e.get("type_name") or "").lower()

            if evt_type == "pass":
                team_stats[tid]["passes"] += 1
                if x > 50:
                    team_stats[tid]["passes_in_opp_half"] += 1
                team_stats[tid]["zones"][_zone(x)] += 1
            elif evt_type in DEFENSIVE_ACTIONS:
                team_stats[tid]["def_actions"] += 1
                if x > 50:
                    team_stats[tid]["def_actions_in_opp_half"] += 1
            elif evt_type == "pressure":
                team_stats[tid]["pressures"] += 1

        tactical: Dict[str, Any] = {}
        for tid in teams:
            opp_passes_in_own_half = sum(
                team_stats[o]["passes"] - team_stats[o]["passes_in_opp_half"]
                for o in teams if o != tid
            )
            def_actions = max(team_stats[tid]["def_actions_in_opp_half"], 1)
            ppda = round(opp_passes_in_own_half / def_actions, 2)

            total_passes = max(team_stats[tid]["passes"], 1)
            zones_pct = {
                k: round(v / total_passes * 100, 1)
                for k, v in team_stats[tid]["zones"].items()
            }

            if ppda < 10:
                press_label = "high press"
            elif ppda < 20:
                press_label = "medium press"
            else:
                press_label = "low press"

            tactical[tid] = {
                "ppda": ppda,
                "press_style": press_label,
                "passes": team_stats[tid]["passes"],
                "defensive_actions": team_stats[tid]["def_actions"],
                "pressures": team_stats[tid]["pressures"],
                "possession_zones_pct": zones_pct,
            }

        return {
            "match_id": match_id,
            "teams": teams,
            "tactical_metrics": tactical,
            "last_updated": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # Player spatial analysis (cross-match)
    # ------------------------------------------------------------------

    async def _get_player_events(
        self,
        player_id: str,
        player: Dict[str, Any],
        event_type: Optional[str] = None,
        last_n_matches: int = 10,
    ) -> List[Dict[str, Any]]:
        """Fetch all events for a player across recent matches directly from MongoDB."""
        candidate_values = self._player_event_candidates(player_id, player)
        if not candidate_values:
            return []

        # Build both string and int variants for match_events lookup
        str_candidates = [str(v) for v in candidate_values]
        int_candidates = [int(v) for v in candidate_values if str(v).isdigit()]
        all_candidates: List[Any] = list(dict.fromkeys(str_candidates + int_candidates))

        recent_matches = await self._get_recent_player_matches(player_id, player, limit=last_n_matches)
        if not recent_matches:
            return []

        match_ids: List[Any] = []
        for m in recent_matches:
            mid = str(m.get('id') or m.get('uID') or m.get('matchID') or '').strip()
            if mid:
                match_ids.append(mid)
                if mid.isdigit():
                    match_ids.append(int(mid))

        if not match_ids:
            return []

        and_clauses: List[Dict[str, Any]] = [
            {'$or': [
                {'player_id': {'$in': all_candidates}},
                {'playerID': {'$in': all_candidates}},
            ]},
            {'$or': [
                {'matchID': {'$in': match_ids}},
                {'match_id': {'$in': match_ids}},
            ]},
        ]
        if event_type:
            and_clauses.append({'type_name': event_type})

        try:
            events = await self.db['match_events'].find(
                {'$and': and_clauses}
            ).to_list(length=10_000)
            for ev in events:
                ev.pop('_id', None)
            return events
        except Exception as exc:
            logger.error('Failed to fetch player events for %s: %s', player_id, exc)
            return []

    @staticmethod
    def _compute_xg_heuristic(x: float, y: float) -> float:
        import math
        dist = math.sqrt((x - 100) ** 2 + (y - 50) ** 2)
        return round(math.exp(-dist / 30), 4)

    @staticmethod
    def _is_progressive_pass(start_x: float, end_x: float) -> bool:
        """Pass that gains ≥15 x-units toward goal in the middle or attacking third."""
        return (end_x - start_x) >= 15 and (start_x >= 33 or end_x >= 50)

    async def get_player_shot_map(
        self, player_id: str, last_n_matches: int = 10
    ) -> Dict[str, Any]:
        dashboard = await self.get_player_dashboard(player_id)
        player = dashboard.get('player', {})
        events = await self._get_player_events(player_id, player, event_type='shot', last_n_matches=last_n_matches)

        shots = []
        total_xg = 0.0
        for ev in events:
            loc = ev.get('location') or {}
            x = self._to_float(loc.get('x'), default=0.0)
            y = self._to_float(loc.get('y'), default=0.0)
            xg = self._compute_xg_heuristic(x, y)
            is_goal = bool(ev.get('is_goal'))
            shots.append({
                'match_id': str(ev.get('matchID') or ev.get('match_id') or ''),
                'minute': self._to_int(ev.get('minute')),
                'period': self._to_int(ev.get('period'), default=1),
                'x': round(x, 2),
                'y': round(y, 2),
                'is_goal': is_goal,
                'xg': xg,
                'type_name': ev.get('type_name') or 'shot',
            })
            total_xg += xg

        goals = sum(1 for s in shots if s['is_goal'])
        n = len(shots)
        return {
            'player_id': player_id,
            'player': player,
            'shots': shots,
            'summary': {
                'total_shots': n,
                'goals': goals,
                'total_xg': round(total_xg, 3),
                'conversion_rate': round(goals / n, 3) if n else 0,
                'xg_per_shot': round(total_xg / n, 3) if n else 0,
                'xg_overperformance': round(goals - total_xg, 3),
            },
            'last_updated': datetime.now().isoformat(),
        }

    async def get_player_heat_map(
        self,
        player_id: str,
        event_type: Optional[str] = None,
        last_n_matches: int = 10,
    ) -> Dict[str, Any]:
        dashboard = await self.get_player_dashboard(player_id)
        player = dashboard.get('player', {})
        events = await self._get_player_events(
            player_id, player, event_type=event_type, last_n_matches=last_n_matches
        )

        points = []
        for ev in events:
            loc = ev.get('location') or {}
            x = self._optional_number(loc.get('x'))
            y = self._optional_number(loc.get('y'))
            if x is None or y is None:
                continue
            points.append({
                'x': round(x, 2),
                'y': round(y, 2),
                'event_type': ev.get('type_name') or 'unknown',
                'minute': self._to_int(ev.get('minute')),
                'intensity': 1,
            })

        return {
            'player_id': player_id,
            'player': player,
            'data': points,
            'event_type': event_type or 'all',
            'total_events': len(points),
            'last_updated': datetime.now().isoformat(),
        }

    async def get_player_pass_map(
        self, player_id: str, last_n_matches: int = 10
    ) -> Dict[str, Any]:
        dashboard = await self.get_player_dashboard(player_id)
        player = dashboard.get('player', {})
        events = await self._get_player_events(player_id, player, event_type='pass', last_n_matches=last_n_matches)

        passes = []
        for ev in events:
            loc = ev.get('location') or {}
            x = self._optional_number(loc.get('x'))
            y = self._optional_number(loc.get('y'))
            if x is None or y is None:
                continue

            end_loc = self._get_qualifier_end_location(ev)
            end_x = end_loc.get('x') if end_loc else None
            end_y = end_loc.get('y') if end_loc else None

            is_progressive = (
                end_x is not None and self._is_progressive_pass(x, end_x)
            )
            raw = ev.get('raw_event') or {}
            is_successful = bool(raw.get('outcome') in (1, '1', True))

            passes.append({
                'match_id': str(ev.get('matchID') or ev.get('match_id') or ''),
                'start_x': round(x, 2),
                'start_y': round(y, 2),
                'end_x': round(end_x, 2) if end_x is not None else None,
                'end_y': round(end_y, 2) if end_y is not None else None,
                'is_successful': is_successful,
                'is_progressive': is_progressive,
                'minute': self._to_int(ev.get('minute')),
            })

        total = len(passes)
        successful = sum(1 for p in passes if p['is_successful'])
        progressive = sum(1 for p in passes if p['is_progressive'])
        return {
            'player_id': player_id,
            'player': player,
            'passes': passes,
            'summary': {
                'total_passes': total,
                'successful_passes': successful,
                'pass_accuracy': round(successful / total * 100, 1) if total else 0,
                'progressive_passes': progressive,
                'progressive_pct': round(progressive / total * 100, 1) if total else 0,
            },
            'last_updated': datetime.now().isoformat(),
        }

    async def get_match_player_stats(self, match_id: str, player_id: str) -> Dict[str, Any]:
        """Aggregate per-player per-match stats from F24 events."""
        import math

        events = await self._get_events_from_mongodb(match_id)
        pid_variants = self._identifier_variants(player_id)
        pid_set: set = set(pid_variants)
        for v in list(pid_variants):
            if v.isdigit():
                pid_set.add(int(v))

        player_events = [
            ev for ev in events
            if str(ev.get('player_id') or '') in pid_set
            or str(ev.get('playerID') or '') in pid_set
            or ev.get('player_id') in pid_set
            or ev.get('playerID') in pid_set
        ]

        counts: Dict[str, Any] = {
            'passes': 0, 'successful_passes': 0,
            'shots': 0, 'shots_on_target': 0, 'goals': 0, 'total_xg': 0.0,
            'tackles': 0, 'interceptions': 0, 'dribbles': 0,
            'fouls_committed': 0, 'fouls_won': 0,
            'yellow_cards': 0, 'red_cards': 0,
            'touches': 0, 'aerials_won': 0,
        }

        for ev in player_events:
            ev_type = str(ev.get('type_name') or '').lower()
            raw = ev.get('raw_event') or {}
            is_successful = bool(raw.get('outcome') in (1, '1', True))
            loc = ev.get('location') or {}
            counts['touches'] += 1

            if 'pass' in ev_type:
                counts['passes'] += 1
                if is_successful:
                    counts['successful_passes'] += 1
            elif ev_type in ('shot', 'attempt saved', 'miss', 'post'):
                counts['shots'] += 1
                x = self._to_float(loc.get('x'), default=50.0)
                y = self._to_float(loc.get('y'), default=50.0)
                counts['total_xg'] += self._compute_xg_heuristic(x, y)
                if bool(ev.get('is_goal')):
                    counts['goals'] += 1
                if ev_type == 'attempt saved' or is_successful:
                    counts['shots_on_target'] += 1
            elif 'tackle' in ev_type:
                counts['tackles'] += 1
            elif 'interception' in ev_type:
                counts['interceptions'] += 1
            elif 'take on' in ev_type or 'dribble' in ev_type:
                counts['dribbles'] += 1
            elif 'foul committed' in ev_type:
                counts['fouls_committed'] += 1
            elif 'foul' in ev_type:
                counts['fouls_won'] += 1
            elif 'yellow card' in ev_type:
                counts['yellow_cards'] += 1
            elif 'red card' in ev_type:
                counts['red_cards'] += 1
            elif 'aerial' in ev_type and is_successful:
                counts['aerials_won'] += 1

        counts['pass_accuracy'] = (
            round(counts['successful_passes'] / counts['passes'] * 100, 1)
            if counts['passes'] else 0
        )
        counts['total_xg'] = round(counts['total_xg'], 3)

        return {
            'match_id': match_id,
            'player_id': player_id,
            'events_count': len(player_events),
            'stats': counts,
            'last_updated': datetime.now().isoformat(),
        }

    async def close(self):
        await self.client.aclose()

