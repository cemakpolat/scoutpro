#!/usr/bin/env python3
"""
Enrich match documents with team names and match events with player names.
This ensures all frontend displays have proper labels instead of just IDs.
"""
import os
import sys
from pymongo import MongoClient
from datetime import datetime

MONGO_URI = os.getenv('MONGO_URI', "mongodb://root:scoutpro123@scoutpro-mongo:27017/scoutpro?authSource=admin")

def enrich_matches(db):
    """Enrich match documents with team names from teams collection."""
    print("=== Enriching Matches ===")
    
    teams_dict = {}
    for team in db.teams.find({}, {'_id': 0, 'uID': 1, 'name': 1}):
        if team.get('uID'):
            teams_dict[team['uID']] = team.get('name', '')
    
    print(f"Found {len(teams_dict)} teams in database")
    
    matches = db.matches.find({})
    updated = 0
    
    for match in matches:
        update_dict = {}
        
        # Use homeTeamID to get home team name
        if match.get('homeTeamID') and match.get('homeTeamID') in teams_dict:
            update_dict['home_team'] = teams_dict[match['homeTeamID']]
        
        # Use awayTeamID to get away team name
        if match.get('awayTeamID') and match.get('awayTeamID') in teams_dict:
            update_dict['away_team'] = teams_dict[match['awayTeamID']]
        
        if update_dict:
            update_dict['enrichedAt'] = datetime.utcnow()
            result = db.matches.update_one(
                {'_id': match['_id']},
                {'$set': update_dict}
            )
            updated += result.modified_count
    
    print(f"Updated {updated} matches with team names")
    
    # Show sample
    sample = db.matches.find_one({})
    if sample:
        print(f"Sample match: {sample.get('home_team')} vs {sample.get('away_team')}")


def enrich_events(db):
    """Enrich match events with player names from players collection."""
    print("\n=== Enriching Match Events ===")
    
    # Build player name map
    players_dict = {}
    for player in db.players.find({}, {'_id': 0, 'uID': 1, 'name': 1, 'position': 1}):
        if player.get('uID'):
            try:
                uid = int(player['uID'])
                players_dict[uid] = {
                    'name': player.get('name', ''),
                    'position': player.get('position', '')
                }
            except (ValueError, TypeError):
                pass
    
    print(f"Found {len(players_dict)} players in database")
    
    # Count events needing enrichment
    events_without_names = db.match_events.count_documents({'player_name': {'$exists': False}})
    print(f"Match events without player_name: {events_without_names}")
    
    if events_without_names > 0:
        # Batch update events
        events = db.match_events.find({'player_name': {'$exists': False}})
        updated = 0
        
        for event in events:
            player_id = event.get('player_id')
            if player_id and player_id in players_dict:
                player_info = players_dict[player_id]
                db.match_events.update_one(
                    {'_id': event['_id']},
                    {'$set': {
                        'player_name': player_info['name'],
                        'player_position': player_info['position'],
                        'enrichedAt': datetime.utcnow()
                    }}
                )
                updated += 1
        
        print(f"Updated {updated} events with player names")
    
    # Show sample
    sample = db.match_events.find_one({'player_name': {'$exists': True, '$ne': None}})
    if sample:
        print(f"Sample event: {sample.get('player_name')} ({sample.get('player_position')}) - {sample.get('type_name')}")


def aggregate_player_statistics(db):
    """
    Aggregate player statistics from match events.
    Creates a new collection: player_statistics
    """
    print("\n=== Aggregating Player Statistics ===")
    
    # Clear existing stats
    db.player_statistics.delete_many({})
    
    # Aggregate stats by player
    pipeline = [
        {
            '$group': {
                '_id': '$player_id',
                'player_name': {'$first': '$player_name'},
                'player_position': {'$first': '$player_position'},
                'matches': {'$addToSet': '$matchID'},
                'goals': {
                    '$sum': {
                        '$cond': [{'$and': [
                            {'$eq': ['$type_name', 'shot']},
                            {'$eq': ['$is_goal', True]}
                        ]}, 1, 0]
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
        print(f"Created statistics for {len(results)} players")
        
        # Show top 5
        print("\nTop 5 Players by Goals:")
        top_players = db.player_statistics.find().sort('goals', -1).limit(5)
        for i, p in enumerate(top_players, 1):
            pass_acc = p.get('pass_accuracy', 0)
            print(f"{i}. {p.get('player_name', 'Unknown')} - "
                  f"{p['goals']} goals, {p['shots']} shots, "
                  f"{p['passes']} passes ({pass_acc}% accuracy)")
    else:
        print("No events to aggregate")


if __name__ == '__main__':
    try:
        client = MongoClient(MONGO_URI)
        db = client['scoutpro']
        
        print("Starting enrichment process...")
        print(f"Database: {db.name}")
        print()
        
        enrich_matches(db)
        enrich_events(db)
        aggregate_player_statistics(db)
        
        print("\n✅ Enrichment complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        client.close()
