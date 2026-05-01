#!/usr/bin/env python3
"""
Aggregate player statistics from match events and store in player_statistics collection.
"""
import os
from pymongo import MongoClient
from datetime import datetime

MONGO_URI = os.getenv('MONGO_URI', "mongodb://root:scoutpro123@scoutpro-mongo:27017/scoutpro?authSource=admin")

def aggregate_player_statistics(db):
    """Properly aggregate player stats grouped by player_id and player_name."""
    print("=== Aggregating Player Statistics ===")
    
    # Delete old collection
    db.player_statistics.delete_many({})
    
    # Proper aggregation pipeline
    pipeline = [
        {
            '$match': {
                'player_id': {'$exists': True, '$ne': None},
                'player_name': {'$exists': True, '$ne': None, '$ne': ''}
            }
        },
        {
            '$group': {
                '_id': '$player_id',
                'player_id': {'$first': '$player_id'},
                'player_name': {'$first': '$player_name'},
                'player_position': {'$first': '$player_position'},
                'teams': {'$addToSet': '$team_id'},
                'matches': {'$addToSet': '$matchID'},
                'goals': {
                    '$sum': {
                        '$cond': [
                            {'$and': [
                                {'$eq': ['$type_name', 'shot']},
                                {'$eq': ['$is_goal', True]}
                            ]},
                            1,
                            0
                        ]
                    }
                },
                'shots': {
                    '$sum': {
                        '$cond': [{'$eq': ['$type_name', 'shot']}, 1, 0]
                    }
                },
                'passes': {
                    '$sum': {
                        '$cond': [{'$eq': ['$type_name', 'pass']}, 1, 0]
                    }
                },
                'successful_passes': {
                    '$sum': {
                        '$cond': [
                            {'$and': [
                                {'$eq': ['$type_name', 'pass']},
                                {'$eq': ['$is_successful', True]}
                            ]},
                            1,
                            0
                        ]
                    }
                },
                'assists': {
                    '$sum': {
                        '$cond': [{'$eq': ['$type_name', 'assist']}, 1, 0]
                    }
                },
                'duels': {
                    '$sum': {
                        '$cond': [{'$eq': ['$type_name', 'duel']}, 1, 0]
                    }
                },
                'tackles': {
                    '$sum': {
                        '$cond': [{'$eq': ['$type_name', 'tackle']}, 1, 0]
                    }
                },
                'fouls': {
                    '$sum': {
                        '$cond': [{'$eq': ['$type_name', 'foul']}, 1, 0]
                    }
                },
                'total_events': {'$sum': 1},
            }
        },
        {
            '$addFields': {
                'match_count': {'$size': '$matches'},
                'pass_accuracy': {
                    '$cond': [
                        {'$gt': ['$passes', 0]},
                        {
                            '$round': [
                                {'$multiply': [
                                    {'$divide': ['$successful_passes', '$passes']},
                                    100
                                ]},
                                1
                            ]
                        },
                        0
                    ]
                },
                'shot_accuracy': {
                    '$cond': [
                        {'$gt': ['$shots', 0]},
                        {
                            '$round': [
                                {'$multiply': [
                                    {'$divide': ['$goals', '$shots']},
                                    100
                                ]},
                                1
                            ]
                        },
                        0
                    ]
                }
            }
        },
        {
            '$sort': {'goals': -1, 'shots': -1, 'passes': -1}
        }
    ]
    
    results = list(db.match_events.aggregate(pipeline))
    
    if results:
        db.player_statistics.insert_many(results)
        print(f"✓ Created statistics for {len(results)} players")
        
        # Create indexes
        db.player_statistics.create_index('player_id')
        db.player_statistics.create_index([('goals', -1)])
        db.player_statistics.create_index([('shots', -1)])
        db.player_statistics.create_index('player_name')
        print("✓ Created indexes")
        
        # Show top scorers
        print("\nTop 10 Scorers:")
        top = db.player_statistics.find().sort('goals', -1).limit(10)
        for i, p in enumerate(top, 1):
            print(f"  {i}. {p['player_name']} ({p['player_position']}) - "
                  f"{p['goals']} goals in {p['match_count']} matches")
    else:
        print("No events to aggregate")


if __name__ == '__main__':
    try:
        client = MongoClient(MONGO_URI)
        db = client['scoutpro']
        
        print("Aggregating player statistics...\n")
        aggregate_player_statistics(db)
        
        print("\n✅ Complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
