# Event Enrichment Strategy
## Expanding Statistics-Service with Advanced Analytics

**Created:** April 2026  
**Based on:** Legacy Feed API patterns + Modern microservice architecture  
**Purpose:** Define enrichment functions that transform raw Opta events into actionable insights

---

## Current State vs. Potential

### Currently Implemented
- Basic event counts (total_attempts, total_shots, etc.)
- Pass direction categorization (forward, backward, lateral)
- Simple aggregations without context

### Available in Database
- **8,967 pass events** with qualifiers and coordinates
- **212 shot events** with location, foot type, goal status
- **612 duel events** (ground and aerial)
- **325 tackle events** with success tracking
- **486 foul events** with context
- **46 card events** (yellow/red)
- **733 carry events** (dribbles/take-ons)
- **1,099 ball control events** (touches, receptions)
- **133 goalkeeper events**

### Untapped Potential
- **Regional analysis** (field thirds, halves, penalty box)
- **Quality metrics** (success rates by region, context)
- **Big data extraction** (big chances, dangerous passes, shot zones)
- **Temporal sequences** (dribble→shot, foul→card)
- **Context cascading** (open play vs set piece vs fast break)
- **Derived metrics** (expected goals, pass difficulty, pressure intensity)

---

## Enrichment Functions by Event Type

### 1. PASS EVENTS (8,967 records)

#### A. Regional Pass Analysis
```python
async def get_pass_statistics_regional(player_id, team_id, region=None):
    """
    Regions:
    - defensive_third: x <= 33.3
    - middle_third: 33.3 < x <= 66.6
    - attacking_third: x > 66.6
    - own_half: x <= 50
    - opponent_half: x > 50
    - penalty_box: x >= 83.3 AND 21.1 <= y <= 78.9
    - defensive_box: x <= 16.7 AND 21.1 <= y <= 78.9
    """
    Returns: {
        region,
        total_attempts,
        successful_passes,
        completion_percentage,
        avg_pass_length,
        forward_passes: count,
        backward_passes: count,
        lateral_passes: count
    }
```

#### B. Pass Type Enrichment (via Qualifiers)
```python
async def get_pass_types(player_id, team_id):
    """
    Qualifier IDs:
    - 1: Long pass (distance > threshold)
    - 4: Through ball (qualifiers.4 exists)
    - 2: Cross (qualifiers.2 exists) - from corners or open play
    - 6: Corner cross (qualifiers.6 exists)
    - 107: Throw-in
    - 123: Goal kick
    - 155: Chipped pass
    - 24-26, 160: Set piece indicators
    """
    Returns: {
        long_passes: count,
        through_balls: count,
        crosses: count,
        crosses_successful: count,
        corner_crosses: count,
        throw_ins: count,
        chipped_passes: count,
        set_piece_passes: count,
        open_play_passes: count
    }
```

#### C. Pass Quality by Context
```python
async def get_pass_quality_context(player_id, team_id):
    """
    Context classification:
    - Open play: No set piece qualifiers
    - From set piece: 24, 25, 26, 160, 6, 107, 123 exist
    - After recovery: Linked from ball_recovery events
    - Under pressure: Linked from pressure events
    """
    Returns: {
        open_play_passes: count,
        open_play_completion: percentage,
        set_piece_passes: count,
        set_piece_completion: percentage,
        passes_under_pressure: count,
        pressure_completion: percentage,
        dangerous_passes: count  # Passes into dangerous zones with high risk
    }
```

#### D. Pass Progression Analysis
```python
async def get_pass_progression(player_id, team_id):
    """
    Analyze vertical pass progression toward opponent goal
    """
    Returns: {
        progressive_passes: count,  # Passes moving >10m toward goal
        progressive_pass_completion: percentage,
        passes_into_final_third: count,
        final_third_pass_completion: percentage,
        key_passes: count,  # Passes leading to shot in next 2 events
        avg_pass_progression_distance: float  # Meters moved toward goal per pass
    }
```

---

### 2. SHOT EVENTS (212 records)

#### A. Shot Location Intelligence
```python
async def get_shot_statistics_detailed(player_id, team_id):
    """
    Coordinate-based analysis of shot data
    """
    Returns: {
        total_shots: count,
        shots_on_target: count,
        on_target_percentage: percentage,
        
        # Location analysis
        shots_inside_box: count,
        shots_outside_box: count,
        box_conversion_rate: percentage,
        
        # Foot analysis  
        right_foot_shots: count,
        left_foot_shots: count,
        headed_shots: count,
        other_body_parts: count,
        
        # Shot type
        big_chances: count,
        big_chance_conversion: percentage,
        penalties_taken: count,
        penalties_scored: count,
        
        # Goal analysis (is_goal=true)
        goals: count,
        goals_inside_box: count,
        goals_outside_box: count,
        average_shot_distance_to_goal: float
    }
```

