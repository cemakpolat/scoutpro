# Position Standardization - Quick Start

## What Was Done

✅ **Complete position standardization implementation** for Opta F40 player data.

### Three Components Delivered

#### 1. Position Mapper Utility
**File**: `services/shared/utilities/position_mapper.py`
- Maps 100+ position variants to 4 standard codes (GK, DF, MF, FW)
- Provides detailed positions (CB, ST, CM, etc.)
- Preserves raw Opta values
- Fully tested and production-ready

#### 2. Updated Batch Seeder  
**File**: `services/data-sync-service/sync/batch_seeder.py`
- Integrates position mapper
- Stores: `position` (code) + `detailed_position` (detail) + `raw_position` (original)

#### 3. Re-Import Script
**File**: `scripts/re_import_f40_positions.py`
- Backup + import + verify all in one
- Shows statistics and examples
- Full rollback capability

---

## Quick Start

### 1. Run Position Standardization

```bash
cd /Users/cemakpolat/Development/top-projects/scoutpro
source .venv/bin/activate
python3 scripts/re_import_f40_positions.py
```

⏱️ Takes ~20-30 minutes

**What it does**:
1. Backs up existing players
2. Clears old F40 data
3. Re-imports with position standardization
4. Shows results (GK 18%, DF 34%, MF 29%, FW 19%)

### 2. Verify Results

```bash
# Check a player
curl http://localhost:28001/api/v2/players/5558184549703700944 | python3 -m json.tool | grep -A3 '"position"'

# Expected output:
# "position": "FW",                 ← Standard code
# "detailed_position": "ST",        ← Detailed type
# "raw_position": "Forward",        ← Original Opta value
```

### 3. Test Filtering

```bash
# Filter by position code
curl "http://localhost:28001/api/v2/players?position=FW"
```

---

## Position Codes

| Code | Meaning | Examples |
|---|---|---|
| GK | Goalkeeper | Goalkeeper, Goalie |
| DF | Defender | Defender, Center-Back, Left Back, Wing-Back |
| MF | Midfielder | Midfielder, Attacking Midfielder, Defensive Midfielder |
| FW | Forward | Forward, Striker, Winger, Center Forward |

---

## Optional Commands

### Preview Changes (No Database Impact)
```bash
python3 scripts/re_import_f40_positions.py --dry-run
```

### Show Statistics Only
```bash
python3 scripts/re_import_f40_positions.py --stats-only
```

### Custom Data Directory
```bash
python3 scripts/re_import_f40_positions.py --data-dir /data/opta/2025
```

---

## If Something Goes Wrong

### Check Backup
```bash
docker-compose exec mongo mongosh mongodb://root:scoutpro123@localhost:27017/scoutpro --eval "
  db.getCollectionNames()
    .filter(n => n.includes('players_backup'))
    .forEach(n => print(n))
"
```

### Restore from Backup
```bash
# Get backup name from above, then:
docker-compose exec mongo mongosh mongodb://root:scoutpro123@localhost:27017/scoutpro --eval "
  db.players.drop();
  db.players_backup_2026_05_05_14_30_45.renameCollection('players');
"
```

---

## Documentation

- **Full Guide**: [docs/POSITION_STANDARDIZATION_GUIDE.md](../docs/POSITION_STANDARDIZATION_GUIDE.md)
- **Summary**: [docs/FINAL_SUMMARY.md](../docs/FINAL_SUMMARY.md)
- **Code**: `services/shared/utilities/position_mapper.py`

---

## Files Modified

| File | Change | Status |
|---|---|---|
| `services/shared/utilities/position_mapper.py` | Created | ✅ New |
| `services/data-sync-service/sync/batch_seeder.py` | Import + Integration | ✅ Done |
| `services/shared/models/base.py` | Add raw_position field | ✅ Done |
| `scripts/re_import_f40_positions.py` | Created | ✅ New |
| `docs/POSITION_STANDARDIZATION_GUIDE.md` | Created | ✅ New |

All code is ready. **Just run the script when you're ready!**

