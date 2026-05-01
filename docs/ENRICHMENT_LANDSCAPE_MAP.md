# Opta Event Data Enrichment Landscape
## Comprehensive Mapping of Extractable Analytics

**Status:** Phase 1 Complete (7 event types enriched), Phases 2-4 Roadmapped

---

## Event Types & Enrichment Status

```
┌─ PASS EVENTS (8,967 records) ═════════════════════════════════════════
│  Phase 1 ✅ COMPLETE:
│  ├─ Regional breakdown (thirds, halves)
│  ├─ Pass direction classification (forward/backward/lateral)
│  ├─ Pass type extraction (long, cross, through ball, chipped, etc.)
│  ├─ Set piece vs open play distinction
│  └─ Cross completion tracking
│
│  Phase 2 (Planned):
│  ├─ Pass difficulty scoring (distance × pressure × crowd)
│  ├─ Pass danger zones (passes into critical areas)
│  ├─ Possession chain analysis (pass sequences)
│  ├─ Passing networks (who passes to whom)
│  └─ Progressive pass frequency (moving toward goal)
│
│  Phase 3 (Planned):
│  ├─ Expected pass completion (xPC) modeling
│  ├─ Possession value (passes leading to shots)
│  ├─ Ball retention efficiency by zone
│  └─ Passing lane identification
│
└─ Status: 7 players tested, 250+ passes aggregated per player

┌─ SHOT EVENTS (212 records) ═══════════════════════════════════════════
│  Phase 1 ✅ COMPLETE:
│  ├─ Location analysis (box vs outside, distance to goal)
│  ├─ Shot type classification (foot, head, body)
│  ├─ Goal tracking with location
│  ├─ Big chance identification
│  ├─ Penalty tracking (shot + conversion)
│  └─ Shooting accuracy (on target %)
│
│  Phase 2 (Planned):
│  ├─ Expected goals (xG) integration with ml-service
│  ├─ Shot quality scoring (likelihood of goal)
│  ├─ Shooting under pressure analysis
│  ├─ Shot outcome linkage (rebound, keeper play, etc.)
│  └─ Goal assists context (who created the chance)
│
│  Phase 3 (Planned):
│  ├─ Heat map of shooting zones
│  ├─ Seasonal conversion trends
│  ├─ Shot timing analysis (first touch, setups)
│  └─ Defensive influence on shots
│
└─ Status: ~8 shots per player, conversion rates tracked

┌─ DUEL EVENTS (612 records) ═══════════════════════════════════════════
│  Phase 1 ✅ COMPLETE:
│  ├─ Duel success rate (% won)
│  ├─ Regional breakdown (field thirds)
│  ├─ Half-based dominance analysis
│  └─ Total duel count & intensity
│
│  Phase 2 (Planned):
│  ├─ Aerial vs ground duel separation
│  ├─ Duel outcome consequence (possession, turnover)
│  ├─ One-on-one effectiveness
│  ├─ Duel distance analysis (from qualifier)
│  └─ Contested space control
│
│  Phase 3 (Planned):
│  ├─ Duel heat maps by position
│  ├─ Duel timing (anticipation vs recovery)
│  ├─ Defensive line integrity via duels
│  └─ Physical dominance ranking
│
└─ Status: 42 duels per player, 62% success rate typical

┌─ TACKLE EVENTS (325 records) ════════════════════════════════════════
│  Phase 1 ✅ COMPLETE:
│  ├─ Tackle success rate (% successful)
│  ├─ Regional concentration (which third)
│  ├─ Direction analysis (forward/backward/lateral)
│  └─ Tackle intensity (count per 90)
│
│  Phase 2 (Planned):
│  ├─ Tackle consequence (ball recovery vs turnover)
│  ├─ Sliding vs standing tackles
│  ├─ Tackle timing (anticipatory vs reactive)
│  ├─ Card risk analysis (fouls via tackles)
│  └─ Box vs open field tacklers
│
│  Phase 3 (Planned):
│  ├─ Clean sheet tackle patterns
│  ├─ Under-pressure tackler effectiveness
│  ├─ Tackle win chains (possessions after)
│  └─ Defensive positioning insights
│
└─ Status: 18 tackles per player, 78% success typical

┌─ AERIAL DUEL EVENTS (29 recorded as "aerial lost") ═════════════════
│  Phase 1 ⏳ PARTIAL:
│  ├─ Identified in event data (separate from ground duels)
│  └─ Requires outcome linkage
│
│  Phase 2 (Planned):
│  ├─ Aerial dominance metric
│  ├─ Set piece aerial effectiveness
│  ├─ Header quality analysis
│  └─ Height/strength correlation
│
│  Phase 3 (Planned):
│  ├─ Aerial positioning patterns
│  ├─ Crossing effectiveness (aerials in box)
│  └─ Defensive aerial patterns
│
└─ Status: Low volume (~1 per match), needs special handling

┌─ TAKE-ON EVENTS (302 records) ════════════════════════════════════════
│  Phase 1 ✅ COMPLETE:
│  ├─ Take-on success rate
│  ├─ Regional breakdown (field thirds)
│  ├─ Box dribbles (into/in penalty area)
│  └─ Half analysis (own vs opponent)
│
│  Phase 2 (Planned):
│  ├─ Take-on consequence (shot, pass, lose ball)
│  ├─ Dribble distance traveled
│  ├─ Progressive dribbles (moving toward goal)
│  ├─ Defensive player count (1v1 vs crowded)
│  └─ Space creation via dribbles
│
│  Phase 3 (Planned):
│  ├─ Dribble skill rating
│  ├─ High-pressure dribbling (vs defensive intensity)
│  ├─ Dribble path analysis
│  └─ Time gained via progression
│
└─ Status: 12 take-ons per player, 75% success rate typical

┌─ FOUL EVENTS (486 records) ════════════════════════════════════════════
│  Phase 1 ✅ COMPLETE:
│  ├─ Total fouls committed
│  ├─ Foul type breakdown (dangerous, handball, penalty)
│  ├─ Regional concentration (field thirds)
│  ├─ Box fouls identification
│  └─ Discipline assessment
│
│  Phase 2 (Planned):
│  ├─ Foul consequence (card, free kick, penalty)
│  ├─ Tactical fouls vs reckless
│  ├─ Under-pressure fouls
│  ├─ Repeat offender detection
│  └─ Suspension risk calculation
│
│  Phase 3 (Planned):
│  ├─ Defensive style via fouls
│  ├─ Game state fouls (winning vs losing)
│  ├─ Opponent player fouling patterns
│  └─ Foul consequence outcomes
│
└─ Status: 6 fouls per player, discipline tracked

┌─ CARD EVENTS (46 records) ════════════════════════════════════════════
│  Phase 1 ⏳ PARTIAL:
│  ├─ Yellow/red card count
│  └─ Identified but not yet linked to fouls
│
│  Phase 2 (Planned):
│  ├─ Card cause analysis (foul, dive, dissent)
│  ├─ Card timing in season
│  ├─ Suspension risk tracking
│  ├─ Second yellow red detection
│  └─ Direct red analysis
│
│  Phase 3 (Planned):
│  ├─ Team discipline patterns
│  ├─ Referee bias detection
│  ├─ Impact on team performance (down to 10 men)
│  └─ Card accumulation trends
│
└─ Status: <1 card per player, needs event linking

┌─ GOALKEEPER EVENTS (133 records) ═════════════════════════════════════
│  Phase 1 ⏳ PARTIAL:
│  ├─ Save count (basic tracking)
│  └─ Identified types: saves, claims, punches, sweeps
│
│  Phase 2 (Planned):
│  ├─ Save by type (hands, feet, reflexes)
│  ├─ Shot faced analysis
│  ├─ Distribution accuracy (passes out)
│  ├─ Sweeper actions effectiveness
│  ├─ Cross claiming vs punching
│  └─ Distribution by foot
│
│  Phase 3 (Planned):
│  ├─ Expected goals conceded (xGC)
│  ├─ Shot stopping quality
│  ├─ Sweeper positioning effectiveness
│  ├─ Distribution value (possession retained)
│  └─ Command of area
│
└─ Status: ~3 GK actions per match, not yet aggregated

┌─ BALL CONTROL EVENTS (1,099 records) ═════════════════════════════════
│  Phase 1 ✅ COMPLETE:
│  ├─ Touch count & intensity
│  ├─ Touch accuracy (successful %)
│  ├─ Regional distribution (field zones)
│  ├─ Box touches (attacking pressure)
│  └─ Half-based presence
│
│  Phase 2 (Planned):
│  ├─ Touch type analysis (controlled, miscontrol)
│  ├─ Touch under pressure
│  ├─ First touch quality
│  ├─ Possession sequences
│  ├─ Turnover analysis
│  └─ Touch rhythm (spacing between touches)
│
│  Phase 3 (Planned):
│  ├─ Heat maps by touch type
│  ├─ Possession value per touch
│  ├─ Decision-making quality (next action)
│  ├─ Ball retention efficiency
│  └─ Space control via touches
│
└─ Status: 100+ touches per player, touch maps created

┌─ PRESSURE EVENTS (239 records) ═══════════════════════════════════════
│  Phase 1 ⏳ NOT YET:
│  ├─ Events identified but not aggregated
│  └─ Volume: ~6 pressure actions per team per match
│
│  Phase 2 (Planned):
│  ├─ Pressure intensity by zone
│  ├─ Pressure success rate (loses ball vs keeps)
│  ├─ High press vs low press distribution
│  ├─ Pressure timing effectiveness
│  └─ Distance from goal when applying pressure
│
│  Phase 3 (Planned):
│  ├─ Pressing line organization
│  ├─ Counter-pressing effectiveness
│  ├─ Zone-based pressing patterns
│  └─ Tactical pressing instructions
│
└─ Status: Identified, queued for Phase 2

┌─ INTERCEPTION EVENTS (228 records) ═════════════════════════════════
│  Phase 1 ⏳ NOT YET:
│  ├─ Events identified but not aggregated
│  └─ Volume: ~6 interceptions per team per match
│
│  Phase 2 (Planned):
│  ├─ Interception locations (field thirds)
│  ├─ Interception consequence (possession, turnover)
│  ├─ Anticipatory interceptions
│  ├─ Reading of game
│  └─ Defensive positioning effectiveness
│
│  Phase 3 (Planned):
│  ├─ Interception heat maps
│  ├─ Passing lane identification from interceptions
│  ├─ Defensive intelligence scoring
│  └─ Predictive interception modeling
│
└─ Status: Identified, queued for Phase 2

┌─ BALL RECOVERY EVENTS (92 records) ════════════════════════════════════
│  Phase 1 ⏳ NOT YET:
│  ├─ Events identified but not aggregated
│  └─ Volume: ~2-3 recoveries per player per match
│
│  Phase 2 (Planned):
│  ├─ Recovery locations (defensive territory)
│  ├─ Recovery consequence (possession outcome)
│  ├─ Transition efficiency (recovery → shot within 10s)
│  ├─ Countess press success
│  └─ Pressing intensity (recoveries initiated)
│
│  Phase 3 (Planned):
│  ├─ Counter-attack trigger analysis
│  ├─ Possession duration after recovery
│  ├─ Transition value scoring
│  └─ Team pressing patterns
│
└─ Status: Identified, queued for Phase 2

┌─ CLEARANCE EVENTS (398 records) ══════════════════════════════════════
│  Phase 1 ⏳ NOT YET:
│  ├─ Events identified but not aggregated
│  └─ Volume: ~10 clearances per team per match
│
│  Phase 2 (Planned):
│  ├─ Clearance locations (box pressure)
│  ├─ Clearance type (feet, head, volley)
│  ├─ Clearance consequence (possession loss %)
│  ├─ Defensive load indicator
│  └─ Set pieces defended
│
│  Phase 3 (Planned):
│  ├─ Clearance effectiveness vs pressure
│  ├─ Zone-based clearance patterns
│  ├─ Defensive positioning from clearances
│  └─ Transition risk (clearance to attack)
│
└─ Status: Identified, queued for Phase 2

┌─ BLOCKED PASS/SHOT EVENTS (331 + 118 records) ════════════════════════
│  Phase 1 ⏳ NOT YET:
│  ├─ Events identified but not aggregated
│  └─ Volume: ~12 blocks per team per match
│
│  Phase 2 (Planned):
│  ├─ Block locations (box defense)
│  ├─ Block types (pass vs shot)
│  ├─ Defensive positioning effectiveness
│  ├─ Shot-stopping via blocks
│  └─ Block distance from goal
│
│  Phase 3 (Planned):
│  ├─ Block heat maps
│  ├─ Defensive line compactness via blocks
│  ├─ Shot prevention value
│  └─ Defensive intensity zones
│
└─ Status: Identified, queued for Phase 2
```

