"""
Golden Record Migration: generate scoutpro_id and provider_ids for all players.

Algorithm:
  scoutpro_id = "sp_" + uuid5(SCOUTPRO_NS, "opta:<numeric_uid>").hex[:12]

  provider_ids = {
      "opta": "<numeric_uid>",           # always present
      "statsbomb": "<sb_id>",            # only if matched by SB enrichment
  }

This is idempotent — re-running will skip players that already have scoutpro_id.
"""
import os
import sys
import uuid
from pymongo import MongoClient, UpdateOne
from datetime import datetime

MONGO_URI = os.environ.get(
    "MONGODB_URL",
    "mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin"
)

# Stable namespace for ScoutPro canonical IDs
SCOUTPRO_NS = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def gen_scoutpro_id(opta_uid: str) -> str:
    """Deterministically derive a ScoutPro canonical ID from an Opta uID."""
    numeric = opta_uid.lstrip("p")
    return "sp_" + uuid.uuid5(SCOUTPRO_NS, f"opta:{numeric}").hex[:12]


print("Connecting to MongoDB...")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client["scoutpro"]

try:
    db.command("ping")
    print("Connected OK")
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

total = db.players.count_documents({})
already_done = db.players.count_documents({"scoutpro_id": {"$exists": True}})
print(f"Total players: {total} | Already migrated: {already_done}")

bulk_ops = []
skipped = 0

for doc in db.players.find({}):
    uid = doc.get("uID", "")
    if not uid:
        skipped += 1
        continue

    uid_str = str(uid)
    numeric_uid = uid_str.lstrip("p")

    scoutpro_id = gen_scoutpro_id(uid_str)

    # Build provider_ids — start from existing if present
    provider_ids = doc.get("provider_ids", {})
    provider_ids["opta"] = numeric_uid  # always the numeric Opta ID

    # If this doc already had a statsbombEnrichment, extract SB player ref if any
    sb_enrich = doc.get("statsbombEnrichment", {})
    if sb_enrich and sb_enrich.get("statsbomb_player_id"):
        provider_ids["statsbomb"] = str(sb_enrich["statsbomb_player_id"])

    update = {
        "$set": {
            "scoutpro_id": scoutpro_id,
            "provider_ids": provider_ids,
            "updatedAt": datetime.utcnow(),
        }
    }

    bulk_ops.append(UpdateOne({"_id": doc["_id"]}, update))

    # Flush in batches of 500
    if len(bulk_ops) >= 500:
        db.players.bulk_write(bulk_ops, ordered=False)
        bulk_ops = []

if bulk_ops:
    db.players.bulk_write(bulk_ops, ordered=False)

print(f"Migrated: {total - skipped} players | Skipped (no uID): {skipped}")

# Verify
with_id = db.players.count_documents({"scoutpro_id": {"$exists": True}})
with_provider = db.players.count_documents({"provider_ids.opta": {"$exists": True}})
print(f"With scoutpro_id:       {with_id}")
print(f"With provider_ids.opta: {with_provider}")

# Sample
sample = db.players.find_one({"scoutpro_id": {"$exists": True}})
if sample:
    print(f"\nSample: {sample.get('name')}")
    print(f"  scoutpro_id:  {sample.get('scoutpro_id')}")
    print(f"  provider_ids: {sample.get('provider_ids')}")
    print(f"  uID (legacy): {sample.get('uID')}")
