#!/usr/bin/env python3
"""
Fix match team enrichment by using match_events to determine teams.
Also creates and exposes player statistics via API.
"""
import os
from pymongo import MongoClient
from datetime import datetime

MONGO_URI = os.getenv('MONGO_URI', "mongodb://root:scoutpro123@scoutpro-mongo:27017/scoutpro?authSource=admin")

def fix_match_teams_from_events(db):
    """Extract team names from match events to fill in match document teams."""
    print("=== Fixing Match Team Names from Events ===")
    
    # For each match, find the teams that participated
    pipeline = [
        {
            '$group': {
                '_id': '$matchID',
                'teams': {'$addToSet': '$team_id'},
                'team_names': {'$addToSet': '$team_name'}
            }
        }
    ]
    
    matches_with_teams = {}
    for doc in db.match_events.aggregate(pipeline):
        match_id = doc['_id']
        teams = [t for t in doc['teams'] if t]
        team_names = [t for t in doc['team_names'] if t]
        matches_with_teams[match_id] = {
            'teams': teams,
            'team_names': team_names
        }
    
    print(f"Found teams in {len(matches_with_teams)} matches")
    
    # Map team IDs to names
    team_map = {}
    for team in db.teams.find({}, {'uID': 1, 'name': 1}):
        if team.get('uID'):
            try:
                uid = int(team['uID'])
                team_map[uid] = team.get('name', '')
            except (ValueError, TypeError):
                pass
    
    print(f"Team map has {len(team_map)} entries")
    
    # Update matches with correct team info
    updated = 0
    for match_id, data in matches_with_teams.items():
        teams = data['teams']
        team_names = data['team_names']
        
        update_dict = {}
        
        # If we have actual team names from events, use those
        if len(team_names) >= 2:
            update_dict['home_team'] = team_names[0]
            update_dict['away_team'] = team_names[1]
        elif len(team_names) == 1:
            update_dict['home_team'] = team_names[0]
        
        # If we have team IDs, map them to names
        if not update_dict and len(teams) >= 2:
            if teams[0] in team_map:
                update_dict['home_team'] = team_map[teams[0]]
            if teams[1] in team_map:
                update_dict['away_team'] = team_map[teams[1]]
        
        if update_dict:
            update_dict['enrichedAt'] = datetime.utcnow()
            result = db.matches.update_one(
                {'uID': match_id},
                {'$set': update_dict}
            )
            updated += result.modified_count
    
    print(f"Updated {updated} matches with corrected team names")
    
    # Show sample
    sample = db.matches.find_one({'home_team': {'$exists': True, '$ne': None}})
    if sample:
        print(f"Sample: {sample.get('home_team')} vs {sample.get('away_team')}")


def ensure_player_stats_indexed(db):
    """Ensure player_statistics collection has proper indexes."""
    print("\n=== Indexing Player Statistics ===")
    
    count = db.player_statistics.count_documents({})
    print(f"Player statistics documents: {count}")
    
    # Create useful indexes
    db.player_statistics.create_index('player_id', unique=True)
    db.player_statistics.create_index([('goals', -1)])
    db.player_statistics.create_index([('shots', -1)])
    db.player_statistics.create_index('player_name')
    
    print("Created indexes on player_statistics")


if __name__ == '__main__':
    try:
        client = MongoClient(MONGO_URI)
        db = client['scoutpro']
        
        print("Starting fix process...")
        print(f"Database: {db.name}\n")
        
        fix_match_teams_from_events(db)
        ensure_player_stats_indexed(db)
        
        print("\n✅ Fix complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
