"""
Player Data Normalization Script
- Copies camelCase fields → snake_case for F40-origin players (uID with 'p' prefix)
- Re-runs F40 enrichment to set nationality (matching both uID formats)
- Ensures all players have consistent snake_case field names for the API
"""
import json
import os
import sys
from pymongo import MongoClient, UpdateOne
from datetime import datetime

MONGO_URI = os.environ.get(
    "MONGODB_URL",
    "mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin"
)
F40_PATH = os.environ.get("F40_PATH", "/app/data/opta/2019/f40_115_2019")

print(f"Connecting to MongoDB...")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client["scoutpro"]

try:
    db.command("ping")
    print("MongoDB connected OK")
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Normalise camelCase fields for F40-origin players (uID starts with 'p')
# ─────────────────────────────────────────────────────────────────────────────
print("\n[Step 1] Normalising camelCase fields for F40-origin players...")

camel_map = [
    ("birthDate", "birth_date"),
    ("preferredFoot", "preferred_foot"),
    ("shirtNumber", "shirt_number"),
    ("detailedPosition", "detailed_position"),
    ("positionSide", "position_side"),
    ("joinDate", "join_date"),
    ("birthPlace", "birth_place"),
    ("competitionID", "competition_id"),
    ("seasonID", "season_id"),
    ("teamCountry", "team_country"),
    ("teamID", "team_id"),
    ("teamName", "team_name"),
    ("squadStatus", "squad_status"),
    ("realPosition", "real_position"),
]

bulk_ops = []
for doc in db.players.find({"uID": {"$regex": "^p"}}):
    set_fields = {}
    for camel, snake in camel_map:
        val = doc.get(camel)
        if val is not None and val != "" and doc.get(snake) in (None, ""):
            # Convert birthDate string → datetime
            if camel == "birthDate" and isinstance(val, str):
                try:
                    val = datetime.strptime(val, "%Y-%m-%d")
                except ValueError:
                    pass
            elif camel == "preferredFoot" and isinstance(val, str):
                val = val.lower()
            elif camel == "shirtNumber" and val:
                try:
                    val = int(val)
                except (ValueError, TypeError):
                    pass
            set_fields[snake] = val
    if set_fields:
        set_fields["updatedAt"] = datetime.utcnow()
        bulk_ops.append(UpdateOne({"_id": doc["_id"]}, {"$set": set_fields}))

if bulk_ops:
    result = db.players.bulk_write(bulk_ops)
    print(f"  Normalised: {result.modified_count} F40-origin players")
else:
    print("  Nothing to normalise")

# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Set nationality from F40 for all players (match both uID formats)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[Step 2] Setting nationality from F40 data...")

with open(F40_PATH) as f:
    raw = json.load(f)

doc = raw.get("SoccerFeed", {}).get("SoccerDocument", raw)
teams = doc.get("Team", [])
if isinstance(teams, dict):
    teams = [teams]

updated_nat = 0
for team in teams:
    team_players = team.get("Player", [])
    if isinstance(team_players, dict):
        team_players = [team_players]

    for p in team_players:
        raw_uid = p.get("@attributes", {}).get("uID", "")  # e.g. "p45230"
        numeric_uid = raw_uid.lstrip("p")                   # e.g. "45230"
        if not numeric_uid:
            continue

        stat_list = p.get("Stat", [])
        if isinstance(stat_list, dict):
            stat_list = [stat_list]
        stats = {
            s.get("@attributes", {}).get("Type", ""): str(s.get("@value", ""))
            for s in stat_list
            if s.get("@attributes", {}).get("Type")
        }

        update = {}
        if stats.get("first_nationality"):
            update["nationality"] = stats["first_nationality"]
        if stats.get("birth_place"):
            update.setdefault("birth_place", stats["birth_place"])

        if not update:
            continue

        update["updatedAt"] = datetime.utcnow()
        # Match either format: "p45230" or "45230"
        r = db.players.update_many(
            {"$or": [{"uID": raw_uid}, {"uID": numeric_uid}],
             "nationality": None},
            {"$set": update}
        )
        if r.modified_count:
            updated_nat += r.modified_count

print(f"  Nationality set for: {updated_nat} players")

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n[Summary]")
print(f"  Total players:           {db.players.count_documents({})}")
print(f"  With birth_date:         {db.players.count_documents({'birth_date': {'$ne': None}})}")
print(f"  With nationality:        {db.players.count_documents({'nationality': {'$ne': None}})}")
print(f"  With height:             {db.players.count_documents({'height': {'$ne': None}})}")
print(f"  With preferred_foot:     {db.players.count_documents({'preferred_foot': {'$ne': None}})}")

sample = db.players.find_one({"birth_date": {"$ne": None}, "nationality": {"$ne": None}})
if sample:
    print(f"\n  Sample: {sample.get('name')} | born: {sample.get('birth_date')} | nat: {sample.get('nationality')} | h: {sample.get('height')}cm | foot: {sample.get('preferred_foot')}")
