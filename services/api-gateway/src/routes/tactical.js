/**
 * Tactical Routes - Tactical pattern analysis endpoints
 */
const express = require('express');
const router = express.Router();

const {
  ensureSuccess,
  requestJson,
  unwrapPayload,
} = require('../utils/serviceClient');

const matchServiceUrl = (process.env.MATCH_SERVICE_URL || 'http://match-service:8000').replace(/\/$/, '');
const analyticsServiceUrl = (process.env.ANALYTICS_SERVICE_URL || 'http://analytics-service:8012').replace(/\/$/, '');

const tacticalPatterns = [
  {
    id: 'pattern-1',
    name: 'High Press Recovery',
    type: 'defensive',
    description: 'Team regains possession within 5 seconds of losing it in the attacking third',
    successRate: 0.72,
    frequency: 18,
    teams: ['Liverpool', 'Manchester City', 'Arsenal'],
    keyPlayers: ['Rodri', 'Declan Rice', 'Alexis Mac Allister'],
    formation: '4-3-3',
    zone: 'attacking_third'
  },
  {
    id: 'pattern-2',
    name: 'Quick Counter Attack',
    type: 'attacking',
    description: 'Transition from defense to shot on goal in under 10 seconds',
    successRate: 0.34,
    frequency: 12,
    teams: ['Real Madrid', 'Newcastle', 'Bayer Leverkusen'],
    keyPlayers: ['Vinícius Jr.', 'Alexander Isak', 'Florian Wirtz'],
    formation: '4-4-2',
    zone: 'transition'
  },
  {
    id: 'pattern-3',
    name: 'Positional Play Build-Up',
    type: 'possession',
    description: 'Structured build-up through thirds with positional rotations',
    successRate: 0.68,
    frequency: 45,
    teams: ['Manchester City', 'Barcelona', 'Bayern Munich'],
    keyPlayers: ['Rodri', 'Pedri', 'Joshua Kimmich'],
    formation: '4-3-3',
    zone: 'midfield'
  },
  {
    id: 'pattern-4',
    name: 'Wing Overload',
    type: 'attacking',
    description: 'Creating numerical superiority on the flanks through overlaps and underlaps',
    successRate: 0.58,
    frequency: 22,
    teams: ['Arsenal', 'Manchester City', 'Real Madrid'],
    keyPlayers: ['Bukayo Saka', 'Phil Foden', 'Vinícius Jr.'],
    formation: '4-3-3',
    zone: 'wide_areas'
  },
  {
    id: 'pattern-5',
    name: 'Low Block Defence',
    type: 'defensive',
    description: 'Compact defensive shape with two banks of four, denying space in the box',
    successRate: 0.81,
    frequency: 30,
    teams: ['Atlético Madrid', 'Juventus', 'Inter Milan'],
    keyPlayers: ['Stefan Savić', 'Federico Valverde', 'Alessandro Bastoni'],
    formation: '4-4-2',
    zone: 'defensive_third'
  },
  {
    id: 'pattern-6',
    name: 'Set Piece Routine - Corner',
    type: 'set_piece',
    description: 'Near post flick-on or back post delivery pattern from corners',
    successRate: 0.12,
    frequency: 8,
    teams: ['Liverpool', 'Arsenal', 'Brighton'],
    keyPlayers: ['Virgil van Dijk', 'Gabriel', 'Lewis Dunk'],
    formation: 'set_piece',
    zone: 'penalty_area'
  }
];

const tacticalFormations = [
  {
    id: '4-3-3',
    name: '4-3-3',
    popularity: 34,
    effectiveness: 87,
    topTeams: ['Manchester City', 'Barcelona', 'Arsenal']
  },
  {
    id: '4-2-3-1',
    name: '4-2-3-1',
    popularity: 28,
    effectiveness: 84,
    topTeams: ['Bayern Munich', 'Borussia Dortmund', 'Chelsea']
  },
  {
    id: '3-5-2',
    name: '3-5-2',
    popularity: 18,
    effectiveness: 82,
    topTeams: ['Inter Milan', 'Atalanta', 'Juventus']
  },
  {
    id: '4-4-2',
    name: '4-4-2',
    popularity: 12,
    effectiveness: 79,
    topTeams: ['Atlético Madrid', 'Juventus', 'Real Sociedad']
  },
  {
    id: '3-4-3',
    name: '3-4-3',
    popularity: 8,
    effectiveness: 85,
    topTeams: ['Brighton', 'Bayer Leverkusen', 'Sporting CP']
  }
];