#### B. Shot Context & Quality
```python
async def get_shot_quality_context(player_id, team_id):
    """
    Shot efficiency with context awareness
    """
    Returns: {
        open_play_shots: count,
        open_play_conversion: percentage,
        set_piece_shots: count,
        set_piece_conversion: percentage,
        fast_break_shots: count,
        fast_break_conversion: percentage,
        shots_after_dribble: count,
        shots_from_transition: count,  # Within 3s of ball recovery
        shooting_accuracy: percentage  # On target vs total
    }
```

---

### 3. DUEL EVENTS (612 records)

#### A. Duel Success Analysis
```python
async def get_duel_statistics(player_id, team_id):
    """
    Ground and aerial duels - requires tracking success via outcome
    Qualifiers: 56 (direction), 233 (distance), 285 (outcome)
    """
    Returns: {
        total_duels: count,
        duels_won: count,
        duels_lost: count,
        duel_success_rate: percentage,
        
        # By direction
        forward_duels: count,
        backward_duels: count,
        lateral_duels: count,
        
        # Regional analysis
        defensive_third_duels: count,
        middle_third_duels: count,
        attacking_third_duels: count,
        
        duel_intensity: float  # Duels per 90 minutes
    }
```

#### B. Aerial Duel Specialization
```python
async def get_aerial_duel_statistics(player_id, team_id):
    """
    Specialized aerial duel metrics - look for aerial indicators
    """
    Returns: {
        aerial_duels: count,
        aerial_duels_won: count,
        aerial_duel_success_rate: percentage,
        
        # Location-based
        defensive_aerial_duels: count,
        attacking_aerial_duels: count,
        
        aerial_duel_intensity: float  # Aerial duels per 90
    }
```

---

### 4. TACKLE EVENTS (325 records)

#### A. Tackle Effectiveness
```python
async def get_tackle_statistics(player_id, team_id):
    """
    Tackle metrics with success tracking via outcome
    Qualifiers: 56 (direction), 233 (distance), 285 (outcome)
    """
    Returns: {
        total_tackles: count,
        successful_tackles: count,
        tackle_success_rate: percentage,
        
        # Direction of threat
        tackles_forward: count,  # Opponent moving forward
        tackles_backward: count,
        tackles_lateral: count,
        
        # Regional analysis
        defensive_tackles: count,  # Defensive third
        midfield_tackles: count,
        attacking_tackles: count,
        
        tackle_intensity: float,  # Per 90 minutes
        clean_sheet_tackles: count  # Tackles in clean sheet matches
    }
```

---

### 5. TAKE-ON EVENTS (302 records)

#### A. Dribbling & Possession Carrying
```python
async def get_takeon_statistics(player_id, team_id):
    """
    Dribbles, carries, take-ons analysis
    """
    Returns: {
        total_take_ons: count,
        successful_take_ons: count,
        take_on_success_rate: percentage,
        
        # Spatial analysis
        take_ons_in_own_half: count,
        take_ons_in_opponent_half: count,
        take_ons_in_box: count,
        take_ons_into_box: count,  # Completed dribbles resulting in box entry
        
        # Risk vs reward
        take_ons_leading_to_shot: count,  # Dribble + shot in sequence
        take_ons_leading_to_turnover: count,
        take_on_efficiency: float,  # Successful take-ons per game
        
        # Dribble distance
        carry_distance_total: float,  # Distance carried
        avg_carry_distance_per_sequence: float
    }
```

---

### 6. BALL CONTROL EVENTS (1,099 records)

#### A. Possession Quality
```python
async def get_ball_control_statistics(player_id, team_id):
    """
    Touches, receptions, ball control - handling of the ball
    """
    Returns: {
        total_touches: count,
        touch_intensity: float,  # Per 90 minutes
        
        # Quality metrics
        controlled_touches: count,
        miscontrolled_touches: count,
        control_accuracy: percentage,
        
        # Reception types
        first_touch_quality: percentage,
        receptions_in_own_half: count,
        receptions_in_opponent_half: count,
        
        # Possession under pressure
        touches_under_pressure: count,
        pressure_control_accuracy: percentage,
        
        # Error tracking
        possession_errors: count,  # Turnovers, miscontrols
        errors_leading_to_shot: count,
        errors_leading_to_goal: count,
        
        # Dispossession
        times_dispossessed: count,
        dispossession_intensity: float
    }
```

#### B. Receiving Patterns
```python
async def get_receiving_statistics(player_id, team_id):
    """
    How player receives ball - quality of first touch
    """
    Returns: {
        total_receptions: count,
        successful_receptions: count,
        reception_success_rate: percentage,
        
        # By pressure level
        receptions_under_pressure: count,
        receptions_with_space: count,
        
        # By location
        receptions_in_defensive_third: count,
        receptions_in_attacking_third: count,
        
        # Turn patterns
        receives_and_turns: count,  # Reception followed by direction change
        avg_position_after_reception: {x, y}  # Heat map
    }
```