---

## Enrichment Capability by Dimension

### Spatial Analytics
```
✅ Implemented        Planned               Future
├─ Field thirds       ├─ Hot spots           ├─ Positional heatmaps
├─ Halves            ├─ Density maps        ├─ Influence zones
├─ Penalty boxes     ├─ Pass maps           ├─ Control areas
└─ Box regions       └─ Action zones        └─ Transition zones
```

### Temporal Analytics
```
✅ Implemented        Planned               Future
├─ Event counts       ├─ Sequences           ├─ Time series trends
├─ Per-match totals   ├─ Event chains        ├─ Form analysis
├─ Intensity (count)  ├─ Timing patterns     ├─ Fatigue detection
└─ Per-90 metrics     └─ Game phases         └─ Match context
```

### Quality Metrics
```
✅ Implemented        Planned               Future
├─ Success rates      ├─ Expected metrics    ├─ Performance indices
├─ Accuracy %         ├─ Quality scoring     ├─ Position benchmarks
├─ Efficiency         ├─ Difficulty adjust   ├─ Pressure adjustments
└─ Conversion %       └─ Context weighting   └─ Composite ratings
```

### Context Dimensions
```
✅ Implemented        Planned               Future
├─ Set piece/open     ├─ Pressure level      ├─ Formation context
├─ By event type      ├─ Opponent level      ├─ Match state
├─ Location-based     ├─ Game phases         ├─ Player positioning
└─ Direction-based    └─ Weather/conditions  └─ Tactical setup
```

