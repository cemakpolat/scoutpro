"""
Data Sync Service

Main entry point for the multi-provider data synchronization service.

This service orchestrates:
- Periodic data synchronization from multiple providers (Opta, StatsBomb, etc.)
- Entity resolution and merging
- Conflict detection and resolution
- Quality enrichment
- Canonical data storage

Usage:
    # Run with default configuration
    python main.py

    # Run specific sync job
    python main.py --job opta_teams

    # Run once and exit
    python main.py --once

    # Run in daemon mode
    python main.py --daemon
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from sync import (
    SyncScheduler,
    SyncFrequency,
    create_default_scheduler,
    PlayerSyncer,
    TeamSyncer,
    MatchSyncer,
    EventSyncer
)


async def run_once(scheduler: SyncScheduler):
    """
    Run all sync jobs once and exit

    Args:
        scheduler: Configured sync scheduler
    """
    print("\n=== Data Sync Service (Run Once Mode) ===\n")

    await scheduler.run_all_jobs()

    print("\n=== Sync completed ===")
    status = scheduler.get_status()

    print(f"\nSummary:")
    print(f"  Total jobs: {status['total_jobs']}")
    print(f"  Enabled jobs: {status['enabled_jobs']}")

    # Print job results
    for job in status['jobs']:
        if job['last_result']:
            result = job['last_result']
            print(f"\n  {job['name']}:")
            print(f"    Status: {result['status']}")
            print(f"    Fetched: {result['entities_fetched']}")
            print(f"    Created: {result['entities_created']}")
            print(f"    Updated: {result['entities_updated']}")
            if result['errors']:
                print(f"    Errors: {len(result['errors'])}")


async def run_daemon(scheduler: SyncScheduler):
    """
    Run scheduler in daemon mode (continuous)

    Args:
        scheduler: Configured sync scheduler
    """
    print("\n=== Data Sync Service (Daemon Mode) ===\n")

    try:
        await scheduler.start()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        scheduler.stop()


async def run_single_job(job_name: str, config: dict):
    """
    Run a single sync job

    Args:
        job_name: Job name (e.g., 'opta_teams', 'statsbomb_matches')
        config: Job configuration
    """
    print(f"\n=== Running single job: {job_name} ===\n")

    # Parse job name
    parts = job_name.split('_')
    if len(parts) < 2:
        print(f"Error: Invalid job name '{job_name}'")
        print("Format: <provider>_<entity_type> (e.g., opta_teams)")
        return

    provider = parts[0]
    entity_type = parts[1]

    # Create syncer based on entity type
    syncer_map = {
        'players': PlayerSyncer,
        'teams': TeamSyncer,
        'matches': MatchSyncer,
        'events': EventSyncer
    }

    syncer_class = syncer_map.get(entity_type)

    if not syncer_class:
        print(f"Error: Unknown entity type '{entity_type}'")
        print(f"Available: {list(syncer_map.keys())}")
        return

    # Create and run syncer
    syncer = syncer_class(provider=provider, config=config)
    result = await syncer.sync(**config)

    # Print result
    print(f"\n=== Sync completed ===")
    print(f"  Status: {result.status.value}")
    print(f"  Fetched: {result.entities_fetched}")
    print(f"  Created: {result.entities_created}")
    print(f"  Updated: {result.entities_updated}")
    print(f"  Merged: {result.entities_merged}")
    print(f"  Duration: {result.duration_seconds:.2f}s")

    if result.errors:
        print(f"  Errors: {len(result.errors)}")
        for error in result.errors[:5]:  # Show first 5 errors
            print(f"    • {error}")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Data Sync Service')

    parser.add_argument(
        '--once',
        action='store_true',
        help='Run all jobs once and exit'
    )

    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run in daemon mode (continuous)'
    )

    parser.add_argument(
        '--job',
        type=str,
        help='Run a single job (format: provider_entity, e.g., opta_teams)'
    )

    parser.add_argument(
        '--provider',
        type=str,
        default='opta',
        help='Provider name (default: opta)'
    )

    parser.add_argument(
        '--competition',
        type=str,
        default='8',
        help='Competition ID (default: 8 for Premier League)'
    )

    parser.add_argument(
        '--season',
        type=str,
        default='2023',
        help='Season ID (default: 2023)'
    )

    parser.add_argument(
        '--match',
        type=str,
        help='Match ID (for event sync)'
    )

    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_args()

    db_host = os.getenv('MONGODB_HOST', 'mongo')
    db_port = int(os.getenv('MONGODB_PORT', '27017'))
    db_name = os.getenv('MONGODB_DATABASE', 'scoutpro')

    # Build config
    config = {
        'competition_id': args.competition,
        'season_id': args.season,
        'db_name': db_name,
        'db_host': db_host,
        'db_port': db_port
    }

    if args.match:
        config['match_id'] = args.match

    # Single job mode
    if args.job:
        await run_single_job(args.job, config)
        return

    # Create scheduler
    providers = [args.provider]
    competitions = [args.competition]

    scheduler = create_default_scheduler(
        providers=providers,
        competitions=competitions
    )

    # Run once mode
    if args.once:
        await run_once(scheduler)
        return

    # Daemon mode (default)
    await run_daemon(scheduler)


if __name__ == '__main__':
    asyncio.run(main())
