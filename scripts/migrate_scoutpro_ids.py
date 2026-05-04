"""
Migration: assign integer ScoutPro IDs to all existing MongoDB documents.

Run once after deploying the new id_generator (numeric IDs).

    docker exec -it scoutpro-mongo mongosh   # verify DB is up
    docker run --rm --network scoutpro_default \
        -v $(pwd)/scripts:/scripts \
        -e MONGODB_URL=mongodb://root:scoutpro123@mongo:27017/scoutpro?authSource=admin \
        python:3.11-slim bash -c "pip install pymongo -q && python /scripts/migrate_scoutpro_ids.py"

Or locally (if mongo is port-forwarded to localhost:27017):
    MONGODB_URL=mongodb://root:scoutpro123@localhost:27017/scoutpro?authSource=admin python scripts/migrate_scoutpro_ids.py
"""

import os
import uuid
import sys
from pymongo import MongoClient, UpdateOne

MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://root:scoutpro123@localhost:27017/scoutpro?authSource=admin",
)

_NS = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

_STRIP: dict[str, str] = {
    "player": "pP",
    "team": "tT",
    "match": "gG",
    "event": "",
    "competition": "cC",
    "season": "",
}


def _strip(entity: str, raw_id: str) -> str:
    chars = _STRIP.get(entity, "")
    s = str(raw_id).strip()
    if chars and s and s[0] in chars:
        s = s[1:]
    return s


def scoutpro_id(entity: str, provider: str, raw_id: str) -> int:
    key = f"{entity}:{provider.lower()}:{_strip(entity, raw_id)}"
    return int(uuid.uuid5(_NS, key).hex[:8], 16)


def migrate(db) -> None:
    # ── 1. Matches ──────────────────────────────────────────────────────────
    print("Migrating matches …")
    matches = list(db.matches.find({}, {"_id": 1, "uID": 1, "id": 1}))
    ops = []
    match_opta_to_scoutpro: dict[str, int] = {}  # "1080981" → scoutpro_id

    for m in matches:
        uid = str(m.get("uID") or "").strip()          # e.g. "g1080981"
        numeric = uid.lstrip("gG") if uid else ""       # "1080981"
        if not numeric:
            print(f"  SKIP match _id={m['_id']} — no uID")
            continue
        sid = scoutpro_id("match", "opta", uid)
        match_opta_to_scoutpro[numeric] = sid
        ops.append(UpdateOne(
            {"_id": m["_id"]},
            {"$set": {
                "scoutpro_id": sid,
                "provider_ids": {"opta": numeric},
            }},
        ))

    if ops:
        result = db.matches.bulk_write(ops, ordered=False)
        print(f"  updated {result.modified_count}/{len(matches)} match documents")

    # ── 2. Teams ─────────────────────────────────────────────────────────────
    print("Migrating teams …")
    teams = list(db.teams.find({}, {"_id": 1, "uID": 1}))
    ops = []
    for t in teams:
        uid = str(t.get("uID") or "").strip()
        numeric = uid.lstrip("tT") if uid else uid
        if not numeric:
            print(f"  SKIP team _id={t['_id']} — no uID")
            continue
        sid = scoutpro_id("team", "opta", uid)
        ops.append(UpdateOne(
            {"_id": t["_id"]},
            {"$set": {
                "scoutpro_id": sid,
                "provider_ids": {"opta": numeric},
            }},
        ))

    if ops:
        result = db.teams.bulk_write(ops, ordered=False)
        print(f"  updated {result.modified_count}/{len(teams)} team documents")

    # ── 3. Players ───────────────────────────────────────────────────────────
    print("Migrating players …")
    players = list(db.players.find({}, {"_id": 1, "uID": 1}))
    ops = []
    for p in players:
        uid = str(p.get("uID") or "").strip()
        numeric = uid.lstrip("pP") if uid else uid
        if not numeric:
            print(f"  SKIP player _id={p['_id']} — no uID")
            continue
        sid = scoutpro_id("player", "opta", uid)
        ops.append(UpdateOne(
            {"_id": p["_id"]},
            {"$set": {
                "scoutpro_id": sid,
                "provider_ids": {"opta": numeric},
            }},
        ))

    if ops:
        result = db.players.bulk_write(ops, ordered=False)
        print(f"  updated {result.modified_count}/{len(players)} player documents")

    # ── 4. Events ────────────────────────────────────────────────────────────
    # Events store the Opta numeric match ID in matchID / match_id.
    # We need to add scoutpro_match_id pointing to the parent match's ScoutPro ID.
    print("Migrating events …")

    if not match_opta_to_scoutpro:
        print("  No match mapping available — skipping events")
        return

    total = db.match_events.count_documents({})
    print(f"  {total} events to process …")

    BATCH = 10_000
    processed = 0
    ops = []

    cursor = db.match_events.find(
        {"scoutpro_match_id": {"$exists": False}},
        {"_id": 1, "matchID": 1, "match_id": 1},
        batch_size=BATCH,
    )

    for ev in cursor:
        raw_mid = str(ev.get("matchID") or ev.get("match_id") or "").strip()
        numeric_mid = raw_mid.lstrip("gG")
        sp_mid = match_opta_to_scoutpro.get(numeric_mid)

        if sp_mid is None:
            continue  # event belongs to an unknown match — skip

        ops.append(UpdateOne(
            {"_id": ev["_id"]},
            {"$set": {"scoutpro_match_id": sp_mid}},
        ))

        if len(ops) >= BATCH:
            db.match_events.bulk_write(ops, ordered=False)
            processed += len(ops)
            ops = []
            print(f"  … {processed}/{total}", end="\r", flush=True)

    if ops:
        db.match_events.bulk_write(ops, ordered=False)
        processed += len(ops)

    print(f"  updated {processed} event documents          ")

    # ── 5. Create indexes ────────────────────────────────────────────────────
    print("Creating indexes …")
    db.matches.create_index("scoutpro_id", unique=True, sparse=True, name="idx_ma_scoutpro_id")
    db.teams.create_index("scoutpro_id", unique=True, sparse=True, name="idx_tm_scoutpro_id")
    db.players.create_index("scoutpro_id", unique=True, sparse=True, name="idx_pl_scoutpro_id")
    db.match_events.create_index("scoutpro_match_id", name="idx_ev_scoutpro_match_id")
    print("  done")


def main():
    print(f"Connecting to {MONGODB_URL.split('@')[-1]} …")
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
    except Exception as exc:
        print(f"Cannot connect to MongoDB: {exc}", file=sys.stderr)
        sys.exit(1)

    db = client["scoutpro"]
    migrate(db)
    client.close()
    print("Migration complete.")


if __name__ == "__main__":
    main()
