#!/usr/bin/env python3
"""
Create optimized MongoDB indexes for event queries.

This script creates indexes to prevent COLLSCAN operations
and optimize the player event lookup pipeline.

Indexes created:
- player_id: Fast player event lookups (indexed)
- playerID: Alternative player field (indexed)
- matchID: Fast match lookups (indexed)
- Composite indexes for common query patterns
"""

import sys
sys.path.append('/app')

from pymongo import MongoClient, ASCENDING, DESCENDING
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_indexes():
    """Create optimized indexes for event queries."""
    mongo_uri = "mongodb://root:scoutpro123@localhost:27017/scoutpro?authSource=admin"
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Test the connection
        client.admin.command('ping')
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return False
    
    db = client['scoutpro']
    
    events_col = db['match_events']
    matches_col = db['matches']
    
    logger.info("Creating optimized MongoDB indexes for event queries...")
    
    try:
        # Index 1: Primary player_id index
        logger.info("Creating player_id index...")
        events_col.create_index([('player_id', ASCENDING)], name='idx_player_id', sparse=True)
        
        # Index 2: Alternative playerID field index
        logger.info("Creating playerID index...")
        events_col.create_index([('playerID', ASCENDING)], name='idx_playerID', sparse=True)
        
        # Index 3: matchID index for match lookups
        logger.info("Creating matchID index...")
        events_col.create_index([('matchID', ASCENDING)], name='idx_matchID', sparse=True)
        
        # Index 4: match_id index (alternative field)
        logger.info("Creating match_id index...")
        events_col.create_index([('match_id', ASCENDING)], name='idx_match_id', sparse=True)
        
        # Index 5: Composite for player + match lookups
        logger.info("Creating player_id + matchID composite index...")
        events_col.create_index(
            [('player_id', ASCENDING), ('matchID', ASCENDING)],
            name='idx_player_match',
            sparse=True
        )
        
        # Index 6: Composite for playerID + matchID lookups
        logger.info("Creating playerID + matchID composite index...")
        events_col.create_index(
            [('playerID', ASCENDING), ('matchID', ASCENDING)],
            name='idx_playerID_match',
            sparse=True
        )
        
        # Index 7: Event type queries
        logger.info("Creating type_name index...")
        events_col.create_index([('type_name', ASCENDING)], name='idx_type_name', sparse=True)
        
        # Index 8: Event type + Match composite
        logger.info("Creating type_name + matchID composite index...")
        events_col.create_index(
            [('type_name', ASCENDING), ('matchID', ASCENDING)],
            name='idx_type_match',
            sparse=True
        )
        
        # Index 9: Timestamp-based queries
        logger.info("Creating timestamp index...")
        events_col.create_index([('timestamp', DESCENDING)], name='idx_timestamp', sparse=True)
        
        # Index 10: Matches collection indexes
        logger.info("Creating team indexes on matches...")
        matches_col.create_index([('homeTeamID', ASCENDING)], name='idx_home_team', sparse=True)
        matches_col.create_index([('awayTeamID', ASCENDING)], name='idx_away_team', sparse=True)
        
        logger.info("Index creation completed successfully!")
        
        # Print index statistics
        logger.info("\nCreated indexes on match_events:")
        for idx in events_col.list_indexes():
            logger.info(f"  - {idx['name']}: {idx['key']}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        return False
    finally:
        client.close()


if __name__ == '__main__':
    success = create_indexes()
    sys.exit(0 if success else 1)
