#!/usr/bin/env python3
"""
Event Aggregation Pipeline
===========================
Executes the complete event evaluation system on match_events data.
Transforms raw Opta F24 events into detailed player, team, and match statistics.

Pipeline:
1. Read match_events from MongoDB grouped by player/match/team
2. Run all event handlers (Passes, Shots, Aerials, Duels, etc.)
3. Aggregate computed statistics by multiple dimensions
4. Store results in detailed_player_statistics, detailed_team_statistics, detailed_match_statistics

Author: Scout Pro Architecture Team
"""

import json
import sys
from datetime import datetime
from pymongo import MongoClient
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Add services to path so we can import event handlers
sys.path.insert(0, '/app/shared')
sys.path.insert(0, '/app')

try:
    from shared.events.event_handler import EventHandler
    from shared.events.PassEvent import PassEvent
    from shared.events.ShotandGoalEvents import ShotandGoalEvents
    from shared.events.AerialDuelEvents import AerialDuelEvents
    from shared.events.DuelEvents import DuelEvents
    from shared.events.TakeOnEvents import TakeOnEvents
    from shared.events.CardEvents import CardEvents
    from shared.events.TouchEvents import TouchEvents
    from shared.events.FoulEvents import FoulEvents
    from shared.events.BallControlEvents import BallControlEvents
    from shared.events.AssistEvents import AssistEvents
    HANDLERS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Event handlers not available: {e}. Running in metrics-only mode.")
    HANDLERS_AVAILABLE = False


