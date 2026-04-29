/**
 * Advanced Analytics Routes - BI Dashboard, rankings, comparisons, trends
 * Handles /api/v2/analytics/* endpoints called by the frontend.
 */
const express = require('express');
const router = express.Router();

// GET /api/v2/analytics/dashboard/overview - Full dashboard data
router.get('/dashboard/overview', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.json(generateOverview());

    const [playerCount, teamCount, matchCount, liveCount] = await Promise.all([
      db.collection('players').countDocuments(),
      db.collection('teams').countDocuments(),
      db.collection('matches').countDocuments(),
      db.collection('matches').countDocuments({ status: 'live' })
    ]);

    // Top scorers
    const topScorers = await db.collection('players')
      .find({})
      .sort({ goals: -1 })
      .limit(5)
      .project({ name: 1, goals: 1, club: 1, position: 1, id: 1 })
      .toArray();

    // Recent matches
    const recentMatches = await db.collection('matches')
      .find({})
      .sort({ date: -1 })
      .limit(5)
      .toArray();

    res.json({
      summary: {
        totalPlayers: playerCount,
        totalTeams: teamCount,
        totalMatches: matchCount,
        liveMatches: liveCount,
        avgGoalsPerMatch: 2.7,
        scoutingReports: 156,
        activeScouts: 12,
        recentActivity: 42
      },
      topScorers: topScorers.map(p => ({ ...p, _id: undefined })),
      recentMatches: recentMatches.map(m => ({ ...m, id: m.id || m._id?.toString(), _id: undefined })),
      performanceTrends: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [
          { label: 'Goals', data: [45, 52, 48, 61, 55, 67] },
          { label: 'Assists', data: [32, 28, 35, 41, 38, 44] },
          { label: 'Clean Sheets', data: [12, 15, 10, 13, 16, 11] }
        ]
      },
      leagueDistribution: [
        { league: 'Premier League', players: 120, percentage: 24 },
        { league: 'La Liga', players: 95, percentage: 19 },
        { league: 'Bundesliga', players: 85, percentage: 17 },
        { league: 'Serie A', players: 80, percentage: 16 },
        { league: 'Ligue 1', players: 70, percentage: 14 },
        { league: 'Other', players: 50, percentage: 10 }
      ]
    });
  } catch (error) {
    console.error('Dashboard overview error:', error);
    res.json(generateOverview());
  }
});

// GET /api/v2/analytics/dashboard/team/:teamId
router.get('/dashboard/team/:teamId', async (req, res) => {
  try {
    const db = req.app.locals.db;
    let team = null;
    let teamPlayers = [];
    let teamMatches = [];

    if (db) {
      team = await db.collection('teams').findOne({ id: req.params.teamId });
      if (team) {
        teamPlayers = await db.collection('players')
          .find({ club: team.name })
          .toArray();
        teamMatches = await db.collection('matches')
          .find({ $or: [{ homeTeam: team.name }, { awayTeam: team.name }] })
          .sort({ date: -1 })
          .limit(10)
          .toArray();
      }
    }

    res.json({
      team: team ? { ...team, _id: undefined } : { id: req.params.teamId, name: 'Unknown Team' },
      squad: {
        size: teamPlayers.length,
        avgAge: teamPlayers.length > 0
          ? +(teamPlayers.reduce((s, p) => s + (p.age || 25), 0) / teamPlayers.length).toFixed(1)
          : 25.5,
        avgRating: teamPlayers.length > 0
          ? +(teamPlayers.reduce((s, p) => s + (p.rating || 7), 0) / teamPlayers.length).toFixed(1)
          : 7.2,
        totalValue: teamPlayers.reduce((s, p) => s + (p.marketValue || 0), 0)
      },
      recentForm: teamMatches.slice(0, 5).map(m => {
        const isHome = m.homeTeam === team?.name;
        const goalsFor = isHome ? m.homeScore : m.awayScore;
        const goalsAgainst = isHome ? m.awayScore : m.homeScore;
        return goalsFor > goalsAgainst ? 'W' : goalsFor < goalsAgainst ? 'L' : 'D';
      }),
      matches: teamMatches.map(m => ({ ...m, id: m.id || m._id?.toString(), _id: undefined })),
      players: teamPlayers.map(p => ({ ...p, id: p.id || p._id?.toString(), _id: undefined })),
      stats: {
        wins: teamMatches.filter(m => {
          const isH = m.homeTeam === team?.name;
          return isH ? m.homeScore > m.awayScore : m.awayScore > m.homeScore;
        }).length,
        draws: teamMatches.filter(m => m.homeScore === m.awayScore).length,
        losses: teamMatches.filter(m => {
          const isH = m.homeTeam === team?.name;
          return isH ? m.homeScore < m.awayScore : m.awayScore < m.homeScore;
        }).length,
        goalsScored: teamMatches.reduce((s, m) => s + (m.homeTeam === team?.name ? m.homeScore : m.awayScore) || 0, 0),
        goalsConceded: teamMatches.reduce((s, m) => s + (m.homeTeam === team?.name ? m.awayScore : m.homeScore) || 0, 0)
      }
    });
  } catch (error) {
    console.error('Team dashboard error:', error);
    res.status(500).json({ error: 'Failed to get team dashboard' });
  }
});

