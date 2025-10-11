"""
Database connectors
"""
from .connector import Connector

# Create global connector instance
main_conn = Connector(name="scoutpro", port=27017, host="mongo", alias="default")

__all__ = ['Connector', 'main_conn']
