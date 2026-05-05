#!/usr/bin/env python3
"""
Re-import F40 data with position standardization.

This script:
1. Clears existing F40 player records from MongoDB
2. Re-runs the F40 seeder with the new position_mapper utility
3. Standardizes positions to canonical codes (GK, DF, MF, FW)
4. Stores detailed positions (CB, ST, CM, etc.)
5. Preserves raw Opta position values for reference

Usage:
    # Re-import all F40 files with position standardization
    python3 re_import_f40_positions.py

    # With custom data directory
    python3 re_import_f40_positions.py --data-dir /data/opta/2025

    # Dry run (preview changes without modifying DB)
    python3 re_import_f40_positions.py --dry-run

    # Show position mapping statistics
    python3 re_import_f40_positions.py --stats-only
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timezone

# Add service paths
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "data-sync-service"))
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "shared"))

from pymongo import MongoClient

# Import the batch seeder
try:
    from sync.batch_seeder import OptaBatchSeeder
except ImportError:
    print("ERROR: Could not import OptaBatchSeeder. Make sure data-sync-service is in PYTHONPATH")
    sys.exit(1)

# Import position mapper
try:
    from utilities.position_mapper import PositionMapper
except ImportError:
    print("ERROR: Could not import PositionMapper. Make sure shared utilities are available")
    sys.exit(1)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class F40PositionMigration:
    """Handles F40 data re-import with position standardization."""

    def __init__(self, 
                 mongo_uri: str = "mongodb://root:scoutpro123@localhost:27017",
                 db_name: str = "scoutpro",
                 data_root: str = "/data/opta/2019",
                 dry_run: bool = False):
        """
        Initialize the migration.

        Args:
            mongo_uri: MongoDB connection URI
            db_name: Database name
            data_root: Root directory containing Opta F40 XML files
            dry_run: If True, preview changes without modifying DB
        """
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.data_root = data_root
        self.dry_run = dry_run
        self.mapper = PositionMapper()

        # Connect to MongoDB
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        
        logger.info(f"Connected to MongoDB: {mongo_uri}/{db_name}")

    def backup_players(self) -> int:
        """
        Create a backup of current players collection.
        
        Returns:
            Number of documents backed up
        """
        if self.dry_run:
            count = self.db.players.count_documents({})
            logger.info(f"[DRY RUN] Would backup {count} player documents")
            return count

        # Rename current collection
        try:
            self.db.players.rename("players_backup_" + datetime.now(timezone.utc).isoformat())
            count = self.db.players_backup.count_documents({})
            logger.info(f"Backed up {count} player documents to players_backup_*")
            return count
        except Exception as e:
            logger.warning(f"Could not backup players collection (may be first run): {e}")
            return 0

    def clear_f40_players(self) -> int:
        """
        Clear existing F40-sourced player records.
        
        Returns:
            Number of documents deleted
        """
        if self.dry_run:
            count = self.db.players.count_documents({})
            logger.info(f"[DRY RUN] Would clear {count} player documents")
            return count

        # Delete all players from F40
        result = self.db.players.delete_many({})
        logger.info(f"Cleared {result.deleted_count} player documents from collection")
        return result.deleted_count

    def analyze_position_data(self) -> Dict[str, int]:
        """
        Analyze current position values in the collection.
        
        Returns:
            Dictionary mapping position codes to counts
        """
        position_distribution = {}
        
        # Get all distinct position values
        positions = self.db.players.distinct("raw_position")
        
        for pos in positions:
            if pos:  # Skip None/empty
                standardized = self.mapper.standardize(pos)
                code = standardized.get("code") or "UNKNOWN"
                position_distribution[f"{pos} → {code}"] = self.db.players.count_documents({"raw_position": pos})
        
        return position_distribution

    def run_import(self) -> bool:
        """
        Run the OptaBatchSeeder to re-import F40 data.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            seeder = OptaBatchSeeder(
                mongo_uri=self.mongo_uri,
                db_name=self.db_name,
                data_root=self.data_root
            )
            
            logger.info(f"Starting F40 import from {self.data_root}...")
            
            if self.dry_run:
                logger.info("[DRY RUN] Would run OptaBatchSeeder.seed_f40()")
                return True
            
            # Run F40 seeding (this will use the updated batch_seeder with position mapper)
            seeder.seed_f40()
            
            logger.info("F40 import completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during F40 import: {e}", exc_info=True)
            return False

    def verify_positions(self) -> Dict[str, int]:
        """
        Verify that positions have been standardized.
        
        Returns:
            Statistics on position standardization
        """
        total = self.db.players.count_documents({})
        with_code = self.db.players.count_documents({"position": {"$ne": None}})
        with_detailed = self.db.players.count_documents({"detailed_position": {"$ne": None}})
        with_raw = self.db.players.count_documents({"raw_position": {"$ne": None}})
        
        stats = {
            "total_players": total,
            "with_position_code": with_code,
            "with_detailed_position": with_detailed,
            "with_raw_position": with_raw,
        }
        
        # Sample position distributions
        position_codes = self.db.players.aggregate([
            {"$match": {"position": {"$ne": None}}},
            {"$group": {"_id": "$position", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        
        code_dist = {doc["_id"]: doc["count"] for doc in position_codes}
        stats["position_code_distribution"] = code_dist
        
        return stats

    def get_position_examples(self, limit: int = 5) -> List[Dict]:
        """
        Get example documents showing position standardization.
        
        Args:
            limit: Number of examples per position code
            
        Returns:
            List of example documents with position info
        """
        examples = []
        
        for code in ["GK", "DF", "MF", "FW"]:
            docs = self.db.players.find(
                {"position": code},
                {"name": 1, "position": 1, "detailed_position": 1, "raw_position": 1}
            ).limit(limit)
            
            for doc in docs:
                examples.append({
                    "name": doc.get("name"),
                    "raw_position": doc.get("raw_position"),
                    "position_code": doc.get("position"),
                    "detailed_position": doc.get("detailed_position"),
                })
        
        return examples

    def run(self) -> bool:
        """
        Execute the full migration pipeline.
        
        Returns:
            True if successful
        """
        try:
            logger.info("=" * 70)
            logger.info("F40 Position Standardization Migration")
            logger.info("=" * 70)
            
            # Step 1: Backup existing data
            logger.info("\n[1/4] Backing up current player data...")
            backup_count = self.backup_players()
            
            # Step 2: Clear old data
            logger.info("\n[2/4] Clearing old F40 player records...")
            deleted_count = self.clear_f40_players()
            
            # Step 3: Re-import with position standardization
            logger.info("\n[3/4] Re-importing F40 data with position standardization...")
            success = self.run_import()
            
            if not success and not self.dry_run:
                logger.error("Import failed!")
                return False
            
            # Step 4: Verify results
            logger.info("\n[4/4] Verifying position standardization...")
            stats = self.verify_positions()
            
            logger.info("\n" + "=" * 70)
            logger.info("Migration Results")
            logger.info("=" * 70)
            logger.info(f"Total players: {stats['total_players']}")
            logger.info(f"With position code: {stats['with_position_code']}")
            logger.info(f"With detailed position: {stats['with_detailed_position']}")
            logger.info(f"With raw position: {stats['with_raw_position']}")
            logger.info(f"\nPosition code distribution:")
            for code, count in stats.get('position_code_distribution', {}).items():
                pct = (count / stats['total_players'] * 100) if stats['total_players'] > 0 else 0
                logger.info(f"  {code}: {count} ({pct:.1f}%)")
            
            # Show examples
            logger.info(f"\nPosition standardization examples:")
            examples = self.get_position_examples(limit=2)
            for example in examples:
                logger.info(f"  {example['name']}: {example['raw_position']} → {example['position_code']} ({example['detailed_position']})")
            
            logger.info("\n" + "=" * 70)
            if self.dry_run:
                logger.info("DRY RUN COMPLETED - No changes made to database")
            else:
                logger.info("Migration completed successfully!")
            logger.info("=" * 70)
            
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Re-import F40 data with position standardization"
    )
    parser.add_argument(
        "--mongo-uri",
        default="mongodb://root:scoutpro123@localhost:27017",
        help="MongoDB connection URI"
    )
    parser.add_argument(
        "--db-name",
        default="scoutpro",
        help="Database name"
    )
    parser.add_argument(
        "--data-dir",
        default="/data/opta/2019",
        help="Root directory containing Opta F40 XML files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying database"
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show position mapping statistics"
    )
    
    args = parser.parse_args()
    
    # Create migration instance
    migration = F40PositionMigration(
        mongo_uri=args.mongo_uri,
        db_name=args.db_name,
        data_root=args.data_dir,
        dry_run=args.dry_run or args.stats_only
    )
    
    if args.stats_only:
        logger.info("Position mapping statistics:")
        stats = migration.analyze_position_data()
        for mapping, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {mapping}: {count}")
        return 0
    
    # Run full migration
    success = migration.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
