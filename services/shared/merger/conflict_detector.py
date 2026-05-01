"""
Conflict Detector

Detects and logs conflicts between data from multiple providers.
Stores conflicts in MongoDB for later analysis and rule refinement.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import pymongo


class ConflictSeverity(Enum):
    """Severity level of conflicts"""
    LOW = "low"          # Minor differences (e.g., formatting)
    MEDIUM = "medium"    # Notable differences (e.g., coordinates off by <5)
    HIGH = "high"        # Significant differences (e.g., different event types)
    CRITICAL = "critical"  # Critical differences (e.g., different scores)


class ConflictDetector:
    """
    Detects and logs conflicts between provider data

    This class compares values from different providers and logs discrepancies
    to MongoDB for analysis. It helps identify:
    - Data quality issues
    - Provider-specific biases
    - Fields that need custom merge rules
    - Systematic differences between providers

    Usage:
        detector = ConflictDetector(mongo_uri='mongodb://localhost:27017')

        detector.log_conflict(
            entity_type='match',
            entity_id='match_123',
            field_name='home_score',
            primary_value=2,
            secondary_value=3,
            primary_provider='opta',
            secondary_provider='statsbomb',
            severity=ConflictSeverity.CRITICAL
        )

        # Get conflict stats
        stats = detector.get_conflict_stats()
    """

    def __init__(
        self,
        mongo_uri: str = 'mongodb://localhost:27017',
        db_name: str = 'scoutpro',
        collection_name: str = 'data_conflicts'
    ):
        """
        Initialize conflict detector

        Args:
            mongo_uri: MongoDB connection URI
            db_name: Database name
            collection_name: Collection name for storing conflicts
        """
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name

        # MongoDB connection (lazy loading)
        self._client: Optional[pymongo.MongoClient] = None
        self._db = None
        self._collection = None

        # In-memory conflict buffer (for batch inserts)
        self._conflict_buffer: List[Dict[str, Any]] = []
        self._buffer_size = 100  # Flush after 100 conflicts

    def _connect(self):
        """Lazy connect to MongoDB"""
        if self._client is None:
            self._client = pymongo.MongoClient(self.mongo_uri)
            self._db = self._client[self.db_name]
            self._collection = self._db[self.collection_name]

            # Create indexes for efficient querying
            self._collection.create_index([('entity_type', 1), ('field_name', 1)])
            self._collection.create_index([('timestamp', -1)])
            self._collection.create_index([('severity', 1)])
            self._collection.create_index([('primary_provider', 1), ('secondary_provider', 1)])

    # ========================================
    # CONFLICT LOGGING
    # ========================================

    def log_conflict(
        self,
        entity_type: str,
        entity_id: str,
        field_name: str,
        primary_value: Any,
        secondary_value: Any,
        primary_provider: str,
        secondary_provider: str,
        severity: ConflictSeverity = ConflictSeverity.MEDIUM,
        merge_strategy_used: Optional[str] = None,
        merged_value: Any = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log a conflict between two provider values

        Args:
            entity_type: Type of entity ('match', 'event', 'player', 'team')
            entity_id: ID of entity
            field_name: Name of conflicting field
            primary_value: Value from primary provider
            secondary_value: Value from secondary provider
            primary_provider: Name of primary provider
            secondary_provider: Name of secondary provider
            severity: Severity level of conflict
            merge_strategy_used: Strategy used to resolve conflict
            merged_value: Final merged value
            context: Additional context (e.g., match_id, competition_id)

        Example:
            detector.log_conflict(
                entity_type='event',
                entity_id='evt_123',
                field_name='x',
                primary_value=65.2,
                secondary_value=70.5,
                primary_provider='opta',
                secondary_provider='statsbomb',
                severity=ConflictSeverity.MEDIUM,
                merge_strategy_used='average',
                merged_value=67.85,
                context={'match_id': 'match_123'}
            )
        """
        conflict = {
            'entity_type': entity_type,
            'entity_id': entity_id,
            'field_name': field_name,
            'primary_value': self._serialize_value(primary_value),
            'secondary_value': self._serialize_value(secondary_value),
            'primary_provider': primary_provider,
            'secondary_provider': secondary_provider,
            'severity': severity.value,
            'merge_strategy_used': merge_strategy_used,
            'merged_value': self._serialize_value(merged_value),
            'difference': self._calculate_difference(primary_value, secondary_value),
            'context': context or {},
            'timestamp': datetime.now(),
            'resolved': merged_value is not None
        }

        # Add to buffer
        self._conflict_buffer.append(conflict)

        # Flush if buffer is full
        if len(self._conflict_buffer) >= self._buffer_size:
            self.flush()

    def log_multiple_conflicts(self, conflicts: List[Dict[str, Any]]):
        """
        Log multiple conflicts at once

        Args:
            conflicts: List of conflict dicts (same format as log_conflict args)

        Example:
            conflicts = [
                {
                    'entity_type': 'event',
                    'entity_id': 'evt_123',
                    'field_name': 'x',
                    'primary_value': 65.2,
                    'secondary_value': 70.5,
                    'primary_provider': 'opta',
                    'secondary_provider': 'statsbomb',
                    'severity': ConflictSeverity.MEDIUM
                },
                # ... more conflicts
            ]
            detector.log_multiple_conflicts(conflicts)
        """
        for conflict_dict in conflicts:
            self.log_conflict(**conflict_dict)

    def flush(self):
        """Flush conflict buffer to MongoDB"""
        if not self._conflict_buffer:
            return

        self._connect()

        try:
            self._collection.insert_many(self._conflict_buffer)
            self._conflict_buffer.clear()
        except Exception as e:
            print(f"Error flushing conflicts to MongoDB: {e}")

    # ========================================
    # CONFLICT DETECTION
    # ========================================

    def detect_conflict(
        self,
        field_name: str,
        primary_value: Any,
        secondary_value: Any,
        threshold: Optional[float] = None
    ) -> bool:
        """
        Detect if two values conflict

        Args:
            field_name: Name of field
            primary_value: Value from primary provider
            secondary_value: Value from secondary provider
            threshold: Numeric threshold for considering values different

        Returns:
            True if values conflict, False if they match

        Example:
            detect_conflict('home_score', 2, 2) → False
            detect_conflict('x', 65.2, 70.5, threshold=5.0) → True
        """
        # Handle None values
        if primary_value is None and secondary_value is None:
            return False
        if primary_value is None or secondary_value is None:
            return True

        # Handle numeric values with threshold
        if threshold is not None and isinstance(primary_value, (int, float)) and isinstance(secondary_value, (int, float)):
            return abs(primary_value - secondary_value) > threshold

        # Exact match
        return primary_value != secondary_value

    def determine_severity(
        self,
        entity_type: str,
        field_name: str,
        primary_value: Any,
        secondary_value: Any
    ) -> ConflictSeverity:
        """
        Determine severity of conflict

        Args:
            entity_type: Type of entity
            field_name: Field name
            primary_value: Value from primary provider
            secondary_value: Value from secondary provider

        Returns:
            ConflictSeverity level

        Example:
            determine_severity('match', 'home_score', 2, 3) → CRITICAL
            determine_severity('event', 'x', 65.2, 67.5) → LOW
        """
        # Critical fields (e.g., scores, results)
        critical_fields = {
            'match': ['home_score', 'away_score', 'status'],
            'event': ['event_type', 'player_id', 'team_id'],
            'player': ['name', 'birth_date'],
            'team': ['name']
        }

        if field_name in critical_fields.get(entity_type, []):
            return ConflictSeverity.CRITICAL

        # Numeric fields - calculate difference percentage
        if isinstance(primary_value, (int, float)) and isinstance(secondary_value, (int, float)):
            if primary_value == 0 or secondary_value == 0:
                return ConflictSeverity.HIGH

            diff_pct = abs(primary_value - secondary_value) / max(abs(primary_value), abs(secondary_value))

            if diff_pct > 0.2:  # >20% difference
                return ConflictSeverity.HIGH
            elif diff_pct > 0.1:  # >10% difference
                return ConflictSeverity.MEDIUM
            else:
                return ConflictSeverity.LOW

        # Default
        return ConflictSeverity.MEDIUM

    # ========================================
    # CONFLICT ANALYSIS
    # ========================================

    def get_conflict_stats(
        self,
        entity_type: Optional[str] = None,
        field_name: Optional[str] = None,
        primary_provider: Optional[str] = None,
        secondary_provider: Optional[str] = None,
        severity: Optional[ConflictSeverity] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get conflict statistics

        Args:
            entity_type: Filter by entity type
            field_name: Filter by field name
            primary_provider: Filter by primary provider
            secondary_provider: Filter by secondary provider
            severity: Filter by severity
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            Dict with conflict statistics

        Example:
            stats = detector.get_conflict_stats(
                entity_type='event',
                field_name='x',
                primary_provider='opta',
                secondary_provider='statsbomb'
            )
            → {
                'total_conflicts': 1523,
                'by_severity': {'low': 800, 'medium': 600, 'high': 100, 'critical': 23},
                'avg_difference': 3.2,
                'most_common_fields': [...]
            }
        """
        self._connect()

        # Build filter
        filter_dict = {}
        if entity_type:
            filter_dict['entity_type'] = entity_type
        if field_name:
            filter_dict['field_name'] = field_name
        if primary_provider:
            filter_dict['primary_provider'] = primary_provider
        if secondary_provider:
            filter_dict['secondary_provider'] = secondary_provider
        if severity:
            filter_dict['severity'] = severity.value
        if start_date or end_date:
            filter_dict['timestamp'] = {}
            if start_date:
                filter_dict['timestamp']['$gte'] = start_date
            if end_date:
                filter_dict['timestamp']['$lte'] = end_date

        # Total count
        total_conflicts = self._collection.count_documents(filter_dict)

        # Count by severity
        by_severity = {}
        for sev in ConflictSeverity:
            sev_filter = {**filter_dict, 'severity': sev.value}
            by_severity[sev.value] = self._collection.count_documents(sev_filter)

        # Most common fields
        pipeline = [
            {'$match': filter_dict},
            {'$group': {'_id': '$field_name', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        most_common_fields = list(self._collection.aggregate(pipeline))

        # Average numeric difference (where applicable)
        avg_diff_pipeline = [
            {'$match': {**filter_dict, 'difference.absolute': {'$exists': True}}},
            {'$group': {'_id': None, 'avg': {'$avg': '$difference.absolute'}}}
        ]
        avg_diff_result = list(self._collection.aggregate(avg_diff_pipeline))
        avg_difference = avg_diff_result[0]['avg'] if avg_diff_result else None

        return {
            'total_conflicts': total_conflicts,
            'by_severity': by_severity,
            'most_common_fields': most_common_fields,
            'avg_difference': avg_difference
        }

    def get_field_conflicts(self, entity_type: str, field_name: str, limit: int = 100) -> List[Dict]:
        """
        Get all conflicts for a specific field

        Args:
            entity_type: Entity type
            field_name: Field name
            limit: Max number of conflicts to return

        Returns:
            List of conflict documents
        """
        self._connect()

        return list(self._collection.find(
            {'entity_type': entity_type, 'field_name': field_name}
        ).sort('timestamp', -1).limit(limit))

    # ========================================
    # UTILITY METHODS
    # ========================================

    def _serialize_value(self, value: Any) -> Any:
        """Convert value to MongoDB-safe format"""
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, (list, dict)):
            return value
        else:
            return value

    def _calculate_difference(self, primary: Any, secondary: Any) -> Dict[str, Any]:
        """Calculate difference between two values"""
        diff_info = {
            'has_difference': primary != secondary
        }

        # Numeric difference
        if isinstance(primary, (int, float)) and isinstance(secondary, (int, float)):
            diff_info['absolute'] = abs(primary - secondary)
            diff_info['relative'] = abs(primary - secondary) / max(abs(primary), abs(secondary)) if max(abs(primary), abs(secondary)) > 0 else 0
            diff_info['percentage'] = diff_info['relative'] * 100

        # String difference (length)
        elif isinstance(primary, str) and isinstance(secondary, str):
            diff_info['length_diff'] = abs(len(primary) - len(secondary))

        return diff_info

    def __del__(self):
        """Flush remaining conflicts on destruction"""
        if hasattr(self, '_conflict_buffer') and self._conflict_buffer:
            self.flush()

        if hasattr(self, '_client') and self._client:
            self._client.close()
