# Match Visualizations Implementation Guide

## Overview

Scout Pro now includes three professional-grade match analytics visualizations:
1. **Shot Map** - Visualize shooting locations and expected goals (xG)
2. **Heat Maps** - Analyze player/team activity density on the pitch
3. **Pass Networks** - Show player connections and passing patterns

## Components Created

### 1. PitchOverlay (`components/visualizations/PitchOverlay.tsx`)
**Base component** providing:
- Football field rendering with proper markings
- Normalized coordinate system (0-100 range)
- Reusable foundation for all visualizations
- Click event handling for interactive features

**Features:**
- SVG-based pitch drawing with accurate field markings
- Center circle, penalty areas, goal areas
- Configurable dimensions and colors
- Flexible for overlaying custom data

### 2. ShotMap (`components/visualizations/ShotMap.tsx`)
**Visualizes shots on the pitch** with:
- Color-coded outcomes (🟢 Goal, 🔴 Miss)
- Bubble size proportional to xG value
- Interactive hover details
- Shot information: player name, xG value, body part, type

**API Endpoint:**
```typescript
getMatchShotMap(matchId: string)
```

**Data Structure:**
```typescript
{
  id: string;
  player_id: string;
  player_name: string;
  x: number;           // 0-100 normalized coordinate
  y: number;           // 0-100 normalized coordinate
  is_goal: boolean;
  xg: number;          // Expected Goals value
  is_successful?: boolean;
  body_part?: string;  // foot, head, etc.
  shot_type?: string;  // open_play, penalty, etc.
}
```

### 3. HeatMap (`components/visualizations/HeatMap.tsx`)
**Shows activity intensity zones** with:
- Grid-based visualization (10x10 cells)
- Color gradient (cold/blue → hot/red)
- Cell-by-cell intensity metrics
- Event count per zone
- Team and player-specific filtering

**API Endpoint:**
```typescript
getMatchHeatMap(
  matchId: string, 
  teamId?: string, 
  playerId?: string
)
```

**Data Structure:**
```typescript
{
  x: number;           // 0-100 normalized coordinate
  y: number;
  intensity: number;   // Aggregated event count/value
  count?: number;      // Raw event count
  player_name?: string;
}
```

### 4. PassNetwork (`components/visualizations/PassNetwork.tsx`)
**Visualizes passing relationships** with:
- Node size = touch count
- Line thickness = pass count
- Line color = pass accuracy
- Interactive player hover details
- Connection-specific statistics

**API Endpoint:**
```typescript
getMatchPassMap(matchId: string, teamId?: string)
```

**Data Structure:**
```typescript
{
  players: [{
    player_id: string;
    player_name: string;
    x: number;           // 0-100 position on pitch
    y: number;
    touches: number;
    passes: number;
  }];
  connections: [{
    from_player_id: string;
    to_player_id: string;
    passes: number;
    accuracy: number;    // 0-1 percentage
  }];
}
```

## Integration Points

### Add to Match Detail Page

```typescript
import { MatchDetailWithVisualizations } from './components/MatchDetailWithVisualizations';

// In your match detail view:
<MatchDetailWithVisualizations
  matchId={selectedMatch.id}
  homeTeam={selectedMatch.homeTeam}
  awayTeam={selectedMatch.awayTeam}
  homeScore={selectedMatch.homeScore}
  awayScore={selectedMatch.awayScore}
  onBack={() => setSelectedMatch(null)}
/>
```

### Add Individual Visualizations

```typescript
import { ShotMap, HeatMap, PassNetwork } from './components/visualizations';

// Shot Map
<ShotMap matchId={matchId} width={800} height={600} />

// Heat Map
<HeatMap matchId={matchId} teamId={teamId} title="Player Activity" />

// Pass Network  
<PassNetwork matchId={matchId} teamId={teamId} />
```

## API Methods (in `services/api.ts`)

All visualization data is fetched through these endpoints:

```typescript
// Shot map data
async getMatchShotMap(matchId: string)

// Heat map data  
async getMatchHeatMap(matchId: string, teamId?: string, playerId?: string)

// Pass network data
async getMatchPassMap(matchId: string, teamId?: string)

// Additional endpoints
async getMatchPossession(matchId: string)
async getMatchPressureMap(matchId: string, teamId?: string)

// Player comparison
async getPlayerComparison(playerIds: string[])
async getPlayerPercentiles(playerId: string, position?: string)
```

## Backend API Requirements

These endpoints should exist or be created in your API Gateway:

```
GET /matches/{id}/shots-map              → ShotEvent[]
GET /matches/{id}/heat-map?team_id=X     → HeatMapData[]
GET /matches/{id}/pass-map?team_id=X     → PassMapData
GET /matches/{id}/possession             → PossessionData
GET /matches/{id}/pressure-map?team_id=X → PressureMapData
POST /players/compare                    → PlayerComparisonData
GET /players/{id}/percentiles            → PercentileData
```

## Features & Interactions

### Shot Map
- **Click shot**: Get player details (if callback provided)
- **Hover**: See xG value and shot details
- **Legend**: Distinguish goals from missed shots
- **Size coding**: Larger circles = higher xG value

### Heat Map
- **Hover cell**: See event count and intensity
- **Color scale**: Blue (low) → Red (high activity)
- **Grid-based**: Divides pitch into 10x10 zones
- **Team filtering**: View home/away team activity separately

### Pass Network  
- **Hover player**: See touches and pass connections
- **Hover line**: See pass count and accuracy
- **Node size**: Proportional to player touches
- **Line color**: Green (90%+ accuracy) → Red (poor accuracy)
- **Interactive**: Click to filter or compare players

## Styling & Customization

All components use Tailwind CSS and follow Scout Pro's design system:
- Dark theme (slate-800/900 backgrounds)
- Blue/green accent colors
- Responsive layouts
- Hover states and transitions

### Customize Pitch Colors

```typescript
const config: PitchConfig = {
  width: 800,
  height: 600,
  padding: 20,
  pitchColor: '#1a5d1a',      // Dark green
  lineColor: '#ffffff',         // White lines
};

<PitchOverlay config={config}>
  {/* Your visualization */}
</PitchOverlay>
```

## Performance Considerations

1. **Data loading**: Components show loading spinner while fetching
2. **Error handling**: Graceful error messages if API fails
3. **Responsive design**: Works on desktop and tablet
4. **SVG optimization**: Uses SVG for scalable graphics
5. **Hover optimization**: Efficient hover state management

## Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Requires SVG support
- No external canvas libraries needed
- Responsive to viewport changes

## Next Steps

1. **Wire up to MatchCentre**: Import and add to match detail view
2. **Test with real data**: Ensure backend APIs return correct data
3. **Add to routing**: Create new route/tab for detailed match analysis
4. **Enhance with filters**: Add team/player filtering UI
5. **Add live updates**: Integrate WebSocket for live match tracking

## Troubleshooting

### Shot Map not loading
- Check: API endpoint `/matches/{id}/shots-map` exists
- Verify: Response format matches expected ShotEvent[] structure
- Test: `curl http://localhost:3001/api/v2/matches/{id}/shots-map`

### Heat Map showing empty
- Check: Events have valid x,y coordinates (0-100 range)
- Verify: At least one event exists for the match
- Debug: Check browser console for API errors

### Pass Network not rendering
- Check: Players have valid position coordinates
- Verify: Connections reference valid player IDs
- Test: Ensure response includes both `players` and `connections` arrays

## Files Created/Modified

```
NEW:
  frontend/src/components/visualizations/
    ├── PitchOverlay.tsx          (Base component)
    ├── ShotMap.tsx               (Shot visualization)
    ├── HeatMap.tsx               (Activity heatmap)
    ├── PassNetwork.tsx           (Pass connections)
    └── index.ts                  (Barrel export)
  
  frontend/src/components/
    └── MatchDetailWithVisualizations.tsx (Integrated view)

MODIFIED:
  frontend/src/services/api.ts   (Added visualization API methods)
```

## Expected Data Output Examples

### ShotMap Example
```json
[
  {
    "id": "shot-001",
    "player_id": "p123",
    "player_name": "Cristiano Ronaldo",
    "x": 85,
    "y": 50,
    "is_goal": true,
    "xg": 0.45,
    "body_part": "right_foot",
    "shot_type": "open_play"
  }
]
```

### HeatMap Example
```json
[
  {
    "x": 50,
    "y": 40,
    "intensity": 15,
    "count": 12,
    "player_name": "Player A"
  }
]
```

### PassNetwork Example
```json
{
  "players": [
    {
      "player_id": "p1",
      "player_name": "Keeper",
      "x": 10,
      "y": 50,
      "touches": 45,
      "passes": 40
    }
  ],
  "connections": [
    {
      "from_player_id": "p1",
      "to_player_id": "p2",
      "passes": 15,
      "accuracy": 0.93
    }
  ]
}
```

---

## Status: ✅ IMPLEMENTATION COMPLETE

All visualization components are ready for integration. Test with real match data and ensure backend APIs return correctly formatted responses.