---

## Data Volume Snapshot

```
Total Event Records: 51,000+ (across all types)

Most Common Events (implementable immediately):
├─ Pass: 8,967 (17.6%) ✅ Rich analysis pipeline
├─ Out: 1,122 (2.2%)
├─ Ball Control: 1,099 (2.2%) ✅ Touch analysis ready
├─ Carries: 733 (1.4%) ✅ Dribble enrichment ready
├─ Duel: 612 (1.2%) ✅ Success tracking ready
├─ Chance Missed: 522 (1.0%)
├─ Foul: 486 (1.0%) ✅ Discipline analysis ready
├─ Clearance: 398 (0.8%)
├─ Blocked Pass: 331 (0.6%)
├─ Tackle: 325 (0.6%) ✅ Defensive metrics ready
├─ Take-on: 302 (0.6%) ✅ Dribble efficiency ready
└─ Pressure: 239 (0.5%) (Queued for Phase 2)

Low Volume (Special Handling):
├─ Goalkeeper: 133 (0.3%)
├─ Ball Recovery: 92 (0.2%)
├─ Card: 46 (0.1%) (Needs foul linkage)
├─ Aerial Lost: 29 (0.1%) (Partial data)
└─ Shot: 212 (0.4%) ✅ Rich analysis pipeline
```

