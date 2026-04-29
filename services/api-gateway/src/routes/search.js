/**
 * Search Routes - Global search across all entities
 */
const express = require('express');
const router = express.Router();

// GET /api/search - Global search
router.get('/', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.json({ players: [], teams: [], matches: [] });

    const { q, limit = 10 } = req.query;
    if (!q) return res.json({ players: [], teams: [], matches: [] });

    const regex = { $regex: q, $options: 'i' };
    const lim = parseInt(limit);

    const [players, teams, matches] = await Promise.all([
      db.collection('players')
        .find({ $or: [{ name: regex }, { club: regex }, { nationality: regex }] })
        .limit(lim)
        .toArray(),
      db.collection('teams')
        .find({ $or: [{ name: regex }, { shortName: regex }] })
        .limit(lim)
        .toArray(),
      db.collection('matches')
        .find({ $or: [{ homeTeam: regex }, { awayTeam: regex }, { competition: regex }] })
        .limit(lim)
        .toArray()
    ]);

    res.json({
      players: players.map(p => ({ ...p, id: p.id || p._id?.toString(), _id: undefined, type: 'player' })),
      teams: teams.map(t => ({ ...t, id: t.id || t._id?.toString(), _id: undefined, type: 'team' })),
      matches: matches.map(m => ({ ...m, id: m.id || m._id?.toString(), _id: undefined, type: 'match' }))
    });
  } catch (error) {
    console.error('Search error:', error);
    res.status(500).json({ error: 'Search failed' });
  }
});

// GET /api/search/players
router.get('/players', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.json([]);

    const { q, position, club, limit = 20 } = req.query;
    let filter = {};
    
    if (q) {
      filter.$or = [
        { name: { $regex: q, $options: 'i' } },
        { club: { $regex: q, $options: 'i' } }
      ];
    }
    if (position) filter.position = position;
    if (club) filter.club = club;

    const players = await db.collection('players')
      .find(filter)
      .limit(parseInt(limit))
      .toArray();

    res.json(players.map(p => ({ ...p, id: p.id || p._id?.toString(), _id: undefined })));
  } catch (error) {
    console.error('Search players error:', error);
    res.status(500).json({ error: 'Search failed' });
  }
});

// GET /api/search/teams
router.get('/teams', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.json([]);

    const { q, limit = 20 } = req.query;
    let filter = {};
    if (q) {
      filter.$or = [
        { name: { $regex: q, $options: 'i' } },
        { shortName: { $regex: q, $options: 'i' } }
      ];
    }

    const teams = await db.collection('teams')
      .find(filter)
      .limit(parseInt(limit))
      .toArray();

    res.json(teams.map(t => ({ ...t, id: t.id || t._id?.toString(), _id: undefined })));
  } catch (error) {
    console.error('Search teams error:', error);
    res.status(500).json({ error: 'Search failed' });
  }
});

module.exports = router;
