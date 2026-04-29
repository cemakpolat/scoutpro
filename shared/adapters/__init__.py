"""
Adapter Layer

Provider-specific adapters that transform external data into ScoutPro canonical format.
"""

from .factory import ProviderFactory

__all__ = ['ProviderFactory']
