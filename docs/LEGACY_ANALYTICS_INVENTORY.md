# Legacy Analytics Inventory
## Comprehensive Analysis of Opta Event Data - Historical Analytics Patterns

**Created:** April 2026  
**Source:** archive/oldbackend/optaapi/src/events/  
**Purpose:** Document event types, enrichment patterns, and statistical calculations for future analytics implementation

---

## Overview

The legacy backend defined **14 major event-based analyzer classes** that processed Opta F24 event data and calculated 200+ statistical measures. This document catalogs:
- Event types and their meanings
- Calculated statistics per event type
- Qualifier IDs used for enrichment
- Generalized patterns for analytics implementation

---

## 1. PASS EVENTS (PassEvent.py)
**Primary Event Type:** TypeID = 1 (Pass)

### Core Statistics Tracked
- **Basic Counts:** passes_total, passes_successful, passes_unsuccessful
- **Pass Direction:** forward_passes, backward_passes, sideway_passes
- **Pass Regions:** 
  - Defensive third, middle third, attacking third (both originate and destination)
  - Own half vs opponent half
  - Passes into/out of box

### Enriched Statistics
- **Pass Quality Metrics:**
  - Pass completion percentage (overall and by region)
  - Pass completion percentage into each third
  - Pass completion in opponent/own half
  - Pass completion in final third
  - Average pass length
  - Total pass length

- **Box/Critical Area Passes:**
  - Passes into defensive third from own box
  - Total passes into box
  - Passes into box with cross
  - Successful passes into box with cross

- **Cross Analysis:**
  - Total crosses, successful crosses, unsuccessful crosses
  - Crosses from free kicks, open play, right/left third
  - Cross success rate (overall and open play)
  - Crosses from corners
  - Successful crosses from corners
  - Short corners

- **Pass Types (via Qualifiers):**
  - Long passes (ID_1): counted, success tracked
  - Through balls (ID_4): tracked
  - Chipped passes (ID_155): counted, success tracked
  - Lay-off passes (ID_?)
  - Launch passes
  - Flick-on passes with success ratio
  - Pull-back passes
  - Switch play passes
  - Headed passes

- **Set Piece Passes:**
  - Free kick passes (direct/indirect)
  - Corner passes
  - Throw-in passes
  - Goal kick passes
  - Keeper throws

### Key Qualifiers Used
- **140:** x_end coordinate
- **141:** y_end coordinate  
- **213:** pass angle
- **1:** long pass
- **2:** cross indicator (from corners/play)
- **6:** corner indicator
- **107:** throw-in indicator
- **123:** goal kick indicator
- **155:** chipped pass
- **24, 25, 26, 160:** set piece indicators (free kick, corner, throw-in, etc.)
- **22, 23:** regular play / fast break indicators

### Spatial Zones Analyzed
```
Field divided into thirds:
- x <= 33.3: Defensive third
- 33.3 < x <= 66.6: Middle third
- x > 66.6: Attacking third

Box region:
- x >= 83.3 AND 21.1 <= y <= 78.9: Penalty box
```

---

## 2. SHOT AND GOAL EVENTS (ShotandGoalEvents.py)
**Event Types:** TypeID = 13 (Miss), 14 (Post), 15 (Attempt Saved), 16 (Goal)

### Goal Metrics
- **Goal Counts:**
  - goals, goals_inside_the_box, goals_outside_the_box
  - left_footed_goals, right_footed_goals
  - headed_goals, goals_with_other_part_of_body

- **Goal Context:**
  - Goals from penalties, non-penalty goals
  - Goals from set play, open play
  - Goals from corners, direct free kicks, throw-ins
  - Goals from fast break, volleys, regular play
  - Goals deflected, own goal
  - Unassisted goals

- **Goal Timing:**
  - Minutes per goal

### Shot Analysis
- **Total Shots:** by location (inside/outside box), foot, head
- **Shot Type Breakdown:**
  - Headed shots (total, on target, off target, blocked)
  - Left/right footed shots (each category)
  - Shots after dribble
  - Shots with first touch

- **Shot Quality:**
  - Big chances (total, conversion rate)
  - Direct free kicks (total, on target, off target)
  - Penalty shots (taken, saved, conversion)

- **Shot Direction:**
  - Shots on target, off target, blocked, hitting post
  - Shot cleared off line (inside/outside box)
  - Shots hit woodwork

- **Shot Context (Set Play vs Open Play):**
  - From set play, open play, corners, free kicks, throw-ins
  - From fast break, regular play
  - With/without deflection

### Shot Percentages
- Headed goals rate, open play goals rate
- Headed shots rate, inside/outside box shot rate
- Left/right foot shot rate
- Shots on target rate, blocked shots rate
- Shooting percentage (goals/shots)
- No-block shooting percentage
- Big chance conversion rate
- Free kick on target rate
- Unassisted goals/shots rate

### Key Qualifiers
- **15:** Headed shot
- **72:** Left-footed shot
- **20:** Right-footed shot
- **9:** Penalty
- **24, 25, 26, 160:** Set piece indicators
- **22, 23:** Open play / fast break
- **214:** Big chance
- **328:** First touch shot
- **133:** Deflected shot
- **169:** Error led to shot
- **170:** Error led to goal
- **211:** Overrun (for dribble linkage)

### Coordinates Used
- Event x, y: shot location
- x_end, y_end: could track trajectory

---

## 3. GOALKEEPER EVENTS (GoalkeeperEvents.py)
**Event Types:** TypeID = 10 (Save), 54 (Smother), and related

### Save Analysis
- **Save Types:**
  - Body, caught, collected, diving, feet, fingertip, hands
  - Parried (danger), parried (safe)
  - Reaching, standing, stooping
  - 1v1 saves, penalty saves

- **Save Location:**
  - Inside box, outside box

- **Save Metrics:**
  - Total saves, save percentage

### Cross/Ball Control
- **Crosses:**
  - Crosses faced, crosses claimed, crosses punched
  - Crosses not claimed
  - Cross percentage faced

- **Distribution:**
  - Successful goal kicks, total goal kicks
  - Successful keeper throws, total keeper throws
  - Successful keeper distributions

### Defensive Performance
- **Clean Sheets:** tracked per match
- **Sweeper Actions:**
  - GK sweeper (comes off line)
  - Accurate keeper sweeper actions

### Shots Against
- **Shot Conceded:**
  - Total shots against, shots on target against
  - Average shot distance against
  - Headed shots on target conceded
  - Shots on target inside/outside box

- **Big Chances Against:**
  - Big chances faced
  - Shots conceded including blocks

### Key Qualifiers
- **94, 190:** Exclude from saves
- **21:** Save body
- **176:** Caught
- **177:** Collected
- **179:** Diving
- **183:** Feet
- **175:** Fingertip
- **182:** Hands
- **9:** Penalty
- **174, 173:** Parried danger/safe
- **181:** Reaching
- **178:** Standing
- **180:** Stooping
- **101:** Shot against
- **139:** Own player shot/save

---

## 4. DUEL EVENTS (DuelEvents.py)
**Event Types:** TypeID = 44 (Aerial), 3 (Take On), 4 (Foul with qualifier)

### Duel Counts
- **Total:** total_duels, successful_duels, unsuccessful_duels
- **Ground vs Aerial:** ground_duels vs aerial_duels
- **Context:** defensive_duels, offensive_duels

### Regional Duel Analysis
**Thirds:**
- Duels in defending/middle/attacking third
- Success rate by third
- Unsuccessful duels by third

**Halves:**
- Defensive half vs attacking half
- Success rate by half

### Duel Success Rates
- Overall duel success rate
- Success rate by region (each third and half)

### Key Qualifiers
- **285:** Defensive duel
- **286:** Offensive duel
- **211:** Overrun (excludes from ground duel count)
- **264:** Aerial duel from foul

