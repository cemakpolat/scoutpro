"""
Provider batch synchronization.

Runs event sync in batches after discovering match IDs from a provider connector.
This is the missing bridge between an external provider server and ScoutPro's
entity-level syncers.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from shared.adapters.factory import get_factory

from sync.base_syncer import SyncResult, SyncStatus
from sync.event_syncer import EventSyncer


class EventBatchSyncer:
    """
    Discover provider matches and sync their event feeds in batches.

    The per-match event transformation remains in EventSyncer. This class only
    owns match discovery, batching, and aggregate reporting.
    """

    def __init__(self, provider: str, config: Optional[Dict[str, Any]] = None):
        self.provider = provider
        self.config = config or {}
        self.factory = get_factory()

    async def sync(self, **kwargs) -> SyncResult:
        started_at = datetime.now()
        config = {**self.config, **kwargs}

        matches = await self.discover_matches(**config)
        batch_size = max(int(config.get("batch_size", 5)), 1)

        if not matches:
            return SyncResult(
                status=SyncStatus.COMPLETED,
                duration_seconds=(datetime.now() - started_at).total_seconds(),
                metadata={
                    "provider": self.provider,
                    "mode": "event_batch",
                    "selected_match_count": 0,
                    "discovered_match_count": 0,
                },
            )

        total_fetched = 0
        total_created = 0
        total_updated = 0
        total_merged = 0
        total_conflicts = 0
        errors: List[str] = []
        successful_matches: List[str] = []

        for index in range(0, len(matches), batch_size):
            batch = matches[index:index + batch_size]
            results = await asyncio.gather(
                *(self._sync_match(match["match_id"], config) for match in batch),
                return_exceptions=True,
            )

            for match, result in zip(batch, results):
                match_id = match["match_id"]

                if isinstance(result, Exception):
                    errors.append(f"{match_id}: {result}")
                    continue

                if result.errors:
                    errors.extend([f"{match_id}: {error}" for error in result.errors])

                if result.status in (SyncStatus.COMPLETED, SyncStatus.PARTIAL):
                    successful_matches.append(match_id)

                total_fetched += result.entities_fetched
                total_created += result.entities_created
                total_updated += result.entities_updated
                total_merged += result.entities_merged
                total_conflicts += result.conflicts_detected

        if errors and successful_matches:
            status = SyncStatus.PARTIAL
        elif errors:
            status = SyncStatus.FAILED
        else:
            status = SyncStatus.COMPLETED

        return SyncResult(
            status=status,
            entities_fetched=total_fetched,
            entities_created=total_created,
            entities_updated=total_updated,
            entities_merged=total_merged,
            conflicts_detected=total_conflicts,
            errors=errors[:100],
            duration_seconds=(datetime.now() - started_at).total_seconds(),
            metadata={
                "provider": self.provider,
                "mode": "event_batch",
                "selected_match_count": len(matches),
                "successful_match_count": len(successful_matches),
                "discovered_match_count": len(matches),
                "batch_size": batch_size,
                "match_ids": [match["match_id"] for match in matches[:50]],
            },
        )

    async def discover_matches(self, **kwargs) -> List[Dict[str, Any]]:
        connector = self.factory.get_connector(self.provider, kwargs)
        raw_matches = await connector.fetch_matches(
            competition_id=kwargs.get("competition_id"),
            season_id=kwargs.get("season_id"),
            date_from=kwargs.get("date_from"),
            date_to=kwargs.get("date_to"),
        )

        lookback_days = kwargs.get("lookback_days")
        lookahead_days = kwargs.get("lookahead_days")
        max_matches = kwargs.get("max_matches")

        now = datetime.utcnow()
        window_start = now - timedelta(days=int(lookback_days)) if lookback_days is not None else None
        window_end = now + timedelta(days=int(lookahead_days)) if lookahead_days is not None else None

        discovered: List[Dict[str, Any]] = []
        for raw_match in raw_matches:
            match_id = self._extract_match_id(raw_match)
            if not match_id:
                continue

            match_date = self._extract_match_date(raw_match)
            if window_start and match_date and match_date < window_start:
                continue
            if window_end and match_date and match_date > window_end:
                continue

            discovered.append(
                {
                    "match_id": match_id,
                    "date": match_date.isoformat() if match_date else None,
                }
            )

        discovered.sort(key=lambda match: match["date"] or "", reverse=True)

        if max_matches is not None:
            discovered = discovered[:max(int(max_matches), 0)]

        return discovered

    async def _sync_match(self, match_id: str, config: Dict[str, Any]) -> SyncResult:
        syncer = EventSyncer(provider=self.provider, config=config)
        return await syncer.sync(match_id=match_id)

    @staticmethod
    def _extract_match_id(raw_match: Dict[str, Any]) -> Optional[str]:
        attrs = raw_match.get("@attributes", {}) if isinstance(raw_match, dict) else {}
        provider_ids = raw_match.get("provider_ids", {}) if isinstance(raw_match, dict) else {}

        candidates = [
            raw_match.get("match_id"),
            raw_match.get("uID"),
            raw_match.get("id"),
            raw_match.get("external_id"),
            attrs.get("uID"),
            provider_ids.get("opta"),
            provider_ids.get("statsbomb"),
        ]

        for candidate in candidates:
            if candidate:
                return str(candidate).lstrip("g")

        return None

    @staticmethod
    def _extract_match_date(raw_match: Dict[str, Any]) -> Optional[datetime]:
        candidates = [
            raw_match.get("date"),
            raw_match.get("match_date"),
            raw_match.get("utc_date"),
            raw_match.get("kickoff_time"),
            raw_match.get("timestamp"),
        ]

        for candidate in candidates:
            if not candidate or not isinstance(candidate, str):
                continue

            normalized = candidate.replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(normalized)
            except ValueError:
                continue

            if parsed.tzinfo is not None:
                return parsed.replace(tzinfo=None)
            return parsed

        return None