"""
Complementary Event Data Strategy
===================================

Problem: Multiple providers may cover the same match with different:
- Event models (Opta typeID vs StatsBomb type_name)
- Temporal resolution (minute/second precision differs)
- Event granularity (what counts as an event varies)
- Data completeness (tactical detail levels differ)

Solution: Provider Prioritization + Intelligent Merging

STRATEGY 1: Provider Hierarchy (RECOMMENDED FOR MOST CASES)
-----------------------------------------------------------
Primary (OPTA):
  - Widely used in professional football analytics
  - Detailed match event data (F24 format)
  - Standard timing/location encoding
  - Used for official league statistics

Complementary (StatsBomb):
  - Enhanced tactical detail (possession, pressure zones)
  - Better coverage of modern matches
  - Additional event types (ball recovery, pressure)
  - Used when Opta unavailable or for enrichment

When BOTH providers cover same match:
  1. Use Opta as baseline statistics (authoritative)
  2. Add StatsBomb metrics Opta doesn't capture (e.g., pressure events)
  3. Validate consistency (event counts within 10-15% tolerance)
  4. Flag high discrepancies for manual review

STRATEGY 2: Match-Level Provider Assignment
---------------------------------------------
Each match gets ONE primary provider based on:
  1. Data completeness (event count coverage)
  2. Temporal alignment (minute references match)
  3. Provider availability in region
  4. Historical preference (Opta for European leagues, etc.)

```
Match 1080974:
  Primary: OPTA (2,145 events, full 90+ min coverage)
  Complementary: StatsBomb (n/a)
  
Match 3946949:
  Primary: StatsBomb (847 events)
  Complementary: OPTA (not available)
```

STRATEGY 3: Field-Level Conflict Resolution
---------------------------------------------
For overlapping player metrics, define merge logic:

Field                    Rule
---------                ----
passes_total             Prefer primary (more reliable)
passes_successful        Prefer primary
pass_accuracy            Computed from primary
tackles                  Combine if both exist (complementary)
interceptions            Combine if both exist
aerials_won              Prefer primary (better Opta encoding)
duel_events              Add to primary (StatsBomb specialty)
pressure_events          Use complementary only (Opta doesn't track)
ball_recovery            Use complementary only
possession_%             Prefer primary (calculated from passes)

KEY PRINCIPLE: Never double-count the same event
  ✓ If both providers report "Player 51948 passed to Player 51521 at minute 25"
    → Use only Opta version
  ✓ If Opta has "player pass" and SB has "pressure" at same moment
    → Use both (different event types)
  ✗ Never sum counts across providers for same event type
"""