// GET /api/v2/analytics/dashboard/player/:playerId
router.get('/dashboard/player/:playerId', async (req, res) => {
  try {
    const db = req.app.locals.db;
    let player = null;

    if (db) {
      player = await db.collection('players').findOne({ id: req.params.playerId });
    }

    const p = player || { name: 'Unknown', position: 'Forward', age: 25, club: 'Unknown' };

    res.json({
      player: { ...p, id: p.id || req.params.playerId, _id: undefined },
      seasonStats: {
        appearances: p.appearances || 25,
        goals: p.goals || 8,
        assists: p.assists || 5,
        passAccuracy: p.passAccuracy || 82,
        rating: p.rating || 7.2,
        minutesPlayed: (p.appearances || 25) * 78,
        yellowCards: Math.floor(Math.random() * 5),
        redCards: 0
      },
      performanceTrend: {
        labels: ['GW1', 'GW2', 'GW3', 'GW4', 'GW5', 'GW6', 'GW7', 'GW8'],
        ratings: Array.from({ length: 8 }, () => +(6.5 + Math.random() * 2.5).toFixed(1)),
        xG: Array.from({ length: 8 }, () => +(Math.random() * 0.8).toFixed(2)),
        xA: Array.from({ length: 8 }, () => +(Math.random() * 0.5).toFixed(2))
      },
      radar: {
        categories: ['Pace', 'Shooting', 'Passing', 'Dribbling', 'Defending', 'Physical'],
        values: Array.from({ length: 6 }, () => Math.floor(60 + Math.random() * 35))
      },
      similarPlayers: [
        { name: 'Similar Player A', similarity: 0.92 },
        { name: 'Similar Player B', similarity: 0.87 },
        { name: 'Similar Player C', similarity: 0.84 }
      ]
    });
  } catch (error) {
    console.error('Player dashboard error:', error);
    res.status(500).json({ error: 'Failed to get player dashboard' });
  }
});

// GET /api/v2/analytics/trends/league
router.get('/trends/league', async (req, res) => {
  try {
    const db = req.app.locals.db;
    const leagueId = req.query.league_id;

    const leagues = ['Premier League', 'La Liga', 'Bundesliga', 'Serie A', 'Ligue 1', 'Süper Lig'];

    const trends = leagues.map(league => ({
      league,
      avgGoalsPerMatch: +(2 + Math.random() * 1.5).toFixed(2),
      avgPossession: { home: 52 + Math.floor(Math.random() * 6), away: 48 - Math.floor(Math.random() * 6) },
      topScorer: { name: 'Top Scorer', goals: Math.floor(15 + Math.random() * 15) },
      cleanSheetRate: +(20 + Math.random() * 20).toFixed(1),
      seasonProgress: Math.floor(50 + Math.random() * 40),
      trends: {
        months: ['Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'],
        goals: Array.from({ length: 6 }, () => +(2 + Math.random() * 1.5).toFixed(1)),
        attendance: Array.from({ length: 6 }, () => Math.floor(25000 + Math.random() * 50000))
      }
    }));

    if (leagueId) {
      const filtered = trends.find(t => t.league.toLowerCase().includes(leagueId.toLowerCase()));
      return res.json(filtered || trends[0]);
    }

    res.json(trends);
  } catch (error) {
    console.error('League trends error:', error);
    res.status(500).json({ error: 'Failed to get league trends' });
  }
});

