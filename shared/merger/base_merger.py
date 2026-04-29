"""
Base Merger

Abstract base class for all entity mergers.
Provides common merge functionality and conflict resolution logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import yaml
from pathlib import Path

from shared.merger.strategies.merge_strategies import get_strategy, STRATEGY_REGISTRY
from shared.merger.conflict_detector import ConflictDetector, ConflictSeverity


class BaseMerger(ABC):
    """
    Abstract base class for merging entities from multiple providers

    This class provides common functionality for merging data:
    - Loading merge rules from YAML config
    - Applying merge strategies field-by-field
    - Detecting and logging conflicts
    - Quality metadata tracking

    Subclasses implement entity-specific logic:
    - MatchMerger
    - EventMerger
    - PlayerMerger
    - TeamMerger
    """

    def __init__(
        self,
        merge_rules_path: Optional[str] = None,
        conflict_detector: Optional[ConflictDetector] = None
    ):
        """
        Initialize base merger

        Args:
            merge_rules_path: Path to merge_rules.yaml config
                             If None, uses default: shared/config/merge_rules.yaml
            conflict_detector: ConflictDetector instance for logging conflicts
                              If None, creates a new instance
        """
        # Load merge rules
        if merge_rules_path is None:
            base_path = Path(__file__).parent.parent
            merge_rules_path = base_path / 'config' / 'merge_rules.yaml'

        self.merge_rules = self._load_merge_rules(merge_rules_path)

        # Conflict detector
        self.conflict_detector = conflict_detector or ConflictDetector()

        # Entity type (defined by subclass)
        self.entity_type = self.get_entity_type()

    @abstractmethod
    def get_entity_type(self) -> str:
        """
        Get entity type name

        Returns:
            Entity type ('match', 'event', 'player', 'team')
        """
        pass

    @abstractmethod
    def merge(
        self,
        primary_entity: Any,
        secondary_entity: Any,
        primary_provider: str = 'primary',
        secondary_provider: str = 'secondary'
    ) -> Any:
        """
        Merge two entities from different providers

        Args:
            primary_entity: Entity from primary provider
            secondary_entity: Entity from secondary provider
            primary_provider: Name of primary provider
            secondary_provider: Name of secondary provider

        Returns:
            Merged entity
        """
        pass

    # ========================================
    # MERGE CONFIGURATION
    # ========================================

    def _load_merge_rules(self, config_path: Path) -> Dict[str, Any]:
        """Load merge rules from YAML"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Return default rules if file not found
            return {
                'merge_rules': {},
                'conflict_logging': {
                    'enabled': True,
                    'log_threshold': 'medium'
                }
            }

    def _get_field_rule(self, field_name: str) -> Dict[str, Any]:
        """
        Get merge rule for a specific field

        Args:
            field_name: Field name

        Returns:
            Merge rule dict with strategy and parameters

        Example:
            rule = self._get_field_rule('home_score')
            → {
                'strategy': 'prefer_primary',
                'primary_provider': 'opta',
                'log_if_mismatch': True
            }
        """
        entity_rules = self.merge_rules.get('merge_rules', {}).get(self.entity_type, {})

        if field_name in entity_rules:
            return entity_rules[field_name]

        # Check for default rule
        if '_default' in entity_rules:
            return entity_rules['_default']

        # Global default: prefer primary
        return {'strategy': 'prefer_primary'}

    # ========================================
    # FIELD MERGING
    # ========================================

    def merge_field(
        self,
        field_name: str,
        primary_value: Any,
        secondary_value: Any,
        primary_provider: str,
        secondary_provider: str,
        entity_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Merge a single field using configured strategy

        Args:
            field_name: Name of field to merge
            primary_value: Value from primary provider
            secondary_value: Value from secondary provider
            primary_provider: Primary provider name
            secondary_provider: Secondary provider name
            entity_id: ID of entity (for conflict logging)
            context: Additional context

        Returns:
            Merged value

        Example:
            merged = self.merge_field(
                'home_score',
                primary_value=2,
                secondary_value=2,
                primary_provider='opta',
                secondary_provider='statsbomb'
            ) → 2
        """
        # Get merge rule for this field
        rule = self._get_field_rule(field_name)

        strategy_name = rule.get('strategy', 'prefer_primary')
        strategy_fn = get_strategy(strategy_name)

        # Build strategy kwargs from rule
        kwargs = {
            'primary_provider': primary_provider,
            'secondary_provider': secondary_provider
        }

        # Add rule parameters to kwargs
        for key, value in rule.items():
            if key != 'strategy' and key != 'log_if_mismatch':
                kwargs[key] = value

        # Apply strategy
        try:
            merged_value = strategy_fn(primary_value, secondary_value, **kwargs)
        except Exception as e:
            # Fall back to primary value on error
            print(f"Error applying strategy '{strategy_name}' to field '{field_name}': {e}")
            merged_value = primary_value

        # Detect and log conflicts
        if rule.get('log_if_mismatch', False) and self._should_log_conflict(primary_value, secondary_value):
            severity = self.conflict_detector.determine_severity(
                self.entity_type,
                field_name,
                primary_value,
                secondary_value
            )

            self.conflict_detector.log_conflict(
                entity_type=self.entity_type,
                entity_id=entity_id or 'unknown',
                field_name=field_name,
                primary_value=primary_value,
                secondary_value=secondary_value,
                primary_provider=primary_provider,
                secondary_provider=secondary_provider,
                severity=severity,
                merge_strategy_used=strategy_name,
                merged_value=merged_value,
                context=context
            )

        return merged_value

    def _should_log_conflict(self, primary_value: Any, secondary_value: Any) -> bool:
        """Check if conflict should be logged"""
        # Only log if values differ
        if primary_value == secondary_value:
            return False

        # Check if conflict logging is enabled
        conflict_config = self.merge_rules.get('conflict_logging', {})
        if not conflict_config.get('enabled', True):
            return False

        return True

    # ========================================
    # QUALITY METADATA
    # ========================================

    def build_quality_metadata(
        self,
        primary_entity: Any,
        secondary_entity: Any,
        primary_provider: str,
        secondary_provider: str,
        merge_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build quality metadata for merged entity

        Args:
            primary_entity: Primary entity
            secondary_entity: Secondary entity
            primary_provider: Primary provider name
            secondary_provider: Secondary provider name
            merge_stats: Optional merge statistics

        Returns:
            Quality metadata dict

        Example:
            metadata = self.build_quality_metadata(
                primary_entity, secondary_entity,
                'opta', 'statsbomb'
            )
            → {
                'data_sources': ['opta', 'statsbomb'],
                'completeness_score': 0.95,
                'conflicts_detected': 3,
                'last_updated': datetime.now()
            }
        """
        data_sources = [primary_provider, secondary_provider]

        # Calculate completeness score
        # (Percentage of non-null fields)
        completeness = self._calculate_completeness(primary_entity, secondary_entity)

        metadata = {
            'data_sources': data_sources,
            'completeness_score': completeness,
            'primary_source': primary_provider,
            'secondary_source': secondary_provider,
            'last_updated': datetime.now(),
            'merge_timestamp': datetime.now()
        }

        if merge_stats:
            metadata.update(merge_stats)

        return metadata

    def _calculate_completeness(self, primary: Any, secondary: Any) -> float:
        """Calculate data completeness score (0.0 to 1.0)"""
        # Count non-null fields from both entities
        if hasattr(primary, '__dict__'):
            primary_fields = {k: v for k, v in primary.__dict__.items() if v is not None}
            secondary_fields = {k: v for k, v in secondary.__dict__.items() if v is not None}

            total_fields = len(set(list(primary_fields.keys()) + list(secondary_fields.keys())))
            filled_fields = len(set(list(primary_fields.keys()) + list(secondary_fields.keys())))

            if total_fields == 0:
                return 0.0

            return filled_fields / total_fields
        else:
            return 1.0  # Default if not a dataclass

    # ========================================
    # PROVIDER DATA TRACKING
    # ========================================

    def merge_provider_data(
        self,
        primary_entity: Any,
        secondary_entity: Any,
        primary_provider: str,
        secondary_provider: str
    ) -> Dict[str, Any]:
        """
        Merge provider_data fields from both entities

        Args:
            primary_entity: Primary entity
            secondary_entity: Secondary entity
            primary_provider: Primary provider name
            secondary_provider: Secondary provider name

        Returns:
            Merged provider_data dict

        Example:
            merged = self.merge_provider_data(opta_match, sb_match, 'opta', 'statsbomb')
            → {
                'opta': {
                    'source': 'opta',
                    'last_updated': datetime(...),
                    'data': {...}
                },
                'statsbomb': {
                    'source': 'statsbomb',
                    'last_updated': datetime(...),
                    'data': {...}
                }
            }
        """
        provider_data = {}

        # Add primary provider data
        if hasattr(primary_entity, 'provider_data') and primary_entity.provider_data:
            provider_data.update(primary_entity.provider_data)

        # Add secondary provider data
        if hasattr(secondary_entity, 'provider_data') and secondary_entity.provider_data:
            provider_data.update(secondary_entity.provider_data)

        return provider_data

    def merge_provider_ids(
        self,
        primary_entity: Any,
        secondary_entity: Any,
        primary_provider: str,
        secondary_provider: str
    ) -> Dict[str, str]:
        """
        Merge provider_ids fields from both entities

        Args:
            primary_entity: Primary entity
            secondary_entity: Secondary entity
            primary_provider: Primary provider name
            secondary_provider: Secondary provider name

        Returns:
            Merged provider_ids dict

        Example:
            merged = self.merge_provider_ids(opta_player, sb_player, 'opta', 'statsbomb')
            → {'opta': 'p12345', 'statsbomb': 'sb98765'}
        """
        provider_ids = {}

        # Add primary provider ID
        if hasattr(primary_entity, 'provider_ids') and primary_entity.provider_ids:
            provider_ids.update(primary_entity.provider_ids)
        elif hasattr(primary_entity, 'external_id') and primary_entity.external_id:
            provider_ids[primary_provider] = primary_entity.external_id

        # Add secondary provider ID
        if hasattr(secondary_entity, 'provider_ids') and secondary_entity.provider_ids:
            provider_ids.update(secondary_entity.provider_ids)
        elif hasattr(secondary_entity, 'external_id') and secondary_entity.external_id:
            provider_ids[secondary_provider] = secondary_entity.external_id

        return provider_ids

    # ========================================
    # UTILITY
    # ========================================

    def flush_conflicts(self):
        """Flush conflict buffer to MongoDB"""
        self.conflict_detector.flush()
