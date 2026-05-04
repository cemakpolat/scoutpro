"""ScoutPro unified identifier generation.

All entity primary keys in the system MUST be ScoutPro IDs — pure integers.
Provider-specific IDs (Opta uID, StatsBomb ID, Wyscout ID …) are stored as
secondary lookup references in a ``provider_ids`` sub-document, e.g.::

    {
        "scoutpro_id": 1563959217,
        "provider_ids": {
            "opta": "1080981",
            "statsbomb": "3318",
        }
    }

Algorithm
---------
    scoutpro_id = int(uuid5(SCOUTPRO_NS, "<entity>:<provider>:<stripped_raw_id>").hex[:16], 16) & 0x7FFFFFFFFFFFFFFF

UUID5 is deterministic — the same provider entity always maps to the same
ScoutPro ID with no database lookup.  The namespace UUID is fixed once and
must NEVER change after the first deployment.  Including entity type in the
hash key ensures a match and a player sharing the same provider numeric ID
receive different ScoutPro IDs.

The resulting value fits in a signed 64-bit integer (63 usable bits, max
~9.2 quintillion) so it is directly storable in MongoDB, PostgreSQL bigint,
and TimescaleDB without overflow.  Birthday collision probability stays below
0.05% up to 100 million entities of the same type.

Usage
-----
    from shared.utils.id_generator import ScoutProId

    player_id = ScoutProId.player("opta", "p101380")   # → integer
    team_id   = ScoutProId.team("opta", "t405")        # → integer
    match_id  = ScoutProId.match("opta", "g2187923")   # → integer
    event_id  = ScoutProId.event("opta", "12345678")   # → integer
"""

from __future__ import annotations

import uuid
from typing import Optional

# ---------------------------------------------------------------------------
# Fixed namespace — NEVER change after initial deployment.
# ---------------------------------------------------------------------------
_NS = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

# Characters to strip from provider IDs before hashing so that
# "p101380", "P101380", and "101380" all resolve to the same ScoutPro ID.
_STRIP_CHARS_BY_ENTITY: dict[str, str] = {
    "player":      "pP",
    "team":        "tT",
    "match":       "gG",
    "event":       "",
    "competition": "cC",
    "season":      "",
}


def _strip(entity: str, raw_id: str) -> str:
    """Remove provider-specific prefix characters from *raw_id*."""
    chars = _STRIP_CHARS_BY_ENTITY.get(entity, "")
    stripped = str(raw_id).strip()
    if chars and stripped and stripped[0] in chars:
        stripped = stripped[1:]
    return stripped


def generate(entity: str, provider: str, raw_id: str) -> int:
    """Return a deterministic numeric ScoutPro ID for *entity* sourced from *provider*.

    Args:
        entity:   One of ``player``, ``team``, ``match``, ``event``,
                  ``competition``, ``season``.
        provider: Provider name, e.g. ``opta``, ``statsbomb``, ``wyscout``.
        raw_id:   Provider-specific identifier (may carry a letter prefix).

    Returns:
        A stable integer ScoutPro ID (positive signed int64, MongoDB/PG safe).
    """
    key = f"{entity}:{provider.lower()}:{_strip(entity, raw_id)}"
    return int(uuid.uuid5(_NS, key).hex[:16], 16) & 0x7FFFFFFFFFFFFFFF


class ScoutProId:
    """Namespace class with one convenience method per entity type."""

    @staticmethod
    def player(provider: str, raw_id: str) -> int:
        return generate("player", provider, raw_id)

    @staticmethod
    def team(provider: str, raw_id: str) -> int:
        return generate("team", provider, raw_id)

    @staticmethod
    def match(provider: str, raw_id: str) -> int:
        return generate("match", provider, raw_id)

    @staticmethod
    def event(provider: str, raw_id: str) -> int:
        return generate("event", provider, raw_id)

    @staticmethod
    def competition(provider: str, raw_id: str) -> int:
        return generate("competition", provider, raw_id)

    @staticmethod
    def season(provider: str, raw_id: str) -> int:
        return generate("season", provider, raw_id)

    @staticmethod
    def provider_numeric(entity: str, raw_id: str) -> str:
        """Return the numeric portion of a provider ID (strips letter prefix).

        Stored in ``provider_ids`` — e.g. Opta ``"p101380"`` → ``"101380"``.
        """
        return _strip(entity, raw_id)
