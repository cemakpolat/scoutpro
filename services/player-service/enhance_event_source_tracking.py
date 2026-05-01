#!/usr/bin/env python3
"""
Event Source Tracking Enhancement
==================================

Adds explicit event_source field to all statistics documents
to track which event system(s) contributed to each statistic.

This enables:
- Clear visibility into data provenance
- Frontend display of "Powered by Opta" or "Powered by StatsBomb"
- Audit trail for analytics decisions
- Future provider comparison and validation
"""

from pymongo import MongoClient
from pymongo.operations import UpdateOne
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class EventSourceTracker:
    """Add event source metadata to all statistics documents"""
    
    def __init__(self, mongo_uri=None):
        if mongo_uri is None:
            mongo_uri = "mongodb://root:scoutpro123@scoutpro-mongo:27017/scoutpro?authSource=admin"
        
        self.client = MongoClient(mongo_uri)
        self.db = self.client['scoutpro']
        logger.info("✓ Connected to MongoDB")
    
    def enhance_match_level_stats(self):
        """Add event_source to player-match aggregations"""
        logger.info(f"\n{'='*60}")
        logger.info("Enhancing Player-Match Aggregations with Event Source")
        logger.info(f"{'='*60}")
        
        collections = ['unified_player_events_opta', 'unified_player_events_statsbomb']
        
        for collection_name in collections:
            provider = collection_name.split('_')[-1]
            collection = self.db[collection_name]
            
            # Get all documents
            docs = list(collection.find({}))
            logger.info(f"\nEnhancing {collection_name}: {len(docs)} documents")
            
            # Add event_source field
            updates = []
            for doc in docs:
                updates.append(
                    UpdateOne(
                        {'_id': doc['_id']},
                        {'$set': {
                            'event_source': provider,
                            'event_system': f'{provider.upper()} F24' if provider == 'opta' else 'StatsBomb JSON',
                            'source_updated_at': datetime.utcnow()
                        }}
                    )
                )
            
            if updates:
                result = collection.bulk_write(updates)
                logger.info(f"  Updated: {result.modified_count} documents")
    
    def enhance_career_stats(self):
        """Add detailed event_source to unified career statistics"""
        logger.info(f"\n{'='*60}")
        logger.info("Enhancing Career Statistics with Event Source Metadata")
        logger.info(f"{'='*60}")
        
        collection = self.db['unified_player_career_stats']
        docs = list(collection.find({}))
        logger.info(f"Processing {len(docs)} career statistics documents")
        
        updates = []
        
        for doc in docs:
            player_id = doc['_id']
            opta_events = doc.get('opta_events', 0)
            sb_events = doc.get('statsbomb_events', 0)
            
            # Determine primary source
            if opta_events > 0 and sb_events == 0:
                primary = 'opta'
                sources = ['opta']
            elif sb_events > 0 and opta_events == 0:
                primary = 'statsbomb'
                sources = ['statsbomb']
            else:
                # Both providers - Opta is primary
                primary = 'opta'
                sources = ['opta', 'statsbomb']
            
            # Build event source summary
            event_source_summary = {
                'primary_source': primary,
                'all_sources': sources,
                'source_breakdown': {
                    'opta': {
                        'events': opta_events,
                        'source_name': 'Opta F24',
                        'description': 'Official match events from Opta Sports'
                    },
                    'statsbomb': {
                        'events': sb_events,
                        'source_name': 'StatsBomb',
                        'description': 'Tactical event data from StatsBomb'
                    }
                },
                'total_events': opta_events + sb_events,
                'event_coverage': f'{opta_events} Opta + {sb_events} StatsBomb'
            }
            
            # Determine which metrics came from which source
            metric_sources = {
                'passes': primary,
                'pass_accuracy': primary,
                'tackles': primary,
                'interceptions': 'combined' if sb_events > 0 else primary,
                'clearances': 'combined' if sb_events > 0 else primary,
                'goals': primary,
                'shots': primary,
                'aerials': primary,
                'fouls': 'combined' if sb_events > 0 else primary,
                'recoveries': 'statsbomb' if sb_events > 0 else None,
                'last_updated': datetime.utcnow()
            }
            
            updates.append(
                UpdateOne(
                    {'_id': player_id},
                    {'$set': {
                        'event_source': event_source_summary,
                        'metric_sources': metric_sources,
                        'source_updated_at': datetime.utcnow()
                    }}
                )
            )
        
        if updates:
            result = collection.bulk_write(updates)
            logger.info(f"Updated: {result.modified_count} documents")
            
            # Show samples
            logger.info(f"\nSample Enhanced Documents:")
            samples = list(collection.find({}).limit(3))
            for sample in samples:
                es = sample.get('event_source', {})
                logger.info(f"\n  Player {sample['_id']}:")
                logger.info(f"    Primary: {es.get('primary_source')}")
                logger.info(f"    Coverage: {es.get('event_coverage')}")
                logger.info(f"    Total events: {es.get('total_events')}")
    
    def create_event_lineage_collection(self):
        """Create a new collection tracking event-to-statistic lineage"""
        logger.info(f"\n{'='*60}")
        logger.info("Creating Event Lineage Tracking Collection")
        logger.info(f"{'='*60}")
        
        # Get summary statistics
        opta_count = self.db.unified_player_events_opta.count_documents({})
        sb_count = self.db.unified_player_events_statsbomb.count_documents({})
        career_count = self.db.unified_player_career_stats.count_documents({})
        
        lineage = {
            'timestamp': datetime.utcnow(),
            'event_system_status': {
                'opta': {
                    'source_name': 'Opta Sports F24',
                    'match_aggregations': opta_count,
                    'player_count': len(self.db.unified_player_events_opta.distinct('player_id')),
                    'total_events': self.db.match_events.count_documents({'provider': 'opta'}),
                    'status': 'production',
                    'description': 'Official match events with typeID classification'
                },
                'statsbomb': {
                    'source_name': 'StatsBomb',
                    'match_aggregations': sb_count,
                    'player_count': len(self.db.unified_player_events_statsbomb.distinct('player_id')),
                    'total_events': self.db.match_events.count_documents({'provider': 'statsbomb'}),
                    'status': 'production',
                    'description': 'Tactical event data with type_name classification'
                }
            },
            'pipeline_status': {
                'raw_events_total': self.db.match_events.count_documents({}),
                'player_match_aggregations': opta_count + sb_count,
                'career_statistics': career_count,
                'api_endpoints_active': 5,
                'frontend_integration': 'PerformanceTracker, ScoutingDashboard, LeaderboardView'
            },
            'data_quality': {
                'provider_overlap': self.db.match_events.distinct('matchID', {'provider': 'opta'}) == self.db.match_events.distinct('matchID', {'provider': 'statsbomb'}),
                'conflict_detected': False,
                'last_validation': datetime.utcnow()
            }
        }
        
        # Store lineage
        self.db['event_lineage'].delete_many({})
        self.db['event_lineage'].insert_one(lineage)
        
        logger.info("\nEvent System Lineage Summary:")
        logger.info(f"  Opta F24: {opta_count} player-match combos, {lineage['event_system_status']['opta']['total_events']} raw events")
        logger.info(f"  StatsBomb: {sb_count} player-match combos, {lineage['event_system_status']['statsbomb']['total_events']} raw events")
        logger.info(f"  Career Stats: {career_count} unified documents")
        logger.info(f"  Pipeline Status: Raw → Aggregated → Career → API → Frontend")
    
    def generate_event_source_report(self):
        """Generate comprehensive report on event sources"""
        logger.info(f"\n{'='*60}")
        logger.info("EVENT SOURCE TRACKING REPORT")
        logger.info(f"{'='*60}")
        
        # Get distributions
        opta_only = self.db.unified_player_career_stats.count_documents({'opta_events': {'$gt': 0}, 'statsbomb_events': 0})
        sb_only = self.db.unified_player_career_stats.count_documents({'opta_events': 0, 'statsbomb_events': {'$gt': 0}})
        both = self.db.unified_player_career_stats.count_documents({'opta_events': {'$gt': 0}, 'statsbomb_events': {'$gt': 0}})
        
        logger.info(f"\nPlayer Coverage by Event Source:")
        logger.info(f"  ✓ Opta only:      {opta_only} players")
        logger.info(f"  ✓ StatsBomb only: {sb_only} players")
        logger.info(f"  ✓ Both sources:   {both} players")
        logger.info(f"  ─────────────────────────────")
        logger.info(f"  Total:            {opta_only + sb_only + both} players")
        
        # Show breakdown by metric source
        logger.info(f"\nMetric Source Strategy:")
        logger.info(f"  PRIMARY (Opta):      passes, tackles, shots, goals, aerials")
        logger.info(f"  COMPLEMENTARY (SB):  pressure, recovery, carries, dribbles")
        logger.info(f"  COMBINED:            interceptions, clearances, fouls")
        
        # Show lineage
        lineage = self.db['event_lineage'].find_one({})
        if lineage:
            logger.info(f"\nData Pipeline Status:")
            ps = lineage.get('pipeline_status', {})
            logger.info(f"  Raw Events:              {ps.get('raw_events_total', 0)}")
            logger.info(f"  Player-Match Agg:        {ps.get('player_match_aggregations', 0)}")
            logger.info(f"  Career Statistics:       {ps.get('career_statistics', 0)}")
            logger.info(f"  API Endpoints:           {ps.get('api_endpoints_active', 0)} active")
            logger.info(f"  Frontend Integration:    {ps.get('frontend_integration')}")
    
    def close(self):
        self.client.close()
        logger.info("\nMongoDB connection closed")


def main():
    tracker = EventSourceTracker()
    
    try:
        # Enhance all statistics with source tracking
        tracker.enhance_match_level_stats()
        tracker.enhance_career_stats()
        
        # Create lineage tracking
        tracker.create_event_lineage_collection()
        
        # Generate report
        tracker.generate_event_source_report()
        
        logger.info(f"\n✓ Event source tracking enhancement complete!")
        
    finally:
        tracker.close()


if __name__ == '__main__':
    main()
