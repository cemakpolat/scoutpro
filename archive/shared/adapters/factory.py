"""
Provider Factory

Creates adapter instances (mappers, connectors, parsers) based on provider name.
Supports dynamic loading of provider modules and caching.
"""

from typing import Dict, Type, Optional, Any
import yaml
import os
from pathlib import Path

from shared.adapters.base import BaseMapper, BaseConnector, BaseParser


class ProviderFactory:
    """
    Factory for creating provider adapters

    This factory dynamically loads provider modules and creates instances
    of mappers, connectors, and parsers based on provider name.

    Usage:
        factory = ProviderFactory()

        # Get Opta mapper
        opta_mapper = factory.get_mapper('opta')

        # Get Opta connector with config
        opta_connector = factory.get_connector('opta', {
            'db_name': 'statsfabrik',
            'competition_id': '8',
            'season_id': '2023'
        })

        # Get StatsBomb parser
        sb_parser = factory.get_parser('statsbomb')
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize factory

        Args:
            config_path: Path to providers.yaml config file
                        If None, uses default: shared/config/providers.yaml
        """
        # Cache for instantiated adapters
        self._mapper_cache: Dict[str, BaseMapper] = {}
        self._connector_cache: Dict[str, BaseConnector] = {}
        self._parser_cache: Dict[str, BaseParser] = {}

        # Load provider configuration
        if config_path is None:
            # Default path
            base_path = Path(__file__).parent.parent
            config_path = base_path / 'config' / 'providers.yaml'

        self.config = self._load_config(config_path)

        # Provider class mappings
        # Maps provider name → (module_path, class_name)
        self._provider_mappers = {
            'opta': ('shared.adapters.opta.opta_mapper', 'OptaMapper'),
            'statsbomb': ('shared.adapters.statsbomb.statsbomb_mapper', 'StatsBombMapper'),
            'wyscout': ('shared.adapters.wyscout.wyscout_mapper', 'WyscoutMapper'),
        }

        self._provider_connectors = {
            'opta': ('shared.adapters.opta.opta_connector', 'OptaConnector'),
            'statsbomb': ('shared.adapters.statsbomb.statsbomb_connector', 'StatsBombConnector'),
            'wyscout': ('shared.adapters.wyscout.wyscout_connector', 'WyscoutConnector'),
        }

        self._provider_parsers = {
            'opta': ('shared.adapters.opta.opta_parser', 'OptaParser'),
            'statsbomb': ('shared.adapters.statsbomb.statsbomb_parser', 'StatsBombParser'),
            'wyscout': ('shared.adapters.wyscout.wyscout_parser', 'WyscoutParser'),
        }

    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load provider configuration from YAML"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Return default config if file not found
            return {
                'provider_priority': {
                    'global': ['opta', 'statsbomb', 'wyscout']
                }
            }

    # ========================================
    # MAPPER FACTORY
    # ========================================

    def get_mapper(
        self,
        provider: str,
        config: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> BaseMapper:
        """
        Get mapper for provider

        Args:
            provider: Provider name ('opta', 'statsbomb', 'wyscout')
            config: Optional configuration dict for mapper
            use_cache: Whether to use cached instance (default: True)

        Returns:
            Mapper instance implementing BaseMapper

        Raises:
            ValueError: If provider not supported
            ImportError: If provider module cannot be loaded

        Example:
            mapper = factory.get_mapper('opta')
            event = mapper.map_event(raw_opta_event)
        """
        if use_cache and provider in self._mapper_cache:
            return self._mapper_cache[provider]

        if provider not in self._provider_mappers:
            raise ValueError(
                f"Provider '{provider}' not supported. "
                f"Available providers: {list(self._provider_mappers.keys())}"
            )

        module_path, class_name = self._provider_mappers[provider]
        mapper_class = self._load_class(module_path, class_name)

        # Instantiate mapper
        mapper = mapper_class(config) if config else mapper_class()

        if use_cache:
            self._mapper_cache[provider] = mapper

        return mapper

    # ========================================
    # CONNECTOR FACTORY
    # ========================================

    def get_connector(
        self,
        provider: str,
        config: Optional[Dict[str, Any]] = None,
        use_cache: bool = False
    ) -> BaseConnector:
        """
        Get connector for provider

        Args:
            provider: Provider name ('opta', 'statsbomb', 'wyscout')
            config: Configuration dict for connector (often required)
            use_cache: Whether to use cached instance (default: False)
                      Note: Connectors often have stateful connections,
                      so caching is disabled by default

        Returns:
            Connector instance implementing BaseConnector

        Raises:
            ValueError: If provider not supported or config missing
            ImportError: If provider module cannot be loaded

        Example:
            connector = factory.get_connector('opta', {
                'db_name': 'statsfabrik',
                'competition_id': '8',
                'season_id': '2023'
            })
            events = await connector.fetch_match_events('g2187923')
        """
        if use_cache and provider in self._connector_cache:
            return self._connector_cache[provider]

        if provider not in self._provider_connectors:
            raise ValueError(
                f"Provider '{provider}' not supported. "
                f"Available providers: {list(self._provider_connectors.keys())}"
            )

        module_path, class_name = self._provider_connectors[provider]
        connector_class = self._load_class(module_path, class_name)

        # Instantiate connector (usually requires config)
        if config is None:
            # Try to get default config from providers.yaml
            config = self.config.get('providers', {}).get(provider, {})

        connector = connector_class(config)

        if use_cache:
            self._connector_cache[provider] = connector

        return connector

    # ========================================
    # PARSER FACTORY
    # ========================================

    def get_parser(
        self,
        provider: str,
        use_cache: bool = True
    ) -> BaseParser:
        """
        Get parser for provider

        Args:
            provider: Provider name ('opta', 'statsbomb', 'wyscout')
            use_cache: Whether to use cached instance (default: True)

        Returns:
            Parser instance implementing BaseParser

        Raises:
            ValueError: If provider not supported
            ImportError: If provider module cannot be loaded

        Example:
            parser = factory.get_parser('statsbomb')
            events = parser.parse_events(json_string)
        """
        if use_cache and provider in self._parser_cache:
            return self._parser_cache[provider]

        if provider not in self._provider_parsers:
            raise ValueError(
                f"Provider '{provider}' not supported. "
                f"Available providers: {list(self._provider_parsers.keys())}"
            )

        module_path, class_name = self._provider_parsers[provider]
        parser_class = self._load_class(module_path, class_name)

        # Instantiate parser
        parser = parser_class()

        if use_cache:
            self._parser_cache[provider] = parser

        return parser

    # ========================================
    # PROVIDER MANAGEMENT
    # ========================================

    def get_provider_priority(
        self,
        competition_id: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> list:
        """
        Get provider priority list based on context

        Args:
            competition_id: Competition ID (e.g., '55' for Champions League)
            event_type: Event type (e.g., 'shot', 'pass')

        Returns:
            Ordered list of provider names by priority

        Example:
            # Global priority
            priority = factory.get_provider_priority()
            # → ['opta', 'statsbomb', 'wyscout']

            # Competition-specific priority
            priority = factory.get_provider_priority(competition_id='55')
            # → ['statsbomb', 'opta']  (Champions League)

            # Event-type priority
            priority = factory.get_provider_priority(event_type='shot')
            # → ['statsbomb', 'opta']  (StatsBomb has better xG)
        """
        priority_config = self.config.get('provider_priority', {})

        # Check event type priority first
        if event_type:
            by_event = priority_config.get('by_event_type', {})
            if event_type in by_event:
                return by_event[event_type]

        # Check competition priority
        if competition_id:
            by_comp = priority_config.get('by_competition', {})
            if competition_id in by_comp:
                return by_comp[competition_id]

        # Fall back to global priority
        return priority_config.get('global', ['opta', 'statsbomb', 'wyscout'])

    def get_supported_providers(self) -> list:
        """Get list of all supported provider names"""
        return list(self._provider_mappers.keys())

    def is_provider_supported(self, provider: str) -> bool:
        """Check if provider is supported"""
        return provider in self._provider_mappers

    def register_provider(
        self,
        provider: str,
        mapper_module: str,
        mapper_class: str,
        connector_module: str,
        connector_class: str,
        parser_module: Optional[str] = None,
        parser_class: Optional[str] = None
    ):
        """
        Register a new provider dynamically

        This allows adding custom providers without modifying factory code.

        Args:
            provider: Provider name
            mapper_module: Module path for mapper
            mapper_class: Mapper class name
            connector_module: Module path for connector
            connector_class: Connector class name
            parser_module: Module path for parser (optional)
            parser_class: Parser class name (optional)

        Example:
            factory.register_provider(
                'custom_provider',
                'my_adapters.custom.mapper',
                'CustomMapper',
                'my_adapters.custom.connector',
                'CustomConnector'
            )
        """
        self._provider_mappers[provider] = (mapper_module, mapper_class)
        self._provider_connectors[provider] = (connector_module, connector_class)

        if parser_module and parser_class:
            self._provider_parsers[provider] = (parser_module, parser_class)

    # ========================================
    # UTILITY METHODS
    # ========================================

    def _load_class(self, module_path: str, class_name: str) -> Type:
        """
        Dynamically load a class from module

        Args:
            module_path: Python module path (e.g., 'shared.adapters.opta.opta_mapper')
            class_name: Class name (e.g., 'OptaMapper')

        Returns:
            Class type

        Raises:
            ImportError: If module or class cannot be loaded
        """
        try:
            # Import module
            import importlib
            module = importlib.import_module(module_path)

            # Get class from module
            if not hasattr(module, class_name):
                raise ImportError(
                    f"Module '{module_path}' does not have class '{class_name}'"
                )

            return getattr(module, class_name)

        except ImportError as e:
            raise ImportError(
                f"Failed to load {class_name} from {module_path}: {e}"
            )

    def clear_cache(self):
        """Clear all cached adapter instances"""
        self._mapper_cache.clear()
        self._connector_cache.clear()
        self._parser_cache.clear()


# ========================================
# SINGLETON INSTANCE
# ========================================

# Global factory instance (singleton pattern)
_factory_instance: Optional[ProviderFactory] = None


def get_factory(config_path: Optional[str] = None) -> ProviderFactory:
    """
    Get singleton factory instance

    Args:
        config_path: Path to providers.yaml (only used on first call)

    Returns:
        Global ProviderFactory instance

    Example:
        from shared.adapters.factory import get_factory

        factory = get_factory()
        mapper = factory.get_mapper('opta')
    """
    global _factory_instance

    if _factory_instance is None:
        _factory_instance = ProviderFactory(config_path)

    return _factory_instance