const tacticalMovements = [
  {
    id: 'movement-1',
    player: 'LW',
    from: [20, 28],
    to: [78, 24],
    type: 'run',
    success: true,
    formation: '4-3-3',
    phase: 'attack'
  },
  {
    id: 'movement-2',
    player: 'CM',
    from: [42, 60],
    to: [63, 44],
    type: 'pass',
    success: true,
    formation: '4-3-3',
    phase: 'transition'
  },
  {
    id: 'movement-3',
    player: 'RW',
    from: [66, 68],
    to: [74, 34],
    type: 'dribble',
    success: false,
    formation: '4-3-3',
    phase: 'attack'
  },
  {
    id: 'movement-4',
    player: 'DM',
    from: [48, 55],
    to: [56, 42],
    type: 'pass',
    success: true,
    formation: '4-2-3-1',
    phase: 'transition'
  },
  {
    id: 'movement-5',
    player: 'RWB',
    from: [74, 52],
    to: [82, 28],
    type: 'run',
    success: true,
    formation: '3-5-2',
    phase: 'attack'
  },
  {
    id: 'movement-6',
    player: 'CB',
    from: [50, 72],
    to: [44, 56],
    type: 'pass',
    success: true,
    formation: '4-4-2',
    phase: 'defense'
  }
];

const tacticalAnalytics = {
  pressingTriggers: [
    { label: 'Ball Loss in Final Third', value: 87, trend: 'up' },
    { label: 'Goalkeeper Distribution', value: 64, trend: 'stable' },
    { label: 'Wide Area Possession', value: 43, trend: 'down' }
  ],
  buildupPatterns: [
    { label: 'Short Passing', value: 78, trend: 'up' },
    { label: 'Long Ball', value: 23, trend: 'down' },
    { label: 'Wing Play', value: 56, trend: 'stable' }
  ],
  defensiveActions: [
    { label: 'High Press Success', value: 67, suffix: '%' },
    { label: 'Interceptions', value: 89, suffix: '' },
    { label: 'Tackles Won', value: 73, suffix: '%' }
  ]
};

function hasConcreteTeamContext(match) {
  const homeTeamId = String(match?.home_team_id || match?.homeTeamId || '').trim();
  const awayTeamId = String(match?.away_team_id || match?.awayTeamId || '').trim();
  return Boolean(homeTeamId && awayTeamId && homeTeamId !== '0' && awayTeamId !== '0');
}

function pickLiveMatchWithContext(liveMatches, matchId) {
  const normalizedMatchId = String(matchId || '').trim();
  if (!Array.isArray(liveMatches) || liveMatches.length === 0) {
    return null;
  }

  if (normalizedMatchId) {
    return liveMatches.find((candidate) => String(candidate?.id || '').trim() === normalizedMatchId && hasConcreteTeamContext(candidate))
      || liveMatches.find((candidate) => String(candidate?.id || '').trim() === normalizedMatchId)
      || null;
  }

  return liveMatches.find((candidate) => hasConcreteTeamContext(candidate))
    || liveMatches[0]
    || null;
}

async function loadSequenceInsights(matchId) {
  try {
    let liveMatch = null;

    if (matchId) {
      const payload = ensureSuccess(
        await requestJson(matchServiceUrl, `/api/v2/matches/${matchId}`),
        'Failed to fetch tactical match context'
      );
      liveMatch = unwrapPayload(payload);

      if (!hasConcreteTeamContext(liveMatch)) {
        const liveMatchesPayload = ensureSuccess(
          await requestJson(matchServiceUrl, '/api/v2/matches/live'),
          'Failed to fetch live matches for tactical context'
        );
        liveMatch = pickLiveMatchWithContext(unwrapPayload(liveMatchesPayload) || [], matchId) || liveMatch;
      }
    } else {
      const payload = ensureSuccess(
        await requestJson(matchServiceUrl, '/api/v2/matches/live'),
        'Failed to fetch live matches for tactical context'
      );
      liveMatch = pickLiveMatchWithContext(unwrapPayload(payload) || []);
    }

    if (!liveMatch?.id) {
      return null;
    }

    return ensureSuccess(
      await requestJson(analyticsServiceUrl, `/api/v2/analytics/sequences/${liveMatch.id}`, { timeoutMs: 15000 }),
      'Failed to fetch tactical sequence insights'
    );
  } catch (error) {
    console.error('Tactical live sequence analysis error:', error);
    return null;
  }
}

const zoneLabels = {
  attacking_third: 'Final Third',
  transition: 'Transition Lane',
  midfield: 'Central Midfield',
  wide_areas: 'Wide Areas',
  defensive_third: 'Defensive Third',
  penalty_area: 'Penalty Area'
};

// ─── MongoDB-backed helpers (fall back to static on any error) ───────────────

