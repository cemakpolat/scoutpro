#!/usr/bin/env python3
"""
Unified Event Evaluation System
================================
Processes both Opta (F24) and StatsBomb events through a unified pipeline.
Both providers' events are normalized into the same event structure in MongoDB,
and this system evaluates them consistently.

Event Type Mappings:
- Opta: Uses numeric EventIDs (1=Pass, 7=Tackle, 44=Aerial, etc.)
- StatsBomb: Uses string event type_name (pass, duel, tackle, aerial lost, etc.)

Both are evaluated to produce:
- Pass accuracy, completion rates
- Shot efficiency, xG, goal probability
- Aerial duel success rates
- Tackle/interception effectiveness
- Ball control metrics
- Distance covered, speed metrics

Author: Scout Pro Architecture
"""

import json
import sys
from datetime import datetime
from pymongo import MongoClient
from collections import defaultdict
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedEventEvaluator:
    """
    Unified event evaluation for both Opta and StatsBomb events.
    Maps provider-specific event types to common metrics.
    """
    
    # StatsBomb -> Common metric mapping
    STATSBOMB_EVENT_MAP = {
        'pass': 'pass',
        'shot': 'shot',
        'tackle': 'tackle',
        'interception': 'interception',
        'clearance': 'clearance',
        'duel': 'duel',
        'aerial lost': 'aerial_loss',
        'aerial': 'aerial_win',
        'block': 'block',
        'ball recovery': 'recovery',
        'dispossessed': 'dispossessed',
        'miscontrol': 'miscontrol',
        'pressure': 'pressure',
        'foul committed': 'foul',
        'goal kick': 'goal_kick',
        'throw-in': 'throw_in',
        'dribble': 'dribble',
        'free kick': 'free_kick',
        'carries': 'carry',
        'ball receipt*': 'ball_receipt'
    }
    
    # Opta EventID -> Common metric mapping
    OPTA_EVENT_MAP = {
        1: 'pass',
        2: 'offside_pass',
        3: 'take_on',
        4: 'foul',
        5: 'out',
        6: 'corner',
        7: 'tackle',
        8: 'interception',
        9: 'turnover',
        10: 'save',
        11: 'claim',
        12: 'clearance',
        13: 'miss',
        14: 'post',
        15: 'attempt_saved',
        16: 'goal',
        17: 'card',
        44: 'aerial',
        45: 'challenge',
        49: 'recovery',
        50: 'dispossessed',
        51: 'error',
        52: 'keeper_pickup',
        67: 'duel'
    }
    
    def __init__(self, mongo_uri=None):
        if mongo_uri is None:
            mongo_uri = "mongodb://root:scoutpro123@scoutpro-mongo:27017/scoutpro?authSource=admin"
        
        try:
            self.client = MongoClient(mongo_uri)
            self.db = self.client['scoutpro']
            logger.info("✓ Connected to MongoDB")
        except Exception as e:
            logger.error(f"✗ MongoDB connection failed: {e}")
            raise
    
    def evaluate_pass_event(self, event):
        """Evaluate pass event (Opta or StatsBomb)"""
        # is_successful may be at top level OR in raw_event
        is_successful = event.get('is_successful') or (event.get('raw_event', {}).get('is_successful') if isinstance(event.get('raw_event'), dict) else False)
        
        return {
            'passes_total': 1,
            'passes_successful': 1 if is_successful else 0,
            'passes_unsuccessful': 0 if is_successful else 1,
            'pass_distance': self._calculate_distance(event.get('location'), event.get('end_location')),
            'is_forward': self._is_forward_pass(event),
            'is_backward': not self._is_forward_pass(event)
        }
    
    def evaluate_shot_event(self, event):
        """Evaluate shot event"""
        is_successful = event.get('is_successful') or (event.get('raw_event', {}).get('is_successful') if isinstance(event.get('raw_event'), dict) else False)
        is_goal = event.get('is_goal') or (event.get('raw_event', {}).get('is_goal') if isinstance(event.get('raw_event'), dict) else False)
        
        return {
            'shots_total': 1,
            'shots_on_target': 1 if is_successful else 0,
            'goals': 1 if is_goal else 0,
            'shot_location': event.get('location')
        }
    
    def evaluate_tackle_event(self, event):
        """Evaluate tackle/challenge event"""
        is_successful = event.get('is_successful') or (event.get('raw_event', {}).get('is_successful') if isinstance(event.get('raw_event'), dict) else False)
        
        return {
            'tackles_total': 1,
            'tackles_successful': 1 if is_successful else 0,
            'tackles_unsuccessful': 0 if is_successful else 1
        }
    
    def evaluate_aerial_event(self, event):
        """Evaluate aerial duel event"""
        # StatsBomb: 'aerial lost' = unsuccessful, 'aerial' = successful
        # Opta: typeID 44, outcome 0=lost, 1=won
        event_type = event.get('type_name', '').lower()
        provider = event.get('provider', '')
        
        # Check both top-level and raw_event
        is_successful = event.get('is_successful') or (event.get('raw_event', {}).get('is_successful') if isinstance(event.get('raw_event'), dict) else False)
        
        if provider == 'statsbomb':
            is_successful = event_type not in ['aerial lost', 'aerial lost*']
        
        return {
            'aerial_duels_total': 1,
            'aerial_duels_won': 1 if is_successful else 0,
            'aerial_duels_lost': 0 if is_successful else 1,
            'aerial_location': event.get('location')
        }
    
    def evaluate_duel_event(self, event):
        """Evaluate duel event (StatsBomb)"""
        is_successful = event.get('is_successful') or (event.get('raw_event', {}).get('is_successful') if isinstance(event.get('raw_event'), dict) else False)
        
        return {
            'duels_total': 1,
            'duels_won': 1 if is_successful else 0,
            'duels_lost': 0 if is_successful else 1
        }
    
    def evaluate_interception_event(self, event):
        """Evaluate interception event"""
        return {
            'interceptions': 1,
            'interception_location': event.get('location')
        }
    
    def evaluate_clearance_event(self, event):
        """Evaluate clearance event"""
        return {
            'clearances': 1
        }
    
    def evaluate_recovery_event(self, event):
        """Evaluate ball recovery event"""
        return {
            'ball_recoveries': 1
        }
    
    def evaluate_foul_event(self, event):
        """Evaluate foul event"""
        return {
            'fouls_committed': 1
        }
    
    def _calculate_distance(self, loc1, loc2):
        """Calculate distance between two locations (in meters, normalized from 0-100)"""
        if not loc1 or not loc2:
            return 0
        x1, y1 = loc1.get('x', 0), loc1.get('y', 0)
        x2, y2 = loc2.get('x', 0), loc2.get('y', 0)
        distance = ((x2-x1)**2 + (y2-y1)**2) ** 0.5
        return round(distance, 2)
    
    def _get_field(self, event, field_name):
        """Get field from event, checking both top-level and raw_event"""
        value = event.get(field_name)
        if value is None and isinstance(event.get('raw_event'), dict):
            value = event['raw_event'].get(field_name)
        return value
    
    def _is_forward_pass(self, event):
        """Determine if pass is forward (towards opponent goal)"""
        if not event.get('end_location'):
            return False
        
        loc = event.get('location', {})
        end = event.get('end_location', {})
        
        x1 = loc.get('x', 0)
        x2 = end.get('x', 0)
        
        # Field is 0-100 in x direction
        # Forward means moving towards opponent (higher x)
        return x2 > x1
    
    def evaluate_event(self, event):
        """Route event to appropriate evaluator based on type"""
        event_type = event.get('type_name', '').lower()
        provider = event.get('provider', '')
        
        metrics = {}
        
        # Route based on event type
        if event_type == 'pass':
            metrics = self.evaluate_pass_event(event)
        elif event_type == 'shot':
            metrics = self.evaluate_shot_event(event)
        elif event_type in ['tackle', 'challenge']:
            metrics = self.evaluate_tackle_event(event)
        elif event_type in ['duel', 'aerial', 'aerial lost', 'aerial lost*', 'aerial won']:
            metrics = self.evaluate_aerial_event(event)
        elif event_type == 'interception':
            metrics = self.evaluate_interception_event(event)
        elif event_type == 'clearance':
            metrics = self.evaluate_clearance_event(event)
        elif event_type in ['ball recovery', 'recovery']:
            metrics = self.evaluate_recovery_event(event)
        elif event_type in ['foul committed', 'foul']:
            metrics = self.evaluate_foul_event(event)
        
        return metrics
    
    def aggregate_player_events(self, player_id, match_id, team_id, provider):
        """Aggregate all events for a player in a match"""
        pipeline = [
            {
                '$match': {
                    'player_id': player_id,
                    'matchID': match_id,
                    'team_id': team_id,
                    'provider': provider
                }
            },
            {'$sort': {'minute': 1, 'second': 1}}
        ]
        
        events = list(self.db.match_events.aggregate(pipeline))
        
        aggregated = {
            'player_id': player_id,
            'match_id': match_id,
            'team_id': team_id,
            'provider': provider,
            'event_count': len(events),
            'timestamp': datetime.utcnow()
        }
        
        # Initialize all metric counters
        metric_totals = defaultdict(int)
        metric_locations = defaultdict(list)
        
        # Evaluate each event
        for event in events:
            metrics = self.evaluate_event(event)
            
            # Aggregate numeric metrics
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    metric_totals[key] += value
                elif isinstance(value, dict):  # location
                    metric_locations[key].append(value)
        
        # Merge metrics into aggregated stats
        aggregated['metrics'] = dict(metric_totals)
        if metric_locations:
            aggregated['locations'] = dict(metric_locations)
        
        # Compute derived metrics
        if metric_totals.get('passes_total', 0) > 0:
            aggregated['pass_accuracy'] = round(
                (metric_totals['passes_successful'] / metric_totals['passes_total']) * 100,
                2
            )
        
        if metric_totals.get('aerial_duels_total', 0) > 0:
            aggregated['aerial_success_rate'] = round(
                (metric_totals['aerial_duels_won'] / metric_totals['aerial_duels_total']) * 100,
                2
            )
        
        if metric_totals.get('duels_total', 0) > 0:
            aggregated['duel_success_rate'] = round(
                (metric_totals['duels_won'] / metric_totals['duels_total']) * 100,
                2
            )
        
        return aggregated
    
    def process_all_events(self, provider='both'):
        """Process all events for both/single provider"""
        providers = ['opta', 'statsbomb'] if provider == 'both' else [provider]
        
        for prov in providers:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing {prov.upper()} Events")
            logger.info(f"{'='*60}")
            
            # Find all unique player-match combinations for this provider
            pipeline = [
                {'$match': {'provider': prov}},
                {
                    '$group': {
                        '_id': {
                            'match_id': '$matchID',
                            'player_id': '$player_id',
                            'team_id': '$team_id'
                        },
                        'event_count': {'$sum': 1}
                    }
                },
                {'$match': {'event_count': {'$gte': 1}}}
            ]
            
            combos = list(self.db.match_events.aggregate(pipeline))
            logger.info(f"Found {len(combos)} player-match combinations ({prov})")
            
            successful = 0
            failed = 0
            stats_docs = []
            
            for idx, combo in enumerate(combos):
                match_id = combo['_id']['match_id']
                player_id = combo['_id']['player_id']
                team_id = combo['_id']['team_id']
                
                try:
                    stats = self.aggregate_player_events(player_id, match_id, team_id, prov)
                    if stats:
                        stats_docs.append(stats)
                        successful += 1
                    
                    if (idx + 1) % 100 == 0:
                        logger.info(f"  Progress: {idx + 1}/{len(combos)}")
                except Exception as e:
                    logger.warning(f"  Failed for {prov} match {match_id}, player {player_id}: {e}")
                    failed += 1
            
            # Store in collection
            collection_name = f'unified_player_events_{prov}'
            if stats_docs:
                try:
                    self.db[collection_name].delete_many({})
                    result = self.db[collection_name].insert_many(stats_docs)
                    logger.info(f"✓ Stored {len(result.inserted_ids)} {prov} player event aggregations")
                except Exception as e:
                    logger.error(f"✗ Insert failed: {e}")
            
            logger.info(f"Summary ({prov}): {successful} successful, {failed} failed")
        
        # Aggregate across both providers
        self.aggregate_provider_unified()
    
    def aggregate_provider_unified(self):
        """Create unified career statistics from both providers"""
        logger.info(f"\n{'='*60}")
        logger.info("Creating Unified Career Statistics (Opta + StatsBomb)")
        logger.info(f"{'='*60}")
        
        # Union statistics from both providers
        pipeline = [
            {
                '$unionWith': {
                    'coll': 'unified_player_events_statsbomb'
                }
            },
            {
                '$group': {
                    '_id': '$player_id',
                    'opta_events': {
                        '$sum': {'$cond': [{'$eq': ['$provider', 'opta']}, '$event_count', 0]}
                    },
                    'statsbomb_events': {
                        '$sum': {'$cond': [{'$eq': ['$provider', 'statsbomb']}, '$event_count', 0]}
                    },
                    'total_passes': {'$sum': {'$getField': {'field': 'passes_total', 'input': '$metrics'}}},
                    'successful_passes': {'$sum': {'$getField': {'field': 'passes_successful', 'input': '$metrics'}}},
                    'total_shots': {'$sum': {'$getField': {'field': 'shots_total', 'input': '$metrics'}}},
                    'goals': {'$sum': {'$getField': {'field': 'goals', 'input': '$metrics'}}},
                    'tackles': {'$sum': {'$getField': {'field': 'tackles_total', 'input': '$metrics'}}},
                    'interceptions': {'$sum': {'$getField': {'field': 'interceptions', 'input': '$metrics'}}},
                    'clearances': {'$sum': {'$getField': {'field': 'clearances', 'input': '$metrics'}}},
                    'recoveries': {'$sum': {'$getField': {'field': 'ball_recoveries', 'input': '$metrics'}}},
                    'fouls': {'$sum': {'$getField': {'field': 'fouls_committed', 'input': '$metrics'}}},
                    'last_updated': {'$max': '$timestamp'}
                }
            },
            {
                '$addFields': {
                    'pass_accuracy': {
                        '$cond': [
                            {'$gt': ['$total_passes', 0]},
                            {'$round': [{'$multiply': [{'$divide': ['$successful_passes', '$total_passes']}, 100]}, 2]},
                            0
                        ]
                    }
                }
            }
        ]
        
        try:
            results = list(self.db.unified_player_events_opta.aggregate(pipeline))
            
            if results:
                self.db.unified_player_career_stats.delete_many({})
                self.db.unified_player_career_stats.insert_many(results)
                logger.info(f"✓ Created {len(results)} unified career statistics")
                
                # Show sample
                sample = results[0] if results else None
                if sample:
                    logger.info(f"\nSample unified stats:")
                    logger.info(f"  Player {sample['_id']}: {sample.get('opta_events', 0)} Opta + {sample.get('statsbomb_events', 0)} SB events")
                    logger.info(f"  Passes: {sample.get('total_passes', 0)} total, {sample.get('pass_accuracy', 0)}% accurate")
                    logger.info(f"  Shots: {sample.get('total_shots', 0)}, Goals: {sample.get('goals', 0)}")
        except Exception as e:
            logger.warning(f"Unified aggregation failed: {e}")
    
    def close(self):
        self.client.close()
        logger.info("MongoDB connection closed")


def main():
    mongo_uri = "mongodb://root:scoutpro123@scoutpro-mongo:27017/scoutpro?authSource=admin"
    
    evaluator = UnifiedEventEvaluator(mongo_uri)
    
    try:
        logger.info("\n" + "="*60)
        logger.info("UNIFIED EVENT EVALUATION SYSTEM")
        logger.info("Processing Opta + StatsBomb Events")
        logger.info("="*60)
        
        # Process both providers
        evaluator.process_all_events('both')
        
        logger.info(f"\n✓ Unified Event Evaluation completed!")
        
    except Exception as e:
        logger.error(f"✗ Pipeline failed: {e}")
        sys.exit(1)
    finally:
        evaluator.close()


if __name__ == '__main__':
    main()