---

## Enrichment Complexity vs Value Matrix

```
                            HIGH VALUE
                                 ↑
                                 │
        ╔════════════════════════╬════════════════════════╗
        ║  Expected Goals (xG)   │  Regional Analytics    ║
        ║  Expected Assists (xA) │  Pass Quality/Type     ║
        ║  Heat Maps             │  Tactical Patterns     ║
        ║  Pressure Networks     │  Player Influence      ║
        ║  Transition Value      │  Success Rate Analysis ║
        ╠════════════════════════╬════════════════════════╣
        ║ Dive/Dissent Cards     │  Event Sequences       ║
        ║ Foul Outcome Linking   │  Expected Metrics      ║
        ║ Keeper Distribution    │  Machine Learning      ║
        ║ Aerial Duel Separation │  Composite Indices     ║
        ╚════════════════════════╬════════════════════════╝
                                 │
        LOW                    COMPLEXITY                HIGH
        COMPLEXITY                                     COMPLEXITY
```

---

## Implementation Phases Summary

| Phase | Status | Events | Capabilities | Timeline |
|-------|--------|--------|--------------|----------|
| **Phase 1** | ✅ DONE | 7 types | Regional, types, context, success rates | Implemented |
| **Phase 2** | ⏳ PLANNED | 5 more types | Event linking, sequences, pressure, transitions | 2-3 weeks |
| **Phase 3** | 📋 QUEUED | All types | Heat maps, performance indices, xG/xA integration | 3-4 weeks |
| **Phase 4** | 🔮 FUTURE | ML Features | Time series, clustering, predictions | Post-Phase 3 |

---

## Recommended Quick Wins

**Highest ROI / Lowest Effort:**

1. **✅ Implement Ball Recovery aggregation** (92 events, 2 hours)
   - Location breakdown, consequence tracking
   - Enables transition analysis

2. **✅ Implement Interception aggregation** (228 events, 2 hours)
   - Regional distribution, defensive intelligence
   - Enables reading-of-game analysis

3. **✅ Link Card → Foul events** (2-3 hours)
   - Identify which fouls led to cards
   - Enables discipline pattern analysis

4. **✅ Implement Clearance aggregation** (398 events, 2 hours)
   - Box pressure indicator, defensive load
   - Enables situation analysis

5. **✅ Split Aerial vs Ground Duels** (1 hour)
   - Currently mixed in duel events
   - Enables position-specific analysis

**Total estimated effort for all quick wins: 10-12 hours**  
**Value gained: 25+ new analytics endpoints**

---

## Architecture Readiness

```
✅ Data Access Layer:
   ├─ MongoDB find() working reliably
   ├─ Motor async driver configured
   ├─ Document structure understood

✅ Processing Layer:
   ├─ FieldZones class (regions)
   ├─ QualifierExtractor class (Opta data)
   ├─ Success rate tracking
   └─ Aggregation patterns established

✅ Caching Layer:
   ├─ Redis 300s TTL
   ├─ Cache key patterns
   └─ Hit rate optimization ready

✅ API Layer:
   ├─ RESTful endpoint pattern
   ├─ FastAPI integration
   ├─ Response formatting
   └─ Error handling

Ready for scale-up to 50+ event types with minimal additional work.
```