---

### 7. FOUL EVENTS (486 records)

#### A. Foul Discipline
```python
async def get_foul_statistics(player_id, team_id):
    """
    Fouls committed and won
    Qualifiers: 56 (direction), 13 (dangerous foul), 265 (hand/other), 152 (penalty foul)
    """
    Returns: {
        fouls_committed: count,
        fouls_won: count,
        
        # Foul type
        dangerous_fouls: count,  # Qualifier 13
        handball_fouls: count,   # Qualifier 265
        penalty_fouls: count,    # Qualifier 152
        
        # Location analysis
        fouls_in_defensive_third: count,
        fouls_in_attacking_third: count,
        fouls_in_box: count,
        
        # Context
        fouls_under_pressure: count,
        fouls_on_counter_attack: count,
        
        # Outcome prediction
        fouls_leading_to_card: count,  # Linked to card events
        fouls_leading_to_goal: count   # Foul immediately before goal
    }
```

---

### 8. CARD EVENTS (46 records)

#### A. Discipline Tracking
```python
async def get_card_statistics(player_id, team_id):
    """
    Yellow and red card tracking
    """
    Returns: {
        yellow_cards: count,
        red_cards: count,
        total_cards: count,
        
        # Card context
        second_yellow_reds: count,  # Red from 2nd yellow
        direct_reds: count,         # Straight red
        
        # Temporal analysis
        avg_minutes_to_first_card: float,
        card_frequency: float,  # Cards per 90
        
        # Suspension risk
        at_risk_of_suspension: boolean,  # > 4 yellows in X games
        matches_until_suspension: int
    }
```

---

### 9. GOALKEEPER EVENTS (133 records)

#### A. Goalkeeper Distribution & Saves
```python
async def get_goalkeeper_statistics(player_id, team_id):
    """
    Goalkeeper-specific actions: saves, sweeps, punches, claims
    """
    Returns: {
        saves: count,
        save_success_rate: percentage,
        
        # Save type
        saves_with_feet: count,
        punch_outs: count,
        claims: count,      # Claims from crosses
        
        # Shot pressure
        shots_faced: count,
        high_claim_rate: percentage,  # Claims vs punches/saves
        
        # Sweeper actions
        sweeper_actions: count,
        balls_played_out: count,
        
        # Distribution
        pass_completion_rate: percentage,
        long_kick_accuracy: percentage,
        throw_out_accuracy: percentage,
        
        # Clean sheets & goals
        clean_sheets: count,
        goals_conceded: count
    }
```

---

### 10. ASSIST & KEY PASS TRACKING

#### A. Creativity Metrics
```python
async def get_assist_statistics(player_id, team_id):
    """
    Assists and key passes - passes leading to shots/goals
    Requires event sequence linking (pass → shot → goal within threshold)
    """
    Returns: {
        assists: count,
        key_passes: count,  # Passes leading to shots
        big_chance_created: count,
        
        # Context
        assists_open_play: count,
        assists_set_piece: count,
        assists_corner: count,
        
        # Timing  
        avg_time_from_pass_to_shot: float,
        
        # Spatial
        avg_assist_distance: float,
        assists_from_defensive_third: count,
        
        # Consistency
        assists_per_90: float,
        creation_rate: percentage  # Key passes leading to goals
    }
```

---

### 11. PRESSURE & DEFENSIVE ACTIONS

#### A. Pressure Intensity
```python
async def get_pressure_statistics(player_id, team_id):
    """
    Pressure events - how often player pressures opponent
    """
    Returns: {
        pressure_events: count,
        pressure_intensity: float,  # Per 90
        
        # Pressure outcome
        pressure_leading_to_turnover: count,
        pressure_leading_to_bad_pass: count,
        pressure_success_rate: percentage,
        
        # Pressure zones
        high_press_actions: count,  # Pressing in opponent's half
        mid_press_actions: count,
        low_press_actions: count,
        
        # Temporal
        avg_distance_from_ball_when_pressuring: float
    }
```

---

### 12. RECOVERY & TRANSITION

#### A. Transition Metrics
```python
async def get_recovery_statistics(player_id, team_id):
    """
    Ball recovery - regaining possession
    """
    Returns: {
        total_recoveries: count,
        recovery_intensity: float,  # Per 90
        
        # Recovery zones
        recoveries_in_own_third: count,
        recoveries_in_middle_third: count,
        
        # Outcome
        recoveries_leading_to_shot: count,  # Within 5s of shot
        recoveries_leading_to_pass_chain: count,  # Possession sequences
        avg_possession_duration_after_recovery: float
    }
```

---

## Advanced Computed Metrics

