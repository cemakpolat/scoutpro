"""
Sync Scheduler

Orchestrates periodic synchronization jobs for all providers and entities.
"""

import asyncio
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import schedule
import time

from sync.player_syncer import PlayerSyncer
from sync.team_syncer import TeamSyncer
from sync.match_syncer import MatchSyncer
from sync.event_syncer import EventSyncer
from sync.provider_batch_sync import EventBatchSyncer
from sync.base_syncer import SyncResult


class SyncFrequency(Enum):
    """Sync frequency options"""
    REALTIME = "realtime"  # Every minute (for live matches)
    FREQUENT = "frequent"  # Every 15 minutes
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MANUAL = "manual"


DEFAULT_PROVIDER_SYNC_PROFILES: Dict[str, Dict[str, Any]] = {
    'opta': {
        'weekly_match_volume': 10,
        'notes': (
            'Assumes one domestic league competition with roughly 10 fixtures per '
            'week. Refresh squads daily, fixtures hourly, and recent F24 event '
            'windows every 15 minutes for the last 72 hours.'
        ),
        'jobs': {
            'teams': SyncFrequency.DAILY,
            'players': SyncFrequency.DAILY,
            'matches': SyncFrequency.HOURLY,
            'events': SyncFrequency.FREQUENT,
        },
        'event_batch': {
            'online': True,
            'lookback_days': 3,
            'lookahead_days': 1,
            'max_matches': 20,
            'batch_size': 5,
        },
    },
    'statsbomb': {
        'weekly_match_volume': 10,
        'notes': (
            'StatsBomb event delivery is usually post-match rather than live. Poll '
            'matches daily and ingest recent event files hourly with a wider 7-day '
            'lookback window.'
        ),
        'jobs': {
            'teams': SyncFrequency.DAILY,
            'players': SyncFrequency.DAILY,
            'matches': SyncFrequency.DAILY,
            'events': SyncFrequency.HOURLY,
        },
        'event_batch': {
            'online': True,
            'lookback_days': 7,
            'lookahead_days': 0,
            'max_matches': 20,
            'batch_size': 5,
        },
    },
}


def get_provider_sync_profile(provider: str) -> Dict[str, Any]:
    profile = DEFAULT_PROVIDER_SYNC_PROFILES.get(provider, DEFAULT_PROVIDER_SYNC_PROFILES['opta'])
    return {
        'weekly_match_volume': profile['weekly_match_volume'],
        'notes': profile['notes'],
        'jobs': dict(profile['jobs']),
        'event_batch': dict(profile['event_batch']),
    }


