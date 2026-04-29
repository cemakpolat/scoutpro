"""
Sync Scheduler

Orchestrates periodic synchronization jobs for all providers and entities.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import schedule
import time

from sync.player_syncer import PlayerSyncer
from sync.team_syncer import TeamSyncer
from sync.match_syncer import MatchSyncer
from sync.event_syncer import EventSyncer
from sync.base_syncer import SyncResult


class SyncFrequency(Enum):
    """Sync frequency options"""
    REALTIME = "realtime"  # Every minute (for live matches)
    FREQUENT = "frequent"  # Every 15 minutes
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MANUAL = "manual"


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


def create_default_scheduler(providers: List[str] = ['opta'], competitions: List[str] = ['8']) -> SyncScheduler:
    """
    Create a scheduler with default jobs

    Args:
        providers: List of provider names
        competitions: List of competition IDs

    Returns:
        Configured SyncScheduler

    Example:
        scheduler = create_default_scheduler(
            providers=['opta', 'statsbomb'],
            competitions=['8', '55']  # Premier League, Champions League
        )
        await scheduler.start()
    """
    scheduler = SyncScheduler()

    for provider in providers:
        for competition_id in competitions:
            config = {
                'competition_id': competition_id,
                'season_id': '2023',
                'db_name': 'statsfabrik',
                'db_host': 'localhost',
                'db_port': 27017
            }

            # Teams (daily sync)
            scheduler.add_job(
                name=f"{provider}_{competition_id}_teams",
                syncer_class=TeamSyncer,
                provider=provider,
                config=config,
                frequency=SyncFrequency.DAILY
            )

            # Players (daily sync)
            scheduler.add_job(
                name=f"{provider}_{competition_id}_players",
                syncer_class=PlayerSyncer,
                provider=provider,
                config=config,
                frequency=SyncFrequency.DAILY
            )

            # Matches (daily sync)
            scheduler.add_job(
                name=f"{provider}_{competition_id}_matches",
                syncer_class=MatchSyncer,
                provider=provider,
                config=config,
                frequency=SyncFrequency.DAILY
            )

            # Events are synced per match, not as a bulk job
            # They would be triggered by match sync or external events

    return scheduler
