# Multi-Provider Event Data Strategy

## Problem Statement

Different football event data providers have fundamentally different data models:

| Aspect | Opta | StatsBomb | Impact |
|--------|------|-----------|--------|
| **Event Model** | Numeric EventID (1=Pass, 7=Tackle, 44=Aerial) | String type_name (pass, tackle, aerial lost) | Different classification systems |
| **Granularity** | Minute/Second precision | Millisecond precision | Timing may not align |
| **Event Coverage** | Standard FIFA event types | Additional tactical events (pressure, ball recovery, miscontrol) | Different completeness |
| **Data Structure** | Qualifiers dict (field 140=x, 141=y) | Direct location fields (location, end_location) | Schema differences |
| **Match Coverage** | Historical league data | Modern matches, supplementary coverage | Partial overlaps possible |

## Current System State

```
Scout Pro Event Coverage (as of April 30, 2026)

Opta:
  ├─ 15,113 events
  ├─ 10 matches
  ├─ 245 players
  └─ Primary data source (authoritative)

StatsBomb:
  ├─ 3,122 events
  ├─ 1 match (3946949 - Samsunspor vs Besiktas)
  ├─ 33 players
  └─ Complementary data source

Provider Overlap:
  └─ 0 matches covered by both (clean separation currently)
```

## Recommended Strategy: Primary + Complementary

### 1. Provider Hierarchy

```
┌─────────────────────────────────────────────────┐
│ PRIMARY DATA SOURCE: OPTA                       │
├─────────────────────────────────────────────────┤
│ ✓ Baseline player statistics                    │
│ ✓ Official match events                         │
│ ✓ Established professional standard             │
│ ✓ Better temporal consistency                   │
│ ✓ Source of truth for:                          │
│   - Pass counts and accuracy                    │
│   - Tackle success rates                        │
│   - Aerial duel outcomes                        │
│   - Shot efficiency                             │
└─────────────────────────────────────────────────┘
                        ↑
        Use as baseline, never replace

┌─────────────────────────────────────────────────┐
│ COMPLEMENTARY DATA SOURCE: StatsBomb            │
├─────────────────────────────────────────────────┤
│ ✓ Tactical enrichment (pressure zones)          │
│ ✓ Advanced event types (ball recovery)          │
│ ✓ Gap-fill for Opta-unavailable matches        │
│ ✓ Validation/cross-check against Opta          │
│ ✗ Never used as primary for same match         │
│ Use only for:                                    │
│   - Pressure event counts                       │
│   - Ball recovery metrics                       │
│   - Carry/dribble details                       │
│   - Validation of Opta consistency              │
└─────────────────────────────────────────────────┘
```

### 2. Match-Level Assignment

Each match is assigned ONE primary provider based on:

```python
MATCH ASSIGNMENT LOGIC:

For each match:
  1. Check if covered by multiple providers
  2. If single provider → Use that provider
  3. If multiple providers:
     a. Score by: event_count (40%) + temporal_coverage (35%) + player_diversity (25%)
     b. Apply hierarchy: Opta > StatsBomb > Instat > Wyscout
     c. Primary = highest scoring provider from hierarchy
  4. Secondary provider(s) = complementary role only
```

**Example 1 (Current State)**:
```
Match 1080974: Primary = OPTA
  - Opta: 2,145 events, 90 min coverage ✓
  - StatsBomb: N/A
  → Use all Opta events

Match 3946949: Primary = StatsBomb
  - Opta: N/A
  - StatsBomb: 847 events, full coverage ✓
  → Use all StatsBomb events (gap-fill)
```

**Example 2 (Hypothetical Overlap)**:
```
Match 5000000: Dual Coverage
  - Opta: 1,950 events, 95 min coverage, 22 players
    Score: (1950 × 0.4) + (95 × 0.35) + (22 × 0.25) = 1,090
  - StatsBomb: 847 events, 95 min coverage, 22 players
    Score: (847 × 0.4) + (95 × 0.35) + (22 × 0.25) = 592
  → Primary = OPTA (higher score + hierarchy)
  → Secondary = StatsBomb (complementary role)
```

### 3. Field-Level Merge Rules

