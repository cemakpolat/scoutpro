"""
Connector — New Architecture

Replaces the legacy MongoEngine/src.* connector.
Reads Opta feed files from disk and delegates storage to Motor (async MongoDB).
The old src.dbase / src.parse / src.utils chain has been removed.
"""

import logging
import os
import json
from typing import Optional, Dict, Any

try:
    import httpx as _httpx
except ImportError:  # pragma: no cover
    _httpx = None  # type: ignore

logger = logging.getLogger(__name__)

# Canonical feed-name normalisation table
FEED_NAME_MAP = {
    "feed40": "f40", "f40": "f40",
    "feed1":  "f1",  "f1":  "f1",
    "feed9":  "f9",  "f9":  "f9",
    "feed24": "f24", "f24": "f24",
}

# DATA_DIR is resolved at import time; override via DATA_ROOT env var
DATA_ROOT = os.environ.get("DATA_ROOT", os.path.join(os.path.dirname(__file__), "../../../../data"))


class Connector:
    def __init__(self, name: str = "scoutpro", port: int = 27017,
                 host: str = "mongo", alias: str = "default"):
        logger.info("Connector initialised (new architecture, file-based)")
        self.db_name = name
        self.db_port = port
        self.host = host
        self.alias = alias
        self.online = False

        self.feed_name: Optional[str] = None
        self.competition_id: Optional[int] = None
        self.season_id: Optional[int] = None
        self.game_id: Optional[int] = None

    # ------------------------------------------------------------------
    # Connection lifecycle (kept for API compatibility; Motor is async,
    # so real DB connections happen inside individual service repositories)
    # ------------------------------------------------------------------
    def connect(self) -> "Connector":
        return self

    def disconnect(self) -> "Connector":
        return self

    def setOnline(self, online: bool) -> "Connector":
        self.online = online
        return self

    def assign_feed_vars(self, feed_name: str, competition_id: int,
                         season_id: int, game_id: int = None) -> "Connector":
        self.feed_name = feed_name
        self.competition_id = competition_id
        self.season_id = season_id
        self.game_id = game_id
        return self

    # Base URL for an external Opta-compatible provider server.
    # Set via OPTA_BASE_URL env var; defaults to the local mock server name.
    OPTA_BASE_URL: str = os.environ.get("OPTA_BASE_URL", "http://data-provider-mock:7000")

    def getFeed(self, feed_name: str, competition_id: int,
                season_id: int, game_id: int = None) -> Dict[str, Any]:
        """
        Load an Opta feed.

        When online=False (default): reads local files from DATA_ROOT/opta/.
        When online=True: fetches via HTTP from OPTA_BASE_URL using the
          data-provider-mock endpoint pattern:
            /api/football/f{N}/{competition_id}/{season_id}[/{match_id}]
        """
        self.assign_feed_vars(feed_name, competition_id, season_id, game_id)
        short_name = FEED_NAME_MAP.get(feed_name, feed_name)

        if self.online:
            return self._fetch_online(short_name, competition_id, season_id, game_id)

        base_stem_no_game = f"{short_name}_{competition_id}_{season_id}"
        base_stem_alt = f"{short_name}_{season_id}_{competition_id}"

        if game_id is not None:
            stems = [
                f"{base_stem_no_game}_{game_id}",
                f"{base_stem_alt}_{game_id}",
            ]
        else:
            stems = [base_stem_no_game, base_stem_alt]

        opta_root = os.path.join(DATA_ROOT, "opta")
        search_dirs = [
            opta_root,
            os.path.join(opta_root, str(season_id)),
            os.path.join(opta_root, str(competition_id), str(season_id)),
            os.path.join(opta_root, str(season_id), str(competition_id)),
        ]

        for directory in search_dirs:
            for stem in stems:
                candidate = os.path.join(directory, stem)
                if os.path.isfile(candidate):
                    return self._load_file(candidate)

        logger.warning(
            f"Feed not found: {feed_name} comp={competition_id} "
            f"season={season_id} game={game_id}. Searched: {search_dirs}"
        )
        return {}

    def _fetch_online(self, short_name: str, competition_id: int,
                       season_id: int, game_id: Optional[int]) -> Dict[str, Any]:
        """
        Fetch a feed from the HTTP provider server.

        URL pattern (matching the ScoutPro provider server contract):
          GET {OPTA_BASE_URL}/api/football/{short_name}/{competition_id}/{season_id}
          GET {OPTA_BASE_URL}/api/football/{short_name}/{competition_id}/{season_id}/{game_id}
        """
        if _httpx is None:
            logger.error("httpx is not installed; cannot fetch online feed. "
                         "Install it with: pip install httpx")
            return {}

        feed_num = short_name.lstrip("f")  # "f1" → "1", "f24" → "24"
        if game_id is not None:
            url = (f"{self.OPTA_BASE_URL}/api/football/{short_name}/"
                   f"{competition_id}/{season_id}/{game_id}")
        else:
            url = (f"{self.OPTA_BASE_URL}/api/football/{short_name}/"
                   f"{competition_id}/{season_id}")

        try:
            resp = _httpx.get(url, timeout=15.0)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            if "json" in content_type or resp.content[:1] in (b"{", b"["):
                return resp.json()
            # XML response: try to convert via xmltodict if available
            try:
                import xmltodict
                return xmltodict.parse(resp.text)
            except ImportError:
                logger.error(
                    "Feed response is XML but xmltodict is not installed. "
                    "Install it with: pip install xmltodict"
                )
                return {}
        except Exception as exc:
            logger.error(f"Online feed fetch failed [{url}]: {exc}")
            return {}

    @staticmethod
    def _load_file(path: str) -> Dict[str, Any]:
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, IOError) as exc:
            logger.error(f"Failed to load feed file {path}: {exc}")
            return {}


main_conn = Connector()