async function buildRealHeatmap(db) {
  if (!db) return buildHeatmap(tacticalPatterns);
  try {
    const pipeline = [
      { $match: {
        location: { $ne: null },
        type_name: { $nin: ['starting xi', 'half start', 'half end', 'unknown', 'formation', 'lineup'] },
      }},
      { $addFields: {
        locX: {
          $cond: [
            { $isArray: '$location' },
            { $arrayElemAt: ['$location', 0] },
            '$location.x',
          ],
        },
      }},
      { $match: { locX: { $ne: null } }},
      { $addFields: {
        zone: {
          $switch: {
            branches: [
              { case: { $lt: ['$locX', 33] }, then: 'defensive_third' },
              { case: { $lt: ['$locX', 66] }, then: 'midfield' },
              { case: { $lt: ['$locX', 83] }, then: 'attacking_third' },
            ],
            default: 'penalty_area',
          },
        },
      }},
      { $group: {
        _id: '$zone',
        total: { $sum: 1 },
        goals: { $sum: { $cond: [{ $eq: ['$is_goal', true] }, 1, 0] } },
        shots: { $sum: { $cond: [{ $in: ['$type_name', ['shot', 'chance_missed', 'goal_confirmed']] }, 1, 0] } },
      }},
    ];
    const results = await db.collection('match_events').aggregate(pipeline).toArray();
    if (!results.length) return buildHeatmap(tacticalPatterns);

    const maxTotal = Math.max(...results.map(r => r.total), 1);
    const zoneDisplay = {
      defensive_third: 'Defensive Third',
      midfield: 'Central Midfield',
      attacking_third: 'Final Third',
      penalty_area: 'Penalty Area',
    };
    return results
      .map(r => ({
        zone: zoneDisplay[r._id] || r._id,
        intensity: Math.max(15, Math.min(100, Math.round((r.total / maxTotal) * 100))),
        effectiveness: r.shots > 0 ? Math.round((r.goals / r.shots) * 100) : 0,
        event_count: r.total,
        shots: r.shots,
        goals: r.goals,
        data_source: 'opta_f24',
      }))
      .sort((a, b) => b.intensity - a.intensity);
  } catch (err) {
    console.error('Real heatmap error:', err);
    return buildHeatmap(tacticalPatterns);
  }
}

async function buildRealAnalytics(db) {
  if (!db) return tacticalAnalytics;
  try {
    const eventAgg = await db.collection('match_events').aggregate([
      { $group: { _id: '$type_name', count: { $sum: 1 } } },
    ]).toArray();
    const counts = {};
    eventAgg.forEach(e => { if (e._id) counts[e._id] = e.count; });
    const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1;
    const pct = (num, scale) => Math.max(0, Math.min(100, Math.round((num / total) * scale)));

    const passes = counts['pass'] || 0;
    const recoveries = (counts['ball_recovery'] || 0) + (counts['recovery'] || 0);
    const interceptions = counts['interception'] || 0;
    const tackles = counts['tackle'] || 0;
    const dribbles = (counts['dribble'] || 0) + (counts['take_on'] || 0);
    const clearances = counts['clearance'] || 0;
    const keepers = counts['goalkeeper'] || 0;
    const totalTackles = tackles + (counts['challenge'] || 0);

    return {
      pressingTriggers: [
        { label: 'Ball Recovery Rate', value: pct(recoveries, 2000), trend: 'up' },
        { label: 'Keeper Distribution', value: pct(keepers, 3000), trend: 'stable' },
        { label: 'Wide Area Actions', value: pct(dribbles, 3000), trend: 'stable' },
      ],
      buildupPatterns: [
        { label: 'Short Passing', value: Math.min(100, Math.round(passes / (total * 0.3))), trend: 'up' },
        { label: 'Long Ball / Clearance', value: pct(clearances, 2000), trend: 'down' },
        { label: 'Dribble & Take-On', value: pct(dribbles, 2500), trend: 'stable' },
      ],
      defensiveActions: [
        { label: 'Press Success', value: pct(recoveries + interceptions + tackles, 2500), suffix: '%' },
        { label: 'Interceptions', value: interceptions, suffix: '' },
        { label: 'Tackles Won', value: totalTackles > 0 ? Math.round(tackles / totalTackles * 100) : 0, suffix: '%' },
      ],
      event_totals: {
        passes,
        shots: (counts['shot'] || 0) + (counts['chance_missed'] || 0),
        tackles,
        interceptions,
        goals: counts['goal_confirmed'] || 0,
        total_events: total,
      },
      data_source: 'opta_f24',
    };
  } catch (err) {
    console.error('Real analytics error:', err);
    return tacticalAnalytics;
  }
}

