#!/usr/bin/env python3
"""
Create MongoDB indexes for optimized event queries.

Indexes created:
- player_id: Fast player event lookups
- team_id (via matches): Fast team event aggregation
- type_name + matchID: Fast event type filtering within matches
- timestamp: Time-based event queries
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
    client = MongoClient(mongo_uri)
    db = client['scoutpro']
    
    events_col = db['match_events']
    matches_col = db['matches']
    
    logger.info("Creating MongoDB indexes for event queries...")
    
    # Index 1: Player event queries
    logger.info("Creating player_id index...")
    events_col.create_index([('player_id', ASCENDING)], name='idx_player_id')
    
    # Index 2: Player + Match composite
    logger.info("Creating player_id + matchID composite index...")
    events_col.create_index(
        [('player_id', ASCENDING), ('matchID', ASCENDING)],
        name='idx_player_match'
    )
    
    # Index 3: Event type queries
    logger.info("Creating type_name index...")
    events_col.create_index([('type_name', ASCENDING)], name='idx_type_name')
    
    # Index 4: Event type + Match
    logger.info("Creating type_name + matchID composite index...")
    events_col.create_index(
        [('type_name', ASCENDING), ('matchID', ASCENDING)],
        name='idx_type_match'
    )
    
    # Index 5: Timestamp-based queries
    logger.info("Creating timestamp index...")
    events_col.create_index([('timestamp', DESCENDING)], name='idx_timestamp')
    
    # Index 6: Match-based lookups
    logger.info("Creating matchID index...")
    events_col.create_index([('matchID', ASCENDING)], name='idx_match_id')
    
    # Index 7: Team lookups for matches (for team event aggregation)
    logger.info("Creating team indexes on matches...")
    matches_col.create_index([('homeTeamID', ASCENDING)], name='idx_home_team')
    matches_col.create_index([('awayTeamID', ASCENDING)], name='idx_away_team')
    
    # Index 8: Composite for quick team match lookup
    logger.info("Creating team match composite indexes...")
    matches_col.create_index(
        [('homeTeamID', ASCENDING), ('date', DESCENDING)],
        name='idx_home_team_date'
    )
    matches_col.create_index(
        [('awayTeamID', ASCENDING), ('date', DESCENDING)],
        name='idx_away_team_date'
    )
    
    # Index 9: Match status for live match queries
    logger.info("Creating status index...")
    matches_col.create_index([('status', ASCENDING)], name='idx_match_status')
    
    logger.info("✅ All indexes created successfully!")
    
    # Print index statistics
    logger.info("\n📊 Match Events Indexes:")
    for idx in events_col.list_indexes():
        logger.info(f"  - {idx['name']}: {idx['key']}")
    
    logger.info("\n📊 Matches Indexes:")
    for idx in matches_col.list_indexes():
        logger.info(f"  - {idx['name']}: {idx['key']}")
    
    client.close()
    return True


if __name__ == '__main__':
    try:
        create_indexes()
        print("\n✅ Index creation completed successfully")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error creating indexes: {e}")
        sys.exit(1)
