"""MongoDB index definitions for the ScoutPro platform.

All indexes are defined here as a single source of truth and are applied
idempotently (``background=True``, named, so re-runs are safe).

Replacing: scripts/create_event_indexes.py, scripts/create_optimized_event_indexes.py

Usage (called from each service's startup)::

    from shared.database.indexes import ensure_indexes
    await ensure_indexes(motor_db)          # async Motor driver
    # — or synchronous —
    from shared.database.indexes import ensure_indexes_sync
    ensure_indexes_sync(pymongo_db)
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Index specification
# Each entry: (collection_name, [(field, direction), …], options)
# ---------------------------------------------------------------------------
_ASCENDING = 1
_DESCENDING = -1

_INDEX_SPECS: list[tuple[str, list[tuple[str, int]], dict[str, Any]]] = [
    # ── match_events ────────────────────────────────────────────────────────
    ("match_events", [("player_id", _ASCENDING)],
     {"name": "idx_me_player_id", "sparse": True}),

    ("match_events", [("playerID", _ASCENDING)],
     {"name": "idx_me_playerID", "sparse": True}),

    ("match_events", [("matchID", _ASCENDING)],
     {"name": "idx_me_matchID", "sparse": True}),

    ("match_events", [("match_id", _ASCENDING)],
     {"name": "idx_me_match_id", "sparse": True}),

    # ScoutPro canonical ID columns (set by new ID generator)
    ("match_events", [("scoutpro_player_id", _ASCENDING)],
     {"name": "idx_me_sp_player", "sparse": True}),

    ("match_events", [("scoutpro_match_id", _ASCENDING)],
     {"name": "idx_me_sp_match", "sparse": True}),

    # Composite: player lookup within a match
    ("match_events", [("player_id", _ASCENDING), ("matchID", _ASCENDING)],
     {"name": "idx_me_player_match"}),

    # Composite: event type within a match
    ("match_events", [("type_name", _ASCENDING), ("matchID", _ASCENDING)],
     {"name": "idx_me_type_match"}),

    # Derived analytics flags (used by statistics-service hot-path queries)
    ("match_events", [("type_name", _ASCENDING), ("is_goal", _ASCENDING), ("period", _ASCENDING)],
     {"name": "idx_me_type_goal_period", "sparse": True}),

    ("match_events", [("progressive_pass", _ASCENDING)],
     {"name": "idx_me_progressive_pass", "sparse": True}),

    ("match_events", [("analytical_xg", _DESCENDING)],
     {"name": "idx_me_xg", "sparse": True}),

    ("match_events", [("high_regain", _ASCENDING)],
     {"name": "idx_me_high_regain", "sparse": True}),

    # Timestamp ordering
    ("match_events", [("timestamp", _DESCENDING)],
     {"name": "idx_me_timestamp"}),

    ("match_events", [("ingested_at", _DESCENDING)],
     {"name": "idx_me_ingested_at", "sparse": True}),

    # ── matches ─────────────────────────────────────────────────────────────
    ("matches", [("uID", _ASCENDING)],
     {"name": "idx_ma_uID", "unique": True, "sparse": True}),

    ("matches", [("scoutpro_id", _ASCENDING)],
     {"name": "idx_ma_scoutpro_id", "unique": True, "sparse": True}),

    ("matches", [("provider_ids.opta", _ASCENDING)],
     {"name": "idx_ma_prov_opta", "sparse": True}),

    ("matches", [("status", _ASCENDING), ("date", _DESCENDING)],
     {"name": "idx_ma_status_date"}),

    # ── players ─────────────────────────────────────────────────────────────
    ("players", [("scoutpro_id", _ASCENDING)],
     {"name": "idx_pl_scoutpro_id", "unique": True, "sparse": True}),

    ("players", [("provider_ids.opta", _ASCENDING)],
     {"name": "idx_pl_prov_opta", "sparse": True}),

    ("players", [("provider_ids.statsbomb", _ASCENDING)],
     {"name": "idx_pl_prov_statsbomb", "sparse": True}),

    ("players", [("uID", _ASCENDING)],
     {"name": "idx_pl_uID", "sparse": True}),

    # ── teams ───────────────────────────────────────────────────────────────
    ("teams", [("scoutpro_id", _ASCENDING)],
     {"name": "idx_tm_scoutpro_id", "unique": True, "sparse": True}),

    ("teams", [("provider_ids.opta", _ASCENDING)],
     {"name": "idx_tm_prov_opta", "sparse": True}),

    ("teams", [("uID", _ASCENDING)],
     {"name": "idx_tm_uID", "sparse": True}),

    # ── player_statistics ────────────────────────────────────────────────────
    ("player_statistics", [("player_id", _ASCENDING)],
     {"name": "idx_ps_player_id"}),

    ("player_statistics", [("scoutpro_player_id", _ASCENDING)],
     {"name": "idx_ps_sp_player", "sparse": True}),

    ("player_statistics", [("match_id", _ASCENDING)],
     {"name": "idx_ps_match_id"}),

    ("player_statistics",
     [("player_id", _ASCENDING), ("match_id", _ASCENDING)],
     {"name": "idx_ps_player_match", "unique": True}),
]


def ensure_indexes_sync(db: Any) -> None:
    """Apply all indexes using a **synchronous** PyMongo database handle."""
    for collection_name, key_list, options in _INDEX_SPECS:
        col = db[collection_name]
        try:
            col.create_index(key_list, background=True, **options)
            logger.debug("Index ensured: %s.%s", collection_name, options["name"])
        except Exception as exc:
            # Conflict (e.g., same name, different definition) — log and continue.
            logger.warning(
                "Index %s.%s skipped: %s", collection_name, options["name"], exc
            )
    logger.info("MongoDB indexes ensured (%d specs)", len(_INDEX_SPECS))


async def ensure_indexes(db: Any) -> None:
    """Apply all indexes using an **async** Motor database handle."""
    for collection_name, key_list, options in _INDEX_SPECS:
        col = db[collection_name]
        try:
            await col.create_index(key_list, background=True, **options)
            logger.debug("Index ensured: %s.%s", collection_name, options["name"])
        except Exception as exc:
            logger.warning(
                "Index %s.%s skipped: %s", collection_name, options["name"], exc
            )
    logger.info("MongoDB indexes ensured (%d specs)", len(_INDEX_SPECS))