### Outcome Mapping
- outcome = 1: SUCCESSFUL
- outcome = 0: UNSUCCESSFUL

---

## 5. AERIAL DUEL EVENTS (AerialDuelEvents.py)
**Event Type:** TypeID = 44 (Aerial)

### Aerial Duel Metrics
- **Basic Counts:**
  - total_aerial_duels, successful_aerial_duels, unsuccessful_aerial_duels
  - Aerial duel success rate

### Regional Success Analysis
**By Thirds:**
- Aerial duels in defending/middle/attacking third
- Successful aerial duels by third
- Success rate by third

**By Half:**
- Aerial duels in defending/attacking half
- Successful aerial duels by half
- Success rate by half

### Similar Pattern to Ground Duels
- Tracks defensive vs attacking context
- Location-based aggregation (thirds and halves)
- Success rate calculations

---

## 6. FOUL EVENTS (FoulEvents.py)
**Event Type:** TypeID = 4 (Foul)

### Foul Direction
- **Outcome-based:**
  - fouls_won (outcome = SUCCESSFUL, from player's perspective)
  - fouls_conceded (outcome = UNSUCCESSFUL)
  - Total fouls = won + conceded

### Regional Analysis
- **Fouls Won by Region:**
  - In defending third, middle third, attacking third
  
- **Fouls Conceded by Region:**
  - In defending third, middle third, attacking third

### Foul Type Context
- **Penalties:**
  - penalty_won, penalty_conceded
  - Via qualifier ID_9 (penalty)
  
- **Handball:**
  - handball_conceded
  - Via qualifier ID_10 (handball)

### Insight: Foul Direction Interpretation
- outcome = 1: Player won the foul (was fouled)
- outcome = 0: Player committed the foul (conceded)

---

## 7. CARD EVENTS (CardEvents.py)
**Event Type:** TypeID = 17 (Card)

### Card Types
- **By Color:**
  - yellow_card (ID_31)
  - second_yellow_card (ID_32)
  - red_card (ID_33)
  
- **Card Management:**
  - card_rescinded (ID_171)
  - total_cards (sum of all)

### Qualifiers Used
- ID_31: Yellow card
- ID_32: Second yellow card (red)
- ID_33: Direct red card
- ID_171: Card rescinded

---

## 8. TAKE-ON/DRIBBLE EVENTS (TakeOnEvents.py)
**Event Type:** TypeID = 3 (Take On)

### Take-On Metrics
- **Basic Counts:**
  - total_take_ons, take_ons_successful, take_ons_unsuccessful
  
- **Success Rate:**
  - take_on_success_rate = 100 * (successful / total)

### Contextual Take-Ons
- **Location:**
  - take_ons_in_box (x >= 83.3 AND 21.1 <= y <= 78.9)
  - successful_take_ons_in_box
  
- **Attacking Threat:**
  - take_on_in_attacking_third (x > 66.6) - successful
  - take_on_in_attacking_third_uns - unsuccessful
  - take_on_success_rate_attacking_third

### Tackle Inference
- **Overrun Detection:**
  - take_on_overrun (ID_211 qualifier)
  - tackled = unsuccessful_take_ons - overruns
  - (Qualifies as "lost ball" vs "defender ran past the ball")

---

## 9. BALL CONTROL EVENTS (BallControlEvents.py)
**Event Types:** TypeID = 50 (Dispossessed), 51 (Error), 61 (Ball Touch), 2 (Offside Pass)

### Possession Loss
- **Dispossessed:**
  - total_dispossessed
  
- **Ball Touch Quality:**
  - ball_touch (total), ball_hit_the_player, unsuccessful_control
  - Outcome: successful = controlled, unsuccessful = touch failed

### Error Tracking
- **Errors:**
  - total_errors
  
- **Error Consequences:**
  - error_led_to_shot (ID_169)
  - error_led_to_goal (ID_170)

### Offside Tracking
- **Caught Offside:**
  - caught_offside (via ID_2 Offside Pass with ID_7 qualifier)

---

## 10. TOUCH EVENTS (TouchEvents.py)
**Event Types:** TypeID = 1 (Pass), 3 (Take On), 4 (Foul), 7 (Tackle), 8 (Interception), 9 (Turnover), etc.

### Touch Count
- **Total Touches:** by location (thirds and box)
  - total_touches_in_defensive/middle/attacking_third
  - total_touches_in_box

### Turnover Analysis
- **Turnover Percentage:** turnover_percentage calculation

### Tackle Analysis
- **Tackle Counts:**
  - total_tackles, successful_tackles, unsuccessful_tackles
  - tackle_made_percentage
  
- **Tackle by Location:**
  - in attacking/middle/defending third
  
- **Tackle Context:**
  - last_man_tackles

### Challenge Tracking
- **Challenges:** total_challenges
- **Tackle Attempts:** tackle_attempts
- **Tackle Success Percentage:** calculation from totals

### Recovery Metrics
- **Ball Recovery:**
  - total_ball_recovery
  - By location (thirds)

### Interception Analysis
- **Interceptions:** total_interceptions
- **By Location:** defensive/middle/attacking third

### Clearance Analysis
- **Clearances:** total_clearances
- **By Location:** defensive/middle/attacking third
- **Clear Types:**
  - blocked_cross
  - headed_clearance
  - total_real_clearances
  - clearances_off_the_line

### Defensive Touches
- **Defensive Touches:** defensive_touches count

### Offside Provoked
- **Offside Provoked:** total_offsides_provoked

---

## 11. ASSIST EVENTS (AssistEvents.py)
**Event Types:** TypeID = 80 (Assist), 81 (First Touch Assist), 83 (Key Pass Dribble), 84 (Key Pass), 85 (Chances Set Play), 86 (Chances Open Play), 87 (First Touch Key Pass)

### Assists
- **Total Assists:** total_assists
  
- **Assist Context:**
  - assists_from_open_play (ID_22, ID_23)
  - assists_from_set_play (ID_24, ID_25, ID_26, ID_160)
  - assists_from_free_kick (ID_24)
  - assists_from_corners (ID_25)
  - assists_from_throw_in (ID_107)
  - assists_from_goal_kick (ID_124)
  
- **Assist Intent:**
  - intentional_assists (ID_154)

### Key Passes
- **Key Passes:** total key passes not yet captured
- **Key Pass Dribble:** key passes after dribble
- **Key Pass Success:** assist_and_key_passes metric

### Chances Created
- **From Set Play:** chances_created_from_set_play
- **From Open Play:** chances_created_from_open_play
- **Rate:** open_play_assist_rate

### First Touch Analytics
- **First Touch Assists:** assist_for_first_touch_goal
- **First Touch Key Pass:** keypass_for_first_touch_shot

### Key Qualifiers
- **22, 23:** Regular play / fast break indicators
- **24:** Free kick
- **25:** Corner
- **26:** Unknown set piece type
- **160:** Throw-in context
- **107:** Throw-in specific
- **124:** Goal kick
- **154:** Intentional assist

---

## 12. GAMES AND MINUTES EVENTS (GamesandMinutesEvents.py)
**Event Types:** TypeID = 19 (Player On), 18 (Player Off), 20 (Player Retired), 21 (Player Returns), 34 (Team Setup), 35 (Player Changed Position), 40 (Formation Change)

### Match Participation
- **Game Counts:**
  - games_played, games_started
  
- **Playing Time:**
  - total_minutes
  - minutes_per_game
  - actual_minutes_on_field

### Substitution Tracking
- **Substitutions:**
  - substitute_off, substitute_on
  - Tactical substitution detection

### Player Status Events
- **Player On/Off:** counts and timing
- **Player Retired/Returns:** tracking
- **Position Changes:** player_changed_position

### Formation Tracking
- **Formation Changes:** detected from TypeID = 40
- **Teams Setup:** from TypeID = 34 with ID_30 qualifier containing lineup
- **Formations Dictionary:** Maps ID to formation (e.g., "2" = "442")
  
  ```
  "2": "442", "3": "41212", "4": "433", "5": "451", "6": "4411",
  "7": "4141", "8": "4231", "9": "4321", "10": "532", "11": "541",
  "12": "352", "13": "343", "15": "4222", "16": "3511", "17": "3421",
  "18": "3412", "19": "3142", "20": "343d", "21": "4132", "22": "4240",
  "23": "4312", "24": "3241", "25": "3331"
  ```

### Injury Tracking
- **Injured Status:** player_injured detection

### Lineup Intelligence
- **All Players in Game:** determined from Team Setup event
- **Starting 11:** from initial Team Setup
- **Substitutes List:** tracked via Player On/Off events
- **Position Tracking:** exact_position, positions_played, formations_played

---

## 13. EVENT TYPES REFERENCE (from Events.py)

### Complete Event Type Mapping
| ID | Type | Notes |
|----|------|-------|
| 1 | Pass | outcome: 0=unsuccessful, 1=successful |
| 2 | Offside Pass | outcome always 1 |
| 3 | Take On | 0=lost possession, 1=successful |
| 4 | Foul | 0=committed, 1=won |
| 5 | Out | 0=team put out, 1=team won corner |
| 6 | Corner Awarded | 0=conceded, 1=won |
| 7 | Tackle | 0=attempted, 1=successful |
| 8 | Interception | outcome always 1 |
| 9 | Turnover | - |
| 10 | Save | outcome always 1 |
| 11 | Claim | 0=dropped, 1=caught |
| 12 | Clearance | outcome always 1 |
| 13 | Miss | outcome 1 |
| 14 | Post | outcome 1 |
| 15 | Attempt Saved | outcome 1 |
| 16 | Goal | outcome 1 |
| 17 | Card | outcome 1 |
| 18 | Player Off | outcome 1 |
| 19 | Player On | outcome 1 |
| 20-28 | Various | Status/formation changes |
| 30 | End | outcome 1 |
| 32 | Start | outcome 1 |
| 34 | Team Setup | outcome 1 |
| 35-40 | Position/Formation | outcome 1 |
| 41-51 | Ball Events | Punch, skill, recovery, dispossessed, error, etc. |
| 54-73 | Defensive Events | Smother, block, catch offside, etc. |
| 74-87 | Derived Events | Blocked pass, key pass, assist, chances |
| 90-94 | Opponent Stats | Shot against, goal against, etc. |

---

## 14. GENERALIZED PATTERNS FOR ANALYTICS

### Pattern 1: Regional Analysis
**Used Across:** Passes, Fouls, Duels, Tackles, Clearances, Interceptions, Touches

**Pattern:**
```python
if x <= 33.3:
    defensive_third_metric += 1
elif 33.3 < x <= 66.6:
    middle_third_metric += 1
elif x > 66.6:
    attacking_third_metric += 1
```

**Insight:** Field is conceptually divided into 3 equal zones by x-coordinate. Success rates are calculated per zone.

### Pattern 2: Box/Penalty Area Detection
**Used Across:** Passes, Shots, Take-Ons, Clearances

**Pattern:**
```python
if x >= 83.3 and 21.1 <= y <= 78.9:
    in_box_metric += 1
```

**Insight:** Box spans from x=83.3 to 100 (end line), y=21.1 to 78.9 (sides of penalty area)

### Pattern 3: Success Rate Calculation
**Used Across:** All event types with binary outcomes

**Pattern:**
```python
success_rate = 100 * (successful / (successful + unsuccessful))
```

**Insight:** Events with outcome field (1=successful, 0=unsuccessful) generate percentages

### Pattern 4: Outcome-Based Direction
**Used Across:** Fouls, Duels, Tackles, Challenges

**Pattern:**
```python
if event.outcome == SUCCESSFUL:
    player_won_event += 1
elif event.outcome == UNSUCCESSFUL:
    player_lost_event += 1
```

**Insight:** outcome interpretation depends on context (foul committed vs. won, etc.)

### Pattern 5: Qualifier-Based Enrichment
**Used Across:** All event types

**Pattern:**
```python
qualifier_list = [q.qualifierID for q in event.qEvents]
if SPECIFIC_QUALIFIER_ID in qualifier_list:
    specific_context_metric += 1
```

**Insight:** 150+ qualifier IDs add context to event. Key qualifiers:
- Set piece indicators (24, 25, 26, 160)
- Body part (15=head, 20=right foot, 72=left foot)
- Outcome modifiers (211=overrun, 214=big chance)
- Location details (140=x_end, 141=y_end)

### Pattern 6: Context Cascading
**Used Across:** Assists, Shots, Key Passes

**Pattern:**
```python
# First check major category
if event.typeID == EventIDs.ID_80_Assist:
    total_assists += 1
    
    # Then check context qualifiers
    if QTypes.ID_22 in qualifier_list or QTypes.ID_23 in qualifier_list:
        assists_from_open_play += 1
    
    # Then check sub-context
    if QTypes.ID_24 in qualifier_list:
        assists_from_free_kick += 1
```

**Insight:** Creates hierarchical categorization (total -> context -> sub-context)

### Pattern 7: Coordinate-Based Calculation
**Used Across:** Passes, Shots, Duels, Fouls

**Pattern:**
```python
x = event.x           # Starting location
y = event.y           # Starting location
x_end = qualifier_140 # From qualifiers
y_end = qualifier_141 # From qualifiers

# Can calculate distance, angle, direction
angle = math.degrees(value)
```

**Insight:** Events carry start location; end location comes from qualifiers

### Pattern 8: Temporal Linkage
**Used Across:** Shots after dribble, Error consequences

**Pattern:**
```python
if current_event.eventID - 1 == previous_dribble.eventID:
    shot_after_dribble += 1
```

**Insight:** Events can be linked by eventID sequence to detect sequences

### Pattern 9: Half-Pitch Analysis
**Used Across:** Aerial duels, potentially others

**Pattern:**
```python
if x <= 50:
    defending_half_metric += 1
elif x > 50:
    attacking_half_metric += 1
```

**Insight:** Alternative to thirds for aggregation (2 zones instead of 3)

### Pattern 10: Multi-Outcome Event Handling
**Used Across:** Goalkeeper events, complex plays

**Pattern:**
```python
# Exclude certain cases first
if EXCLUDE_QUALIFIER not in qualifier_list:
    # Process main event
    main_metric += 1
    
    # Then check sub-types
    if SUB_QUALIFIER_1 in qualifier_list:
        sub_metric_1 += 1
```

**Insight:** Some events need filtering before processing (saves with exclusions)

---

## 15. QUALIFIER ID REFERENCE (Partial)

| ID | Meaning | Usage |
|----|---------|-------|
| 1 | Long pass | Passes |
| 2 | Cross indicator | Passes/Crosses |
| 4 | Through ball | Passes |
| 6 | Corner | Passes |
| 9 | Penalty | Fouls, Cards, Shots |
| 10 | Handball | Fouls |
| 15 | Headed | Shots, Passes |
| 20 | Right foot | Shots, Passes |
| 21 | Body/Other | Saves |
| 22 | Regular play | Assists, Shots |
| 23 | Fast break | Assists, Shots |
| 24 | Free kick | Assists, Passes, Shots |
| 25 | Corner (set piece) | Assists, Passes, Shots |
| 26 | Unknown set piece | Assists |
| 31 | Yellow card | Cards |
| 32 | Second yellow card | Cards |
| 33 | Red card | Cards |
| 72 | Left foot | Shots |
| 94 | Exclude from save count | Saves |
| 101 | Shot against | Saves |
| 107 | Throw-in | Assists, Passes |
| 123 | Goal kick | Passes |
| 124 | Goal kick assist | Assists |
| 139 | Own player shot | Saves |
| 140 | x_end coordinate | All events with end location |
| 141 | y_end coordinate | All events with end location |
| 154 | Intentional assist | Assists |
| 155 | Chipped pass | Passes |
| 160 | Throw-in context | Assists, Shots |
| 169 | Error led to shot | Errors |
| 170 | Error led to goal | Errors |
| 171 | Card rescinded | Cards |
| 173-183 | Save technique types | Saves |
| 190 | Exclude from save count | Saves |
| 211 | Overrun/ran past ball | Take-ons, Duels |
| 214 | Big chance | Shots |
| 264 | Aerial duel from foul | Aerial duels |
| 285 | Defensive duel | Duels |
| 286 | Offensive duel | Duels |
| 328 | First touch shot | Shots |

---

## 16. CALCULATION PATTERNS FOR CONVERSION

### Statistical Formulas Observed

**Completion/Success Rate:**
```
rate = 100 * (successful / (successful + unsuccessful))
```

**Average Metric:**
```
average = total_length / total_passes
```

**Rate Ratios:**
```
long_pass_ratio = long_passes / total_passes
```

**Timing Metrics:**
```
minutes_per_event = total_minutes / total_events
```

**Percentage Distribution:**
```
defensive_third_percentage = (passes_in_defensive_third / total_passes) * 100
```

---

## 17. IMPLEMENTATION RECOMMENDATIONS

### Generalized Event Processor Architecture
Based on observed patterns, a generalized event processor should:

1. **Accept Event Type Configuration**
   - Define base events to process
   - Map qualifier IDs to enrichments
   - Define regional zones

2. **Implement Core Counters**
   - Total, successful, unsuccessful
   - By region (thirds/halves)
   - By context (qualifiers)

3. **Calculate Derived Metrics**
   - Success rates per region
   - Aggregations and sums
   - Ratio calculations

4. **Support Coordinate Enrichment**
   - Detect zone from x, y
   - Use x_end, y_end from qualifiers
   - Calculate distance/angle if needed

5. **Handle Temporal Sequences**
   - Link events by eventID
   - Detect play sequences (dribble -> shot)

### Migration Strategy
Rather than individual event classes:
- Use unified **event calculator** with configuration
- Each stat is a **configurable calculation** (region + qualifier + outcome)
- Support **aggregation templates** (by thirds, by half, by qualifier)
- Enable **hierarchical stat structures** (total -> context -> sub-context)

---

## Appendix: File Structure

```
archive/oldbackend/optaapi/src/events/
├── Events.py               # Event type constants (TypeID mapping)
├── QTypes.py              # Qualifier type constants (ID_1 through ID_146+)
├── Constructor.py         # Event construction/enrichment logic
├── PassEvent.py           # Pass statistics (300+ lines)
├── ShotandGoalEvents.py   # Shot/goal metrics
├── GoalkeeperEvents.py    # Keeper-specific stats
├── DuelEvents.py          # Ground duel metrics
├── AerialDuelEvents.py    # Aerial duel metrics
├── FoulEvents.py          # Foul statistics
├── CardEvents.py          # Card tracking
├── TakeOnEvents.py        # Dribble/take-on stats
├── BallControlEvents.py   # Possession quality
├── TouchEvents.py         # Touch and defensive event aggregation
├── AssistEvents.py        # Assist and chance metrics
├── GamesandMinutesEvents.py # Participation and formation
└── EventMinutes.py        # (Not fully reviewed)
```

---

## Summary Statistics

- **Event Analyzer Classes:** 14
- **Unique Statistics Tracked:** 200+
- **Qualifiers Referenced:** 150+
- **Event Types Used:** 30+
- **Regional Aggregation Levels:** 3 (thirds) or 2 (halves)
- **Context Dimensions:** Field location, set piece type, body part, defensive/offensive, player direction

---

**Document Version:** 1.0  
**Last Updated:** April 2026