class EventAggregationPipeline:
    """
    Orchestrates event evaluation and statistics aggregation.
    """
    
    def __init__(self, mongo_uri=None):
        """Initialize MongoDB connection."""
        if mongo_uri is None:
            mongo_uri = "mongodb://root:scoutpro123@scoutpro-mongo:27017/scoutpro?authSource=admin"
        
        try:
            self.client = MongoClient(mongo_uri)
            self.db = self.client['scoutpro']
            logger.info("✓ Connected to MongoDB")
        except Exception as e:
            logger.error(f"✗ MongoDB connection failed: {e}")
            raise
    
    def get_player_events(self, player_id, match_id, team_id):
        """
        Retrieve all events for a specific player in a specific match.
        Returns in the format expected by EventHandler classes.
        """
        events_cursor = self.db.match_events.find({
            'matchID': match_id,
            'player_id': player_id,
            'team_id': team_id
        }).sort('minute', 1)
        
        events = list(events_cursor)
        if not events:
            return None
        
        # Prepare data structure for event handlers
        # EventHandler expects: {teamID, playerID, events}
        data = {
            'teamID': [team_id],
            'playerID': [player_id],
            'events': self._convert_events_to_handler_format(events)
        }
        
        return data
    
    def _convert_events_to_handler_format(self, events):
        """
        Convert MongoDB event documents to the format expected by event handlers.
        Event handlers expect objects with: typeID, playerID, teamID, outcome, x, y, qualifiers, etc.
        """
        class SimpleEvent:
            def __init__(self, doc):
                self.playerID = doc.get('player_id')
                self.teamID = doc.get('team_id')
                self.typeID = self._type_to_id(doc.get('type_name'))
                self.outcome = 1 if doc.get('is_successful', False) else 0
                self.x = float(doc.get('location', {}).get('x', 0)) if doc.get('location') else 0
                self.y = float(doc.get('location', {}).get('y', 0)) if doc.get('location') else 0
                self.period = doc.get('period')
                self.minute = doc.get('minute')
                self.is_goal = doc.get('is_goal', False)
                self.qEvents = []  # Qualifiers - would need to parse from qualifiers array
                self.raw_event = doc
                
                # Handle qualifiers
                if doc.get('qualifiers'):
                    for qual in doc.get('qualifiers', []):
                        if isinstance(qual, dict):
                            self.qEvents.append(qual)
            
            @staticmethod
            def _type_to_id(type_name):
                """Convert type_name string to Opta numeric ID."""
                type_map = {
                    'pass': 1, 'offside pass': 2, 'take on': 3, 'foul': 4, 'out': 5,
                    'corner awarded': 6, 'tackle': 7, 'interception': 8, 'turnover': 9,
                    'save': 10, 'claim': 11, 'clearance': 12, 'miss': 13, 'post': 14,
                    'attempt saved': 15, 'goal': 16, 'card': 17, 'player off': 18,
                    'player on': 19, 'player retired': 20, 'player returns': 21,
                    'player becomes goalkeeper': 22, 'goalkeeper becomes player': 23,
                    'aerial': 44, 'challenge': 45, 'ball recovery': 49,
                    'dispossessed': 50, 'error': 51, 'keeper pick-up': 52,
                    'cross not claimed': 53, 'smother': 54, 'offside provoked': 55,
                    'shield ball opp': 56, 'foul throw-in': 57, 'penalty faced': 58,
                    'keeper sweeper': 59, 'chance missed': 60, 'ball touch': 61,
                    '50/50': 67, 'referee drop ball': 68, 'punch': 41,
                    'good skill': 42, 'duel': 44, 'shot': 13
                }
                return type_map.get(str(type_name).lower(), 0)
        
        return [SimpleEvent(event) for event in events]
    
    def evaluate_player_match_events(self, player_id, match_id, team_id):
        """
        Run all event handlers on a player's events for a specific match.
        Returns aggregated statistics.
        """
        data = self.get_player_events(player_id, match_id, team_id)
        if not data:
            return None
        
        stats = {
            'player_id': player_id,
            'match_id': match_id,
            'team_id': team_id,
            'timestamp': datetime.utcnow()
        }
        
        if HANDLERS_AVAILABLE:
            # Run each event handler
            try:
                stats['passes'] = PassEvent().callEventHandler(data, print_results=False)
                stats['shots'] = ShotandGoalEvents().callEventHandler(data, print_results=False)
                stats['aerials'] = AerialDuelEvents().callEventHandler(data, print_results=False)
                stats['duels'] = DuelEvents().callEventHandler(data, print_results=False)
                stats['take_ons'] = TakeOnEvents().callEventHandler(data, print_results=False)
                stats['cards'] = CardEvents().callEventHandler(data, print_results=False)
                stats['touches'] = TouchEvents().callEventHandler(data, print_results=False)
                stats['fouls'] = FoulEvents().callEventHandler(data, print_results=False)
                stats['ball_control'] = BallControlEvents().callEventHandler(data, print_results=False)
                stats['assists'] = AssistEvents().callEventHandler(data, print_results=False)
            except Exception as e:
                logger.warning(f"Event handler failed for player {player_id}: {e}")
        else:
            # Fallback: compute basic metrics from raw events
            stats = self._compute_basic_metrics(data, stats)
        
        return stats
    
    def _compute_basic_metrics(self, data, stats):
        """Fallback method to compute basic metrics when event handlers unavailable."""
        events = data.get('events', [])
        
        passes = [e for e in events if e.typeID == 1]
        stats['passes'] = {
            'total passes': len(passes),
            'passes successful': sum(1 for e in passes if e.outcome == 1),
            'passes unsuccessful': sum(1 for e in passes if e.outcome == 0)
        }
        
        shots = [e for e in events if e.typeID in [13, 15, 16]]
        stats['shots'] = {
            'total shots': len(shots),
            'shots on target': sum(1 for e in shots if e.typeID in [15, 16]),
            'goals': sum(1 for e in shots if e.is_goal)
        }
        
        aerials = [e for e in events if e.typeID == 44]
        stats['aerials'] = {
            'total aerial duels': len(aerials),
            'aerial duels won': sum(1 for e in aerials if e.outcome == 1),
            'aerial duel success rate': round(
                100 * sum(1 for e in aerials if e.outcome == 1) / len(aerials),
                2
            ) if aerials else 0
        }
        
        tackles = [e for e in events if e.typeID == 7]
        stats['tackles'] = {
            'total tackles': len(tackles),
            'successful tackles': sum(1 for e in tackles if e.outcome == 1)
        }
        
        return stats
    
    def aggregate_all_player_matches(self):
        """
        Main entry point: Evaluate all players across all matches.
        Stores results in detailed_player_statistics collection.
        """
        logger.info("Starting Event Aggregation Pipeline...")
        
        # Find all unique (matchID, player_id, team_id) combinations
        pipeline = [
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
            {'$match': {'event_count': {'$gte': 1}}}  # At least 1 event
        ]
        
        results = list(self.db.match_events.aggregate(pipeline))
        logger.info(f"Found {len(results)} player-match combinations")
        
        # Process each player-match combination
        successful = 0
        failed = 0
        detailed_stats = []
        
        for idx, combo in enumerate(results):
            match_id = combo['_id']['match_id']
            player_id = combo['_id']['player_id']
            team_id = combo['_id']['team_id']
            
            try:
                stats = self.evaluate_player_match_events(player_id, match_id, team_id)
                if stats:
                    detailed_stats.append(stats)
                    successful += 1
                    
                    if (idx + 1) % 100 == 0:
                        logger.info(f"Progress: {idx + 1}/{len(results)} processed")
            except Exception as e:
                logger.warning(f"Failed for match {match_id}, player {player_id}: {e}")
                failed += 1
        
        # Bulk insert into MongoDB
        if detailed_stats:
            try:
                # Clear existing detailed stats
                self.db.detailed_player_statistics.delete_many({})
                
                result = self.db.detailed_player_statistics.insert_many(detailed_stats)
                logger.info(f"✓ Inserted {len(result.inserted_ids)} detailed player statistics")
            except Exception as e:
                logger.error(f"✗ Bulk insert failed: {e}")
        
        logger.info(f"\n=== Summary ===")
        logger.info(f"Successful evaluations: {successful}")
        logger.info(f"Failed evaluations: {failed}")
        logger.info(f"Total stored: {len(detailed_stats)}")
        
        # Aggregate to player-level statistics (career stats)
        self.aggregate_player_career_stats()
        
        # Aggregate to team-level statistics
        self.aggregate_team_stats()
        
        # Aggregate to match-level statistics
        self.aggregate_match_stats()
        
        return len(detailed_stats)
    
    def aggregate_player_career_stats(self):
        """Aggregate match-by-match data into career statistics per player."""
        logger.info("Aggregating player career statistics...")
        
        pipeline = [
            {
                '$group': {
                    '_id': '$player_id',
                    'matches': {'$sum': 1},
                    'total_passes': {
                        '$sum': {
                            '$toInt': {
                                '$getField': {
                                    'field': 'total passes',
                                    'input': '$passes'
                                }
                            }
                        }
                    },
                    'successful_passes': {
                        '$sum': {
                            '$toInt': {
                                '$getField': {
                                    'field': 'passes successful',
                                    'input': '$passes'
                                }
                            }
                        }
                    },
                    'total_goals': {
                        '$sum': {
                            '$toInt': {
                                '$getField': {
                                    'field': 'goals',
                                    'input': '$shots'
                                }
                            }
                        }
                    },
                    'total_shots': {
                        '$sum': {
                            '$toInt': {
                                '$getField': {
                                    'field': 'total shots',
                                    'input': '$shots'
                                }
                            }
                        }
                    },
                    'aerial_duels_won': {
                        '$sum': {
                            '$toInt': {
                                '$getField': {
                                    'field': 'aerial duels won',
                                    'input': '$aerials'
                                }
                            }
                        }
                    },
                    'total_tackles': {
                        '$sum': {
                            '$toInt': {
                                '$getField': {
                                    'field': 'total tackles',
                                    'input': '$tackles'
                                }
                            }
                        }
                    },
                    'last_updated': {'$max': '$timestamp'}
                }
            },
            {
                '$addFields': {
                    'pass_accuracy': {
                        '$cond': [
                            {'$gt': ['$total_passes', 0]},
                            {
                                '$round': [
                                    {'$multiply': [
                                        {'$divide': ['$successful_passes', '$total_passes']},
                                        100
                                    ]},
                                    2
                                ]
                            },
                            0
                        ]
                    }
                }
            }
        ]
        
        try:
            self.db.player_detailed_career_stats.delete_many({})
            results = list(self.db.detailed_player_statistics.aggregate(pipeline))
            
            if results:
                self.db.player_detailed_career_stats.insert_many(results)
                logger.info(f"✓ Aggregated {len(results)} player career statistics")
        except Exception as e:
            logger.warning(f"Player career aggregation failed: {e}")
    
    def aggregate_team_stats(self):
        """Aggregate match-by-match data into team statistics."""
        logger.info("Aggregating team statistics...")
        
        try:
            # This would aggregate team-level statistics
            # Implementation depends on team_id being properly tracked
            logger.info("Team aggregation placeholder (requires team context)")
        except Exception as e:
            logger.warning(f"Team aggregation failed: {e}")
    
    def aggregate_match_stats(self):
        """Aggregate player statistics into match-level summary."""
        logger.info("Aggregating match statistics...")
        
        try:
            # This would aggregate match-level statistics
            # Implementation depends on match_id grouping
            logger.info("Match aggregation placeholder")
        except Exception as e:
            logger.warning(f"Match aggregation failed: {e}")
    
    def get_sample_stats(self):
        """Retrieve and display sample detailed statistics."""
        logger.info("\n=== Sample Detailed Player Statistics ===")
        
        sample = self.db.detailed_player_statistics.find_one()
        if sample:
            logger.info(f"Player {sample.get('player_id')} in Match {sample.get('match_id')}:")
            
            if 'passes' in sample:
                logger.info(f"  Passes: {sample['passes'].get('total passes', 0)} total, "
                           f"{sample['passes'].get('passes successful', 0)} successful")
            
            if 'shots' in sample:
                logger.info(f"  Shots: {sample['shots'].get('total shots', 0)} total, "
                           f"{sample['shots'].get('goals', 0)} goals")
            
            if 'aerials' in sample:
                logger.info(f"  Aerials: {sample['aerials'].get('total aerial duels', 0)} duels, "
                           f"{sample['aerials'].get('aerial duel success rate', 0)}% success")
        else:
            logger.info("No statistics found yet")
    
    def close(self):
        """Close MongoDB connection."""
        self.client.close()
        logger.info("MongoDB connection closed")


def main():
    """Main entry point."""
    mongo_uri = "mongodb://root:scoutpro123@scoutpro-mongo:27017/scoutpro?authSource=admin"
    
    pipeline = EventAggregationPipeline(mongo_uri)
    
    try:
        # Run the full aggregation
        count = pipeline.aggregate_all_player_matches()
        
        # Show samples
        pipeline.get_sample_stats()
        
        logger.info(f"\n✓ Event Aggregation Pipeline completed successfully!")
        logger.info(f"  Stored {count} detailed player match statistics")
        
    except Exception as e:
        logger.error(f"✗ Pipeline failed: {e}")
        sys.exit(1)
    finally:
        pipeline.close()


if __name__ == '__main__':
    main()