def list_provider_sync_profiles(providers: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
    selected = providers or list(DEFAULT_PROVIDER_SYNC_PROFILES.keys())
    profiles: Dict[str, Dict[str, Any]] = {}

    for provider in selected:
        profile = get_provider_sync_profile(provider)
        profiles[provider] = {
            'weekly_match_volume': profile['weekly_match_volume'],
            'notes': profile['notes'],
            'jobs': {name: frequency.value for name, frequency in profile['jobs'].items()},
            'event_batch': profile['event_batch'],
        }

    return profiles


class SyncJob:
    """Represents a scheduled sync job"""

    def __init__(
        self,
        name: str,
        syncer_class: type,
        provider: str,
        config: Dict[str, Any],
        frequency: SyncFrequency,
        enabled: bool = True
    ):
        self.name = name
        self.syncer_class = syncer_class
        self.provider = provider
        self.config = config
        self.frequency = frequency
        self.enabled = enabled
        self.last_run: Optional[datetime] = None
        self.last_result: Optional[SyncResult] = None
        self.run_count = 0


class SyncScheduler:
    """
    Orchestrates synchronization jobs

    Manages:
    - Periodic sync jobs for all providers
    - Job scheduling and execution
    - Sync result tracking
    - Error handling and retries

    Usage:
        scheduler = SyncScheduler()

        # Add sync jobs
        scheduler.add_job(
            name='opta_teams',
            syncer_class=TeamSyncer,
            provider='opta',
            config={'competition_id': '8'},
            frequency=SyncFrequency.DAILY
        )

        # Start scheduler
        await scheduler.start()
    """

    def __init__(self):
        """Initialize sync scheduler"""
        self.jobs: List[SyncJob] = []
        self.running = False

    def add_job(
        self,
        name: str,
        syncer_class: type,
        provider: str,
        config: Dict[str, Any],
        frequency: SyncFrequency,
        enabled: bool = True
    ):
        """
        Add a sync job

        Args:
            name: Job name (unique identifier)
            syncer_class: Syncer class (PlayerSyncer, TeamSyncer, etc.)
            provider: Provider name
            config: Provider configuration
            frequency: Sync frequency
            enabled: Whether job is enabled

        Example:
            scheduler.add_job(
                name='opta_premier_league_teams',
                syncer_class=TeamSyncer,
                provider='opta',
                config={'competition_id': '8'},
                frequency=SyncFrequency.DAILY
            )
        """
        job = SyncJob(
            name=name,
            syncer_class=syncer_class,
            provider=provider,
            config=config,
            frequency=frequency,
            enabled=enabled
        )

        self.jobs.append(job)
        print(f"[Scheduler] Added job: {name} ({frequency.value})")

    def remove_job(self, name: str):
        """Remove a job by name"""
        self.jobs = [j for j in self.jobs if j.name != name]
        print(f"[Scheduler] Removed job: {name}")

    def enable_job(self, name: str):
        """Enable a job"""
        for job in self.jobs:
            if job.name == name:
                job.enabled = True
                print(f"[Scheduler] Enabled job: {name}")
                break

    def disable_job(self, name: str):
        """Disable a job"""
        for job in self.jobs:
            if job.name == name:
                job.enabled = False
                print(f"[Scheduler] Disabled job: {name}")
                break

    async def run_job(self, job: SyncJob):
        """
        Execute a sync job

        Args:
            job: Job to execute

        Returns:
            SyncResult
        """
        if not job.enabled:
            print(f"[Scheduler] Skipping disabled job: {job.name}")
            return

        print(f"\n[Scheduler] Running job: {job.name}")
        start_time = datetime.now()

        try:
            # Create syncer instance
            syncer = job.syncer_class(provider=job.provider, config=job.config)

            # Run sync
            result = await syncer.sync(**job.config)

            # Update job stats
            job.last_run = datetime.now()
            job.last_result = result
            job.run_count += 1

            # Log result
            duration = (datetime.now() - start_time).total_seconds()
            print(f"[Scheduler] Job {job.name} completed in {duration:.2f}s")
            print(f"  - Fetched: {result.entities_fetched}")
            print(f"  - Created: {result.entities_created}")
            print(f"  - Updated: {result.entities_updated}")
            print(f"  - Merged: {result.entities_merged}")

            if result.errors:
                print(f"  - Errors: {len(result.errors)}")
                for error in result.errors[:3]:  # Show first 3 errors
                    print(f"    • {error}")

            return result

        except Exception as e:
            print(f"[Scheduler] Job {job.name} failed: {str(e)}")
            job.last_run = datetime.now()
            return None

    async def run_all_jobs(self):
        """Run all enabled jobs once"""
        print(f"\n[Scheduler] Running all jobs ({len(self.jobs)} total)")

        for job in self.jobs:
            if job.enabled:
                await self.run_job(job)

    async def start(self):
        """
        Start the scheduler (blocking)

        This will run jobs according to their frequency.
        """
        self.running = True
        print(f"\n[Scheduler] Starting scheduler with {len(self.jobs)} jobs")

        # Schedule jobs based on frequency
        for job in self.jobs:
            if not job.enabled:
                continue

            if job.frequency == SyncFrequency.REALTIME:
                schedule.every(1).minutes.do(lambda j=job: asyncio.create_task(self.run_job(j)))
            elif job.frequency == SyncFrequency.FREQUENT:
                schedule.every(15).minutes.do(lambda j=job: asyncio.create_task(self.run_job(j)))
            elif job.frequency == SyncFrequency.HOURLY:
                schedule.every(1).hours.do(lambda j=job: asyncio.create_task(self.run_job(j)))
            elif job.frequency == SyncFrequency.DAILY:
                schedule.every().day.at("02:00").do(lambda j=job: asyncio.create_task(self.run_job(j)))
            elif job.frequency == SyncFrequency.WEEKLY:
                schedule.every().monday.at("02:00").do(lambda j=job: asyncio.create_task(self.run_job(j)))
            # MANUAL jobs are not scheduled

        # Run scheduler loop
        print("[Scheduler] Scheduler running (Ctrl+C to stop)")

        while self.running:
            schedule.run_pending()
            await asyncio.sleep(1)

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        print("\n[Scheduler] Stopping scheduler")

    def get_status(self) -> Dict[str, Any]:
        """
        Get scheduler status

        Returns:
            Dict with scheduler status

        Example:
            status = scheduler.get_status()
            print(f"Total jobs: {status['total_jobs']}")
            print(f"Enabled jobs: {status['enabled_jobs']}")
        """
        enabled_jobs = [j for j in self.jobs if j.enabled]

        return {
            'total_jobs': len(self.jobs),
            'enabled_jobs': len(enabled_jobs),
            'running': self.running,
            'jobs': [
                {
                    'name': j.name,
                    'provider': j.provider,
                    'entity_type': j.syncer_class.__name__.replace('Syncer', '').lower(),
                    'frequency': j.frequency.value,
                    'enabled': j.enabled,
                    'last_run': j.last_run,
                    'run_count': j.run_count,
                    'last_result': j.last_result.to_dict() if j.last_result else None
                }
                for j in self.jobs
            ]
        }


def create_default_scheduler(providers: List[str] = ['opta'], competitions: List[str] = None) -> SyncScheduler:
    """
    Create a scheduler with default jobs

    Args:
        providers: List of provider names
        competitions: List of competition IDs (defaults to env OPTA_COMPETITION_ID or '115')

    Returns:
        Configured SyncScheduler
    """
    if competitions is None:
        competitions = [os.environ.get('OPTA_COMPETITION_ID', '115')]

    scheduler = SyncScheduler()

    for provider in providers:
        profile = get_provider_sync_profile(provider)

        for competition_id in competitions:
            config = {
                'competition_id': competition_id,
                'season_id': os.environ.get('OPTA_SEASON_ID', '2019'),
                'db_name': os.environ.get('MONGODB_DATABASE', 'scoutpro'),
                'db_host': os.environ.get('MONGODB_HOST', 'mongo'),
                'db_port': int(os.environ.get('MONGODB_PORT', '27017')),
                'online': provider in ('opta', 'statsbomb'),
            }

            # Teams
            scheduler.add_job(
                name=f"{provider}_{competition_id}_teams",
                syncer_class=TeamSyncer,
                provider=provider,
                config=config,
                frequency=profile['jobs']['teams']
            )

            # Players
            scheduler.add_job(
                name=f"{provider}_{competition_id}_players",
                syncer_class=PlayerSyncer,
                provider=provider,
                config=config,
                frequency=profile['jobs']['players']
            )

            # Matches
            scheduler.add_job(
                name=f"{provider}_{competition_id}_matches",
                syncer_class=MatchSyncer,
                provider=provider,
                config=config,
                frequency=profile['jobs']['matches']
            )

            # Events are pulled in batches from the provider server.
            scheduler.add_job(
                name=f"{provider}_{competition_id}_event_batches",
                syncer_class=EventBatchSyncer,
                provider=provider,
                config={
                    **config,
                    **profile['event_batch'],
                },
                frequency=profile['jobs']['events']
            )

    return scheduler
