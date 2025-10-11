"""
Ingestion module exports
"""
from .opta_client import OptaLiveClient
from .stream_processor import LiveDataProcessor

__all__ = ['OptaLiveClient', 'LiveDataProcessor']
