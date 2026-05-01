"""
F40 Enrichment Script
Reads F40 squad list and patches MongoDB players with:
  birth_date, nationality, height, weight, preferred_foot, detailed_position
"""
import json
import os
import sys
from pymongo import MongoClient
from datetime import datetime

MONGO_URI = os.environ.get(
    "MONGODB_URL",
    "mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin"
)
F40_PATH = os.environ.get("F40_PATH", "/app/data/opta/2019/f40_115_2019")

print(f"Connecting to MongoDB: {MONGO_URI[:40]}...")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client["scoutpro"]

# Verify connection
try:
    db.command("ping")
    print("MongoDB connected OK")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    sys.exit(1)

print(f"Reading F40 from: {F40_PATH}")
with open(F40_PATH) as f:
    raw = json.load(f)

doc = raw.get("SoccerFeed", {}).get("SoccerDocument", raw)
teams = doc.get("Team", [])
if isinstance(teams, dict):
    teams = [teams]

print(f"Teams in F40: {len(teams)}")
updated = 0
not_found = 0

for team in teams:
    team_players = team.get("Player", [])
    if isinstance(team_players, dict):
        team_players = [team_players]

    for p in team_players:
        uid = p.get("@attributes", {}).get("uID", "").lstrip("p")
        if not uid:
            continue

        stat_list = p.get("Stat", [])
        if isinstance(stat_list, dict):
            stat_list = [stat_list]

        stats = {}
        for s in stat_list:
            t = s.get("@attributes", {}).get("Type", "")
            v = s.get("@value", "")
            if t and v:
                stats[t] = str(v)

        update = {}
        if stats.get("birth_date"):
            try:
                update["birth_date"] = datetime.strptime(stats["birth_date"], "%Y-%m-%d")
            except ValueError:
                pass
        if stats.get("first_nationality"):
            update["nationality"] = stats["first_nationality"]
        for field in ("height", "weight"):
            v = stats.get(field)
            if v and v not in ("Unknown", ""):
                try:
                    update[field] = int(v)
                except ValueError:
                    pass
        foot = stats.get("preferred_foot", "")
        if foot and foot not in ("Unknown", ""):
            update["preferred_foot"] = foot.lower()
        if stats.get("real_position"):
            update["detailed_position"] = stats["real_position"]

        if not update:
            continue

        update["updatedAt"] = datetime.utcnow()
        r = db.players.update_one({"uID": uid}, {"$set": update})
        if r.matched_count:
            updated += 1
        else:
            not_found += 1

print(f"Updated: {updated} | Not matched in DB: {not_found}")
sample = db.players.find_one({"birth_date": {"$ne": None}, "uID": {"$ne": None}})
if sample:
    print(
        f"Sample: {sample.get('name')} | born: {sample.get('birth_date')} "
        f"| nat: {sample.get('nationality')} | h: {sample.get('height')}cm "
        f"| foot: {sample.get('preferred_foot')}"
    )
print(f"Players with birth_date:  {db.players.count_documents({'birth_date': {'$ne': None}})}")
print(f"Players with nationality: {db.players.count_documents({'nationality': {'$ne': None}})}")
print(f"Players with height:      {db.players.count_documents({'height': {'$ne': None}})}")
