"""
Base Adapter Interfaces

Abstract base classes that all provider adapters must implement.
"""

from .base_mapper import BaseMapper
from .base_connector import BaseConnector
from .base_parser import BaseParser

__all__ = ['BaseMapper', 'BaseConnector', 'BaseParser']