async function buildRealFormations(db) {
  if (!db) return tacticalFormations;
  try {
    const matchesWithF9 = await db.collection('matches')
      .find({ 'f9_summary.teams': { $exists: true } }, { projection: { 'f9_summary.teams': 1 } })
      .toArray();
    const formationCounts = {};
    matchesWithF9.forEach(match => {
      (match.f9_summary?.teams || []).forEach(team => {
        if (team.formation) {
          formationCounts[team.formation] = (formationCounts[team.formation] || 0) + 1;
        }
      });
    });
    if (!Object.keys(formationCounts).length) return tacticalFormations;
    const total = Object.values(formationCounts).reduce((a, b) => a + b, 0) || 1;
    return Object.entries(formationCounts)
      .sort(([, a], [, b]) => b - a)
      .map(([id, count]) => ({
        id,
        name: id,
        popularity: Math.round(count / total * 100),
        effectiveness: null,
        topTeams: [],
        data_source: 'opta_f9',
      }));
  } catch (err) {
    console.error('Real formations error:', err);
    return tacticalFormations;
  }
}
// ─────────────────────────────────────────────────────────────────────────────

function buildHeatmap(patterns) {
  const zoneBuckets = new Map();

  patterns.forEach((pattern) => {
    const zoneKey = pattern.zone || 'midfield';
    const bucket = zoneBuckets.get(zoneKey) || {
      zone: zoneLabels[zoneKey] || zoneKey,
      totalFrequency: 0,
      totalSuccess: 0,
      count: 0
    };

    bucket.totalFrequency += Number(pattern.frequency) || 0;
    bucket.totalSuccess += Number(pattern.successRate) || 0;
    bucket.count += 1;
    zoneBuckets.set(zoneKey, bucket);
  });

  return Array.from(zoneBuckets.values())
    .map((bucket) => ({
      zone: bucket.zone,
      intensity: Math.max(15, Math.min(100, Math.round(bucket.totalFrequency * 1.8))),
      effectiveness: Math.round((bucket.totalSuccess / Math.max(1, bucket.count)) * 100)
    }))
    .sort((left, right) => right.intensity - left.intensity);
}

function filterMovements(formation, phase) {
  return tacticalMovements.filter((movement) => {
    if (formation && movement.formation !== formation) {
      return false;
    }

    if (phase && movement.phase !== phase) {
      return false;
    }

    return true;
  });
}

// GET /api/tactical/patterns
router.get('/patterns', (req, res) => {
  res.json(tacticalPatterns);
});

// GET /api/tactical/patterns/:id
router.get('/patterns/:id', (req, res) => {
  const pattern = tacticalPatterns.find(p => p.id === req.params.id);
  if (!pattern) {
    return res.status(404).json({ error: 'Pattern not found' });
  }
  res.json(pattern);
});

// GET /api/tactical/formations  — real F9 formations, fallback to static
router.get('/formations', async (req, res) => {
  res.json(await buildRealFormations(req.app.locals.db));
});

// GET /api/tactical/movements
router.get('/movements', (req, res) => {
  const { formation, phase } = req.query;
  res.json(filterMovements(formation, phase));
});

// GET /api/tactical/heatmap  — real F24 event coordinates, fallback to static
router.get('/heatmap', async (req, res) => {
  res.json(await buildRealHeatmap(req.app.locals.db));
});

// GET /api/tactical/analytics  — real F24 event counts, fallback to static
router.get('/analytics', async (req, res) => {
  res.json(await buildRealAnalytics(req.app.locals.db));
});

// GET /api/tactical/overview  — merged response with all real data
router.get('/overview', async (req, res) => {
  const { formation, phase, matchId } = req.query;
  const db = req.app.locals.db;

  const [sequenceInsights, heatmap, analytics, formations] = await Promise.all([
    loadSequenceInsights(matchId),
    buildRealHeatmap(db),
    buildRealAnalytics(db),
    buildRealFormations(db),
  ]);

  res.json({
    patterns: tacticalPatterns,
    formations,
    movements: filterMovements(formation, phase),
    heatmap,
    analytics,
    sequenceInsights,
  });
});

// GET /api/tactical  (root)
router.get('/', async (req, res) => {
  const db = req.app.locals.db;
  const [sequenceInsights, heatmap, analytics, formations] = await Promise.all([
    loadSequenceInsights(req.query.matchId),
    buildRealHeatmap(db),
    buildRealAnalytics(db),
    buildRealFormations(db),
  ]);
  res.json({
    patterns: tacticalPatterns,
    formations,
    movements: filterMovements(req.query.formation, req.query.phase),
    heatmap,
    analytics,
    sequenceInsights,
  });
});

module.exports = router;