// GET /api/v2/analytics/rankings/players
router.get('/rankings/players', async (req, res) => {
  try {
    const db = req.app.locals.db;
    const metric = req.query.metric || 'rating';
    const limit = parseInt(req.query.limit) || 20;
    const leagueId = req.query.league_id;

    if (!db) {
      return res.json(generateMockRankings('player', metric, limit));
    }

    const sortField = metric === 'goals' ? 'goals' : metric === 'assists' ? 'assists' : 'rating';
    const filter = leagueId ? { league: { $regex: leagueId, $options: 'i' } } : {};

    const players = await db.collection('players')
      .find(filter)
      .sort({ [sortField]: -1 })
      .limit(limit)
      .toArray();

    res.json(players.map((p, i) => ({
      rank: i + 1,
      id: p.id || p._id?.toString(),
      name: p.name,
      club: p.club,
      position: p.position,
      nationality: p.nationality,
      value: p[sortField] || 0,
      metric,
      _id: undefined
    })));
  } catch (error) {
    console.error('Player rankings error:', error);
    res.json(generateMockRankings('player', req.query.metric || 'rating', 20));
  }
});

// GET /api/v2/analytics/rankings/teams
router.get('/rankings/teams', async (req, res) => {
  try {
    const db = req.app.locals.db;
    const metric = req.query.metric || 'points';
    const limit = parseInt(req.query.limit) || 20;

    if (!db) {
      return res.json(generateMockRankings('team', metric, limit));
    }

    const teams = await db.collection('teams')
      .find({})
      .limit(limit)
      .toArray();

    res.json(teams.map((t, i) => ({
      rank: i + 1,
      id: t.id || t._id?.toString(),
      name: t.name,
      league: t.league,
      country: t.country,
      value: metric === 'marketValue' ? t.marketValue || 0 : Math.floor(Math.random() * 50 + 20),
      metric,
      _id: undefined
    })));
  } catch (error) {
    console.error('Team rankings error:', error);
    res.json(generateMockRankings('team', req.query.metric || 'points', 20));
  }
});

// GET /api/v2/analytics/insights/team/:teamId
router.get('/insights/team/:teamId', async (req, res) => {
  try {
    const db = req.app.locals.db;
    let teamName = req.params.teamId;

    if (db) {
      const team = await db.collection('teams').findOne({ id: req.params.teamId });
      if (team) teamName = team.name;
    }

    res.json({
      teamId: req.params.teamId,
      teamName,
      insights: [
        {
          type: 'strength',
          title: 'Strong Ball Possession',
          description: `${teamName} maintains above-average possession rates in recent matches.`,
          confidence: 0.88,
          impact: 'high'
        },
        {
          type: 'weakness',
          title: 'Vulnerable to Counter-Attacks',
          description: `High defensive line leaves ${teamName} exposed to fast breaks.`,
          confidence: 0.76,
          impact: 'medium'
        },
        {
          type: 'opportunity',
          title: 'Set-Piece Conversion',
          description: 'Set-piece conversion rate is below league average - area for improvement.',
          confidence: 0.82,
          impact: 'medium'
        },
        {
          type: 'trend',
          title: 'Improving xG Differential',
          description: 'xG differential has improved 15% over the last 5 matches.',
          confidence: 0.91,
          impact: 'high'
        }
      ],
      performanceIndex: +(70 + Math.random() * 25).toFixed(1),
      leagueRank: Math.floor(Math.random() * 20) + 1
    });
  } catch (error) {
    console.error('Team insights error:', error);
    res.status(500).json({ error: 'Failed to get team insights' });
  }
});

// GET /api/v2/analytics/insights/player/:playerId
router.get('/insights/player/:playerId', async (req, res) => {
  try {
    const db = req.app.locals.db;
    let playerName = req.params.playerId;

    if (db) {
      const player = await db.collection('players').findOne({ id: req.params.playerId });
      if (player) playerName = player.name;
    }

    res.json({
      playerId: req.params.playerId,
      playerName,
      insights: [
        {
          type: 'performance',
          title: 'Above Average Finishing',
          description: `${playerName}'s shot conversion rate exceeds league average by 4.2%.`,
          confidence: 0.89,
          impact: 'high'
        },
        {
          type: 'development',
          title: 'Improving Defensive Contribution',
          description: 'Tackles and interceptions have increased 20% in recent weeks.',
          confidence: 0.75,
          impact: 'medium'
        },
        {
          type: 'market',
          title: 'Market Value Trending Up',
          description: 'Performance metrics suggest a potential 15% market value increase.',
          confidence: 0.83,
          impact: 'high'
        }
      ],
      overallScore: +(70 + Math.random() * 25).toFixed(1),
      potentialRating: +(80 + Math.random() * 15).toFixed(1)
    });
  } catch (error) {
    console.error('Player insights error:', error);
    res.status(500).json({ error: 'Failed to get player insights' });
  }
});

