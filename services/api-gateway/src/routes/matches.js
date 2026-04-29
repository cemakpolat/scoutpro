/**
 * Matches Routes
 */
const express = require('express');
const router = express.Router();

// GET /api/matches - List matches
router.get('/', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.json([]);

    const { status, teams, competition, season, limit = 50, skip = 0 } = req.query;
    
    let filter = {};
    if (status) filter.status = { $in: Array.isArray(status) ? status : [status] };
    if (competition) filter.competition = competition;
    if (season) filter.season = season;
    if (teams) {
      const teamList = Array.isArray(teams) ? teams : [teams];
      filter.$or = [
        { homeTeam: { $in: teamList } },
        { awayTeam: { $in: teamList } }
      ];
    }

    const matches = await db.collection('matches')
      .find(filter)
      .sort({ date: -1 })
      .skip(parseInt(skip))
      .limit(parseInt(limit))
      .toArray();

    const normalized = matches.map(m => ({
      ...m,
      id: m.id || m._id?.toString(),
      _id: undefined
    }));

    res.json(normalized);
  } catch (error) {
    console.error('Matches list error:', error);
    res.status(500).json({ error: 'Failed to fetch matches' });
  }
});

// GET /api/matches/live - Live matches
router.get('/live', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.json([]);

    const matches = await db.collection('matches')
      .find({ status: 'live' })
      .toArray();

    const normalized = matches.map(m => ({
      ...m,
      id: m.id || m._id?.toString(),
      _id: undefined
    }));

    res.json(normalized);
  } catch (error) {
    console.error('Live matches error:', error);
    res.status(500).json({ error: 'Failed to fetch live matches' });
  }
});

// GET /api/matches/:id - Get match by ID
router.get('/:id', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.status(404).json({ error: 'Match not found' });

    let match = await db.collection('matches').findOne({ id: req.params.id });
    if (!match) {
      try {
        const { ObjectId } = require('mongodb');
        match = await db.collection('matches').findOne({ _id: new ObjectId(req.params.id) });
      } catch (e) { /* ignore */ }
    }
    
    if (!match) return res.status(404).json({ error: 'Match not found' });

    match.id = match.id || match._id?.toString();
    delete match._id;
    res.json(match);
  } catch (error) {
    console.error('Match get error:', error);
    res.status(500).json({ error: 'Failed to fetch match' });
  }
});

// POST /api/matches - Create match
router.post('/', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.status(503).json({ error: 'Database unavailable' });

    const { v4: uuidv4 } = require('uuid');
    const match = {
      id: uuidv4(),
      ...req.body,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    await db.collection('matches').insertOne(match);
    res.status(201).json(match);
  } catch (error) {
    console.error('Match create error:', error);
    res.status(500).json({ error: 'Failed to create match' });
  }
});

// PUT /api/matches/:id - Update match
router.put('/:id', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.status(503).json({ error: 'Database unavailable' });

    const result = await db.collection('matches').findOneAndUpdate(
      { id: req.params.id },
      { $set: { ...req.body, updatedAt: new Date().toISOString() } },
      { returnDocument: 'after' }
    );

    if (!result) return res.status(404).json({ error: 'Match not found' });
    res.json(result);
  } catch (error) {
    console.error('Match update error:', error);
    res.status(500).json({ error: 'Failed to update match' });
  }
});

// GET /api/matches/:id/events - Get match events (goals, cards, substitutions, etc.)
router.get('/:id/events', async (req, res) => {
  try {
    const db = req.app.locals.db;
    let match = null;
    
    if (db) {
      match = await db.collection('matches').findOne({ id: req.params.id });
    }

    // Generate realistic match events based on the match data
    const events = [];
    if (match) {
      const homeGoals = match.homeScore || 0;
      const awayGoals = match.awayScore || 0;
      
      // Generate goal events
      for (let i = 0; i < homeGoals; i++) {
        events.push({
          id: `evt-${req.params.id}-hg-${i}`,
          matchId: req.params.id,
          type: 'goal',
          minute: Math.floor(Math.random() * 90) + 1,
          team: match.homeTeam,
          player: `Home Player ${i + 1}`,
          description: `Goal scored by ${match.homeTeam}`
        });
      }
      for (let i = 0; i < awayGoals; i++) {
        events.push({
          id: `evt-${req.params.id}-ag-${i}`,
          matchId: req.params.id,
          type: 'goal',
          minute: Math.floor(Math.random() * 90) + 1,
          team: match.awayTeam,
          player: `Away Player ${i + 1}`,
          description: `Goal scored by ${match.awayTeam}`
        });
      }

      // Add some standard events
      events.push(
        { id: `evt-${req.params.id}-ko`, matchId: req.params.id, type: 'kickoff', minute: 0, description: 'Kick off' },
        { id: `evt-${req.params.id}-ht`, matchId: req.params.id, type: 'halftime', minute: 45, description: 'Half time' },
        { id: `evt-${req.params.id}-yc1`, matchId: req.params.id, type: 'yellow_card', minute: Math.floor(Math.random() * 90) + 1, team: match.homeTeam, player: 'Home Player 5', description: 'Yellow card' },
        { id: `evt-${req.params.id}-sub1`, matchId: req.params.id, type: 'substitution', minute: 60 + Math.floor(Math.random() * 25), team: match.homeTeam, player: 'Home Player 11', replacement: 'Home Sub 1', description: 'Substitution' }
      );

      // Sort by minute
      events.sort((a, b) => a.minute - b.minute);
    }

    res.json(events);
  } catch (error) {
    console.error('Match events error:', error);
    res.status(500).json({ error: 'Failed to fetch match events' });
  }
});

module.exports = router;