| Metric | Rule | Reason |
|--------|------|--------|
| **passes_total** | Use primary | Different counting methods across providers |
| **passes_successful** | Use primary | Outcome encoding differs |
| **pass_accuracy** | Use primary | Computed from primary provider data |
| **tackles_total** | Use primary | Opta has authoritative tackle classification |
| **tackles_successful** | Use primary | Outcome definitions vary |
| **shots_total** | Use primary | Shot identification differs |
| **goals** | Use primary | Primary provider has official goal records |
| **aerial_duels** | Use primary | Opta typeID=44 is standard |
| **interceptions** | Combine | Both providers track; safe to add |
| **clearances** | Combine | Complementary tracking doesn't conflict |
| **ball_recoveries** | Combine | Mostly StatsBomb; add to primary |
| **pressure_events** | Use complementary only | Only StatsBomb tracks pressure |
| **carry_events** | Use complementary only | StatsBomb specialty; Opta doesn't track |
| **miscontrol** | Use complementary only | StatsBomb exclusive event |

**Key Principle: NEVER DOUBLE-COUNT**
```python
❌ WRONG:
  total_passes = opta_passes_total + statsbomb_passes_total  # Double-counts!

✓ CORRECT:
  total_passes = opta_passes_total  # Opta is primary
  pressure_events = statsbomb_pressure_events  # StatsBomb exclusive
  total_defensive_actions = tackles + interceptions + clearances + ball_recoveries  # Combine where safe
```

### 4. Conflict Detection & Resolution

When providers report different values for the same metric:

```python
CONFLICT DETECTION:
  If abs(opta_value - statsbomb_value) / max(opta_value, statsbomb_value) > 0.20:
    → Flag for manual review (>20% discrepancy)
    → Log detailed comparison
    → Use primary value
    → Annotate with "data_quality_flag"

Example:
  Opta: Pass accuracy = 75%
  StatsBomb: Pass accuracy = 62%
  Discrepancy: 17% → OK, use Opta
  
  Opta: Tackles = 8
  StatsBomb: Tackles = 2
  Discrepancy: 75% → FLAG FOR REVIEW
```

## Implementation in Unified Event Evaluator

### Current Code

The `unified_event_evaluator.py` already implements:
- ✅ Provider-agnostic event routing
- ✅ Consistent metric computation for both providers
- ✅ Career-level aggregation across providers

### Enhancement Needed

Next iteration should add:

```python
class ComplementaryEventEvaluator(UnifiedEventEvaluator):
    """
    Extends unified evaluator with:
    - Provider conflict detection
    - Intelligent field merging
    - Match-level primary assignment
    - Data quality flagging
    """
    
    def assign_primary_provider(self, match_id):
        """Score and select primary provider for a match"""
        pass
    
    def merge_player_statistics(self, player_id, match_id, opta_stats, statsbomb_stats):
        """Intelligently merge stats using field-level rules"""
        pass
    
    def validate_provider_consistency(self, match_id):
        """Detect and flag high discrepancies"""
        pass
```

## API Response Format

When returning statistics, include provider metadata:

```json
{
  "player_id": 51948,
  "match_id": 1080974,
  "statistics": {
    "passing": {
      "total": 28,
      "successful": 21,
      "accuracy": 75.0,
      "source": "opta"
    },
    "defending": {
      "tackles": 3,
      "source": "opta"
    },
    "pressure": {
      "pressure_events": 12,
      "source": "statsbomb",
      "note": "complementary data"
    }
  },
  "data_quality": {
    "primary_provider": "opta",
    "providers_used": ["opta"],
    "flags": []
  }
}
```

## Scalability to Additional Providers

This framework is extensible. To add Instat, Wyscout, or other providers:

```python
PROVIDER_HIERARCHY = [
    'opta',        # Primary
    'statsbomb',   # Complementary
    'instat',      # Tertiary (when added)
    'wyscout',     # Quaternary (when added)
]

PROVIDER_EXCLUSIVE_EVENTS = {
    'statsbomb': ['pressure', 'ball recovery', 'carries', 'miscontrol'],
    'instat': ['xg_model_event', 'defensive_action_quality'],
    'wyscout': ['deep_event_data', 'video_timeline'],
}
```

## Summary: When to Use Each Provider

### Use OPTA for:
- ✅ Official match statistics
- ✅ Player performance ratings
- ✅ Team tactical reports
- ✅ League-wide comparisons
- ✅ Historical trend analysis

### Use StatsBomb for:
- ✅ Tactical detail (pressure, ball recovery)
- ✅ Matches without Opta coverage
- ✅ Modern match analysis (post-2018)
- ✅ Advanced coaching insights
- ✅ Cross-validation of Opta data

### Use BOTH for:
- ✅ Comprehensive event streams (all event types)
- ✅ Data quality validation
- ✅ Player consistency checking
- ✅ Research requiring multiple perspectives

### AVOID:
- ❌ Summing counts across providers for same metric
- ❌ Treating StatsBomb as primary for overlap matches
- ❌ Ignoring provider differences in metric definitions
- ❌ Reporting provider-specific events as universal facts