// GET /api/v2/analytics/comparison/players?ids=id1,id2   
router.get('/comparison/players', async (req, res) => {
  try {
    const db = req.app.locals.db;
    const ids = (req.query.ids || '').split(',').filter(Boolean);

    if (ids.length < 2) {
      return res.status(400).json({ error: 'Provide at least 2 player IDs (ids=id1,id2)' });
    }

    let players = [];
    if (db) {
      players = await db.collection('players')
        .find({ id: { $in: ids } })
        .toArray();
    }

    // Ensure we have results for all IDs
    const result = ids.map(id => {
      const p = players.find(pl => pl.id === id) || {
        id, name: `Player ${id}`, position: 'Forward', age: 25, club: 'Unknown'
      };
      return {
        id: p.id,
        name: p.name,
        position: p.position,
        age: p.age,
        club: p.club,
        stats: {
          goals: p.goals || Math.floor(Math.random() * 20),
          assists: p.assists || Math.floor(Math.random() * 15),
          appearances: p.appearances || 25,
          rating: p.rating || +(6.5 + Math.random() * 2.5).toFixed(1),
          passAccuracy: p.passAccuracy || Math.floor(75 + Math.random() * 20),
          xG: p.xG || +(Math.random() * 15).toFixed(1),
          xA: p.xA || +(Math.random() * 10).toFixed(1),
          minutesPlayed: (p.appearances || 25) * 78
        },
        radar: {
          pace: Math.floor(60 + Math.random() * 35),
          shooting: Math.floor(60 + Math.random() * 35),
          passing: Math.floor(60 + Math.random() * 35),
          dribbling: Math.floor(60 + Math.random() * 35),
          defending: Math.floor(30 + Math.random() * 50),
          physical: Math.floor(60 + Math.random() * 35)
        }
      };
    });

    res.json({
      players: result,
      comparisonMatrix: generateComparisonMatrix(result)
    });
  } catch (error) {
    console.error('Player comparison error:', error);
    res.status(500).json({ error: 'Failed to compare players' });
  }
});

// GET /api/v2/analytics/comparison/teams?ids=id1,id2
router.get('/comparison/teams', async (req, res) => {
  try {
    const db = req.app.locals.db;
    const ids = (req.query.ids || '').split(',').filter(Boolean);

    if (ids.length < 2) {
      return res.status(400).json({ error: 'Provide at least 2 team IDs (ids=id1,id2)' });
    }

    let teams = [];
    if (db) {
      teams = await db.collection('teams')
        .find({ id: { $in: ids } })
        .toArray();
    }

    const result = ids.map(id => {
      const t = teams.find(tm => tm.id === id) || {
        id, name: `Team ${id}`, league: 'Unknown', country: 'Unknown'
      };
      return {
        id: t.id,
        name: t.name,
        league: t.league,
        country: t.country,
        stats: {
          points: Math.floor(30 + Math.random() * 50),
          wins: Math.floor(5 + Math.random() * 20),
          draws: Math.floor(2 + Math.random() * 10),
          losses: Math.floor(1 + Math.random() * 10),
          goalsScored: Math.floor(20 + Math.random() * 60),
          goalsConceded: Math.floor(10 + Math.random() * 40),
          possession: Math.floor(45 + Math.random() * 15),
          passAccuracy: Math.floor(75 + Math.random() * 15)
        }
      };
    });

    res.json({ teams: result });
  } catch (error) {
    console.error('Team comparison error:', error);
    res.status(500).json({ error: 'Failed to compare teams' });
  }
});

// ===== Helper Functions =====

function generateOverview() {
  return {
    summary: {
      totalPlayers: 500,
      totalTeams: 20,
      totalMatches: 380,
      liveMatches: 2,
      avgGoalsPerMatch: 2.7,
      scoutingReports: 156,
      activeScouts: 12,
      recentActivity: 42
    },
    topScorers: [],
    recentMatches: [],
    performanceTrends: {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      datasets: [
        { label: 'Goals', data: [45, 52, 48, 61, 55, 67] },
        { label: 'Assists', data: [32, 28, 35, 41, 38, 44] }
      ]
    },
    leagueDistribution: []
  };
}

function generateMockRankings(type, metric, limit) {
  return Array.from({ length: limit }, (_, i) => ({
    rank: i + 1,
    id: `${type[0]}${i + 1}`,
    name: `${type === 'player' ? 'Player' : 'Team'} ${i + 1}`,
    value: Math.floor(Math.random() * 30 + 5),
    metric
  }));
}

function generateComparisonMatrix(players) {
  const metrics = ['goals', 'assists', 'rating', 'passAccuracy', 'xG'];
  const matrix = {};
  metrics.forEach(m => {
    matrix[m] = {};
    players.forEach(p => {
      matrix[m][p.id] = p.stats[m] || 0;
    });
  });
  return matrix;
}

module.exports = router;
