/**
 * Leagues Routes - Returns real competition data from MongoDB (Opta F1).
 * Falls back to static data only if the database is unavailable.
 */
const express = require('express');
const router = express.Router();

// ── static fallback ────────────────────────────────────────────────────────
const STATIC_LEAGUES = [
  { id: 'premier-league', name: 'Premier League', country: 'England', logo: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', season: '2024/25', teams: 20, currentMatchday: 15, startDate: '2024-08-17', endDate: '2025-05-25' },
  { id: 'la-liga', name: 'La Liga', country: 'Spain', logo: '🇪🇸', season: '2024/25', teams: 20, currentMatchday: 15, startDate: '2024-08-18', endDate: '2025-05-25' },
];

async function buildLeagueDoc(comp, db) {
  // Matches in this dataset don't carry a competition_id field — all 306 belong to c115.
  // We count all matches in the collection (single-competition dataset).
  const matchAgg = await db.collection('matches').aggregate([
    { $group: {
      _id: null,
      maxDay: { $max: '$matchDay' },
      total: { $sum: 1 },
      finished: { $sum: { $cond: [{ $eq: ['$status', 'finished'] }, 1, 0] } },
    }},
  ]).toArray();

  const teamCount = await db.collection('teams').countDocuments({});
  const agg = matchAgg[0] || {};

  return {
    id: comp.uID,
    name: comp.name || comp.competition_name || 'Unknown League',
    country: comp.country || 'Unknown',
    logo: '🏆',
    season: comp.season_name || String(comp.season_id || ''),
    teams: teamCount || comp.teams_count || 18,
    currentMatchday: agg.maxDay || 1,
    total_matches: agg.total || 0,
    matches_played: agg.finished || 0,
    startDate: comp.start_date || null,
    endDate: comp.end_date || null,
    data_source: 'opta_f1',
  };
}

// GET /api/leagues
router.get('/', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.json(STATIC_LEAGUES);

    const comps = await db.collection('competitions').find({}).toArray();
    if (!comps.length) return res.json(STATIC_LEAGUES);

    const result = await Promise.all(comps.map(c => buildLeagueDoc(c, db)));
    res.json(result);
  } catch (err) {
    console.error('Leagues list error:', err);
    res.json(STATIC_LEAGUES);
  }
});

// GET /api/leagues/:id
router.get('/:id', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (db) {
      const comp = await db.collection('competitions').findOne({ uID: req.params.id });
      if (comp) {
        return res.json(await buildLeagueDoc(comp, db));
      }
    }
    const staticLeague = STATIC_LEAGUES.find(l => l.id === req.params.id);
    if (!staticLeague) return res.status(404).json({ error: 'League not found' });
    res.json(staticLeague);
  } catch (err) {
    console.error('League by ID error:', err);
    res.status(500).json({ error: 'Failed to fetch league' });
  }
});

// GET /api/leagues/:id/matches   - fixture list for a competition (paginated)
router.get('/:id/matches', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.json([]);

    const { matchDay, status, limit = 34 } = req.query;
    // Matches have no competition_id field; all belong to the single competition c115.
    const filter = {};
    if (matchDay) filter.matchDay = Number(matchDay);
    if (status) filter.status = status;

    const docs = await db.collection('matches')
      .find(filter)
      .sort({ matchDay: 1, date: 1 })
      .limit(Number(limit))
      .toArray();

    res.json(docs.map(m => ({
      id: m.uID,
      matchDay: m.matchDay,
      date: m.date,
      status: m.status,
      homeTeam: m.homeTeamName,
      awayTeam: m.awayTeamName,
      homeScore: m.homeScore,
      awayScore: m.awayScore,
      homeTeamId: m.homeTeamID,
      awayTeamId: m.awayTeamID,
    })));
  } catch (err) {
    console.error('League matches error:', err);
    res.status(500).json({ error: 'Failed to fetch league matches' });
  }
});

module.exports = router;