### A. Player Heat Maps & Influence
```python
async def get_player_influence_map(player_id, team_id):
    """
    Aggregate all event locations to create influence heatmap
    """
    Returns: {
        event_map: [[event_count]],  # 10x10 grid on field
        most_active_zone: {x_range, y_range, density},
        avg_position: {x, y},
        position_spread: float,  # Standard deviation of positions
    }
```

### B. Player Performance Index
```python
async def get_performance_index(player_id, team_id):
    """
    Composite score combining multiple metrics
    """
    Returns: {
        pass_completion_index: float,      # 0-100
        defensive_contribution_index: float,
        creative_contribution_index: float,
        physical_contribution_index: float,  # Duels, tackles, pressure
        overall_performance_index: float     # Weighted average
    }
```

### C. Positional Role Analysis
```python
async def get_player_role_analysis(player_id, team_id):
    """
    Infer playing role from event patterns
    """
    Returns: {
        inferred_role: string,  # CB, FB, CM, ST, etc.
        role_confidence: percentage,
        
        # Role-specific metrics
        role_benchmarks: {
            pass_completion_vs_position: float,
            defensive_actions_vs_position: float,
            creative_actions_vs_position: float
        }
    }
```

---

## Implementation Priority

### Phase 1: Core Enrichments (High Value, Low Complexity)
1. **Regional pass analysis** - Divide passes by thirds/halves/box
2. **Shot location details** - Coordinate-based shot quality
3. **Foul/card tracking** - Simple count aggregation with location
4. **Pass type extraction** - Qualifier-based classification
5. **Recovery events** - Simple aggregation

### Phase 2: Context-Aware Analytics (Medium Value, Medium Complexity)
6. **Pass quality by context** - Open play vs set piece vs pressure
7. **Duel success tracking** - Outcome-based duel analysis
8. **Tackle effectiveness** - Regional + outcome analysis
9. **Goalkeeper distribution** - Pass accuracy by type
10. **Pressure statistics** - Intensity and success rates

### Phase 3: Advanced Intelligence (High Value, High Complexity)
11. **Assist/key pass linking** - Event sequence tracking
12. **Transition analysis** - Recovery → possession outcome
13. **Dribble efficiency** - Take-on success + progression
14. **Heat maps & influence** - Spatial distribution analysis
15. **Performance indices** - Composite scoring

### Phase 4: ML-Ready Metrics (ML Model Training)
16. **Expected goals** - Integrate xG model from ml-service
17. **Expected assists** - Key pass quality scoring
18. **Player similarity** - Role-based clustering
19. **Performance predictions** - Time-series forecasting

---

## Data Requirements for Implementation

### Core Data Already Available
- ✅ Event coordinates (x, y)
- ✅ Event timestamps (period, minute, second)
- ✅ Player & team IDs
- ✅ Event success flags (is_goal, is_successful)
- ✅ Qualifier dictionaries (numeric string keys with values)

### Data Needing Enhancement
- ⚠️ Event sequencing (eventID linking for chains)
- ⚠️ Player lineups & substitutions (for per-90 normalization)
- ⚠️ Match context (possession %, expected output)
- ⚠️ Formation tracking (for positional benchmarking)

### Optional Advanced Data
- 🔲 Video segment references (for context validation)
- 🔲 Player physical data (height, weight for aerial dominance models)
- 🔲 Opposition defensive structure (for pressure effectiveness)

---

## Database Optimization for Enrichments

### Current Challenge
Motor async aggregation returns empty for reasons TBD - **switching to find()+Python approach**

### Recommended Pattern
```python
async def get_enriched_stats(player_id, team_id, event_type):
    # 1. Use find() to get documents
    docs = await db.match_events.find(filters).to_list(None)
    
    # 2. Compute enrichments in Python
    stats = {
        'total': len(docs),
        'by_region': compute_regional_breakdown(docs),
        'by_context': compute_context_breakdown(docs),
        'quality': compute_quality_metrics(docs),
        'derived': compute_derived_metrics(docs)
    }
    
    # 3. Cache comprehensive result
    await redis.setex(cache_key, 300, json.dumps(stats))
    return stats
```

### Benefits
- ✅ Guaranteed working data access
- ✅ Complex logic in Python (easier to debug, extend)
- ✅ More flexible transformation pipeline
- ✅ Easier to add new enrichments without pipeline rewrites

---

## Next Steps

1. **Verify basic find() + Python aggregation works** (Pass, Shot, Tackle)
2. **Implement Phase 1 enrichments** (regional + qualifier-based)
3. **Add qualifier mapping reference** (all 300+ qualifier IDs)
4. **Build event sequence linker** (for assists, transitions)
5. **Implement heat map generation** (spatial analytics)
6. **Create composite performance indices** (ML-ready features)
7. **Integrate with ml-service** (feed features to xG/xA models)