from pymongo import MongoClient
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class ComplementaryEventStrategy:
    """
    Manages multi-provider event data with intelligent deduplication.
    """
    
    # Per-match provider priority (Opta > StatsBomb for overlaps)
    PROVIDER_HIERARCHY = ['opta', 'statsbomb', 'instat', 'wyscout']
    
    # Events that are exclusive to certain providers
    PROVIDER_EXCLUSIVE_EVENTS = {
        'statsbomb': ['pressure', 'ball recovery', 'ball receipt*', 'carries', 'miscontrol'],
        'opta': [],  # Opta is baseline; we accept all its events
    }
    
    # Merge rules: (field_name, merge_strategy)
    FIELD_MERGE_RULES = {
        # Use primary provider only
        'passes_total': 'use_primary',
        'passes_successful': 'use_primary',
        'pass_accuracy': 'use_primary',  # Derived field
        'tackles_total': 'use_primary',
        'shots_total': 'use_primary',
        'goals': 'use_primary',
        'aerial_duels_total': 'use_primary',
        'aerial_duels_won': 'use_primary',
        
        # Combine complementary data
        'interceptions': 'combine',
        'clearances': 'combine',
        'ball_recoveries': 'combine',
        'fouls_committed': 'combine',
        'duels_total': 'combine',  # StatsBomb specialty
        'duels_won': 'combine',
        
        # Provider-specific only
        'pressure_events': 'use_complementary_only',
    }
    
    def __init__(self, mongo_uri=None):
        if mongo_uri is None:
            mongo_uri = "mongodb://root:scoutpro123@scoutpro-mongo:27017/scoutpro?authSource=admin"
        
        self.client = MongoClient(mongo_uri)
        self.db = self.client['scoutpro']
        logger.info("✓ Connected to MongoDB")
    
    def detect_match_overlaps(self):
        """Find matches covered by multiple providers"""
        pipeline = [
            {
                '$group': {
                    '_id': '$matchID',
                    'providers': {'$addToSet': '$provider'},
                    'provider_count': {'$sum': 1}
                }
            },
            {
                '$addFields': {
                    'num_providers': {'$size': '$providers'}
                }
            },
            {
                '$match': {'num_providers': {'$gt': 1}}
            },
            {'$sort': {'provider_count': -1}}
        ]
        
        overlaps = list(self.db.match_events.aggregate(pipeline))
        
        logger.info(f"\n{'='*60}")
        logger.info(f"MATCH PROVIDER OVERLAP ANALYSIS")
        logger.info(f"{'='*60}")
        logger.info(f"Matches with multiple providers: {len(overlaps)}")
        
        for overlap in overlaps:
            match_id = overlap['_id']
            providers = overlap['providers']
            event_count = overlap['provider_count']
            
            logger.info(f"\nMatch {match_id}: {providers} ({event_count} events)")
            
            # Get event breakdown per provider
            breakdown = list(self.db.match_events.aggregate([
                {'$match': {'matchID': match_id}},
                {
                    '$group': {
                        '_id': '$provider',
                        'count': {'$sum': 1},
                        'minutes': {'$max': '$minute'}
                    }
                }
            ]))
            
            for item in breakdown:
                logger.info(f"  {item['_id']:12} | {item['count']:5} events | max_minute: {item['minutes']}")
        
        return overlaps
    
    def assign_primary_provider(self, match_id):
        """
        Determine primary provider for a match based on:
        1. Event count (higher = more complete)
        2. Temporal coverage (more minutes = better)
        3. Provider hierarchy
        """
        breakdown = list(self.db.match_events.aggregate([
            {'$match': {'matchID': match_id}},
            {
                '$group': {
                    '_id': '$provider',
                    'count': {'$sum': 1},
                    'max_minute': {'$max': '$minute'},
                    'unique_players': {'$addToSet': '$player_id'}
                }
            },
            {
                '$addFields': {
                    'player_count': {'$size': '$unique_players'}
                }
            }
        ]))
        
        if not breakdown:
            return None
        
        # Score each provider
        scores = {}
        for item in breakdown:
            provider = item['_id']
            event_count = item['count']
            temporal_coverage = item['max_minute']
            player_diversity = item['player_count']
            
            # Scoring: events (40%) + temporal (35%) + players (25%)
            score = (event_count * 0.4) + (temporal_coverage * 0.35) + (player_diversity * 0.25)
            scores[provider] = {
                'score': score,
                'events': event_count,
                'max_minute': temporal_coverage,
                'players': player_diversity
            }
        
        # Apply hierarchy preference (Opta > StatsBomb > others)
        primary = max(scores.keys(), key=lambda p: (
            self.PROVIDER_HIERARCHY.index(p) if p in self.PROVIDER_HIERARCHY else 999,  # Lower index = higher priority
            scores[p]['score']  # Then by score
        ), reverse=True)
        
        return primary, scores
    
    def merge_player_statistics(self, player_id, match_id, opta_stats, statsbomb_stats):
        """
        Intelligently merge statistics from multiple providers.
        Opta is primary, StatsBomb is complementary.
        """
        merged = {}
        
        # Start with Opta (primary)
        if opta_stats:
            merged.update(opta_stats.get('metrics', {}))
            merged['primary_provider'] = 'opta'
        elif statsbomb_stats:
            merged.update(statsbomb_stats.get('metrics', {}))
            merged['primary_provider'] = 'statsbomb'
        else:
            return None
        
        # Add complementary data from other provider
        complementary = statsbomb_stats if opta_stats else None
        if complementary:
            for field, value in complementary.get('metrics', {}).items():
                merge_rule = self.FIELD_MERGE_RULES.get(field, 'use_primary')
                
                if merge_rule == 'combine':
                    # Add complementary data
                    current = merged.get(field, 0)
                    merged[field] = current + value
                    merged[f'{field}_sources'] = ['opta', 'statsbomb']
                elif merge_rule == 'use_complementary_only':
                    # Use only if not in primary
                    if field not in merged or merged[field] == 0:
                        merged[field] = value
                        merged[f'{field}_source'] = 'statsbomb'
                # else: use_primary, skip complementary
        
        merged['match_id'] = match_id
        merged['player_id'] = player_id
        merged['data_strategy'] = 'primary_with_complementary'
        
        return merged
    
    def reconcile_match_events(self, match_id, primary_provider):
        """
        Build unified event stream for a match:
        - Include all primary provider events
        - Add complementary provider events that don't conflict
        """
        # Get all events for this match
        all_events = list(self.db.match_events.find(
            {'matchID': match_id},
            {'provider': 1, 'type_name': 1, 'player_id': 1, 'minute': 1, 'second': 1}
        ).sort([('minute', 1), ('second', 1)]))
        
        reconciled = []
        primary_events = set()
        
        # First pass: include all primary provider events
        for event in all_events:
            if event['provider'] == primary_provider:
                event_key = (event['player_id'], event['minute'], event.get('second', 0), event['type_name'])
                primary_events.add(event_key)
                reconciled.append({**event, 'is_primary': True})
        
        # Second pass: add complementary events that don't duplicate
        for event in all_events:
            if event['provider'] != primary_provider:
                event_key = (event['player_id'], event['minute'], event.get('second', 0), event['type_name'])
                
                # Check if this is an exclusive complementary event
                is_exclusive = event['type_name'] in self.PROVIDER_EXCLUSIVE_EVENTS.get(event['provider'], [])
                
                # Include if: exclusive event OR not already in primary
                if is_exclusive or event_key not in primary_events:
                    reconciled.append({**event, 'is_primary': False, 'complementary_source': event['provider']})
        
        return reconciled
    
    def validate_provider_consistency(self, match_id):
        """
        Compare event counts/timing between providers.
        Flag high discrepancies for manual review.
        """
        breakdown = list(self.db.match_events.aggregate([
            {'$match': {'matchID': match_id}},
            {
                '$group': {
                    '_id': '$provider',
                    'event_count': {'$sum': 1},
                    'max_minute': {'$max': '$minute'}
                }
            }
        ]))
        
        if len(breakdown) < 2:
            return None  # No overlap to validate
        
        # Calculate discrepancy
        counts = {item['_id']: item['event_count'] for item in breakdown}
        max_count = max(counts.values())
        min_count = min(counts.values())
        discrepancy_pct = ((max_count - min_count) / max_count) * 100
        
        validation = {
            'match_id': match_id,
            'discrepancy_pct': round(discrepancy_pct, 1),
            'counts': counts,
            'flag_for_review': discrepancy_pct > 20  # >20% difference is suspicious
        }
        
        return validation
    
    def generate_provider_strategy_report(self):
        """Generate comprehensive report on provider strategy"""
        logger.info(f"\n{'='*60}")
        logger.info("PROVIDER STRATEGY REPORT")
        logger.info(f"{'='*60}")
        
        # Overall coverage
        providers = list(self.db.match_events.distinct('provider'))
        logger.info(f"\nProviders in system: {providers}")
        
        for provider in providers:
            count = self.db.match_events.count_documents({'provider': provider})
            matches = len(self.db.match_events.distinct('matchID', {'provider': provider}))
            players = len(self.db.match_events.distinct('player_id', {'provider': provider}))
            logger.info(f"  {provider:12} | {count:6} events | {matches:4} matches | {players:4} players")
        
        # Overlaps
        overlaps = self.detect_match_overlaps()
        
        # Recommendations
        logger.info(f"\n{'─'*60}")
        logger.info("RECOMMENDATIONS:")
        logger.info(f"{'─'*60}")
        logger.info("1. PRIMARY DATA SOURCE: OPTA")
        logger.info("   - Use for baseline player/match statistics")
        logger.info("   - More established in professional football")
        logger.info("")
        logger.info("2. COMPLEMENTARY DATA SOURCE: StatsBomb")
        logger.info("   - Use for tactical enrichment (pressure, ball recovery)")
        logger.info("   - Gap-fill for matches without Opta coverage")
        logger.info("   - Validate consistency against Opta")
        logger.info("")
        logger.info("3. MERGE STRATEGY FOR OVERLAPS:")
        logger.info("   - Never double-count event metrics")
        logger.info("   - Prefer Opta for primary stats (passes, tackles, etc.)")
        logger.info("   - Add StatsBomb exclusive event types (pressure)")
        logger.info("   - Flag discrepancies >20% for manual review")
    
    def close(self):
        self.client.close()
        logger.info("\nMongoDB connection closed")


if __name__ == '__main__':
    strategy = ComplementaryEventStrategy()
    
    try:
        # Analyze overlaps
        strategy.generate_provider_strategy_report()
        
        # Validate consistency where overlaps exist
        overlaps = strategy.detect_match_overlaps()
        
        if overlaps:
            logger.info(f"\n{'='*60}")
            logger.info("CONSISTENCY VALIDATION")
            logger.info(f"{'='*60}")
            
            for overlap in overlaps[:5]:  # Check first 5 overlaps
                match_id = overlap['_id']
                primary, scores = strategy.assign_primary_provider(match_id)
                validation = strategy.validate_provider_consistency(match_id)
                
                logger.info(f"\nMatch {match_id}:")
                logger.info(f"  Primary provider: {primary}")
                for prov, data in scores.items():
                    logger.info(f"    {prov}: score={data['score']:.0f} | events={data['events']} | max_min={data['max_minute']}")
                
                if validation:
                    logger.info(f"  Discrepancy: {validation['discrepancy_pct']:.1f}% (Flag: {validation['flag_for_review']})")
    
    finally:
        strategy.close()
