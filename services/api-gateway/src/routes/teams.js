/**
 * Teams Routes
 */
const express = require('express');
const router = express.Router();

// GET /api/teams
router.get('/', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.json([]);

    const { country, league, search, limit = 50, skip = 0 } = req.query;
    
    let filter = {};
    if (country) filter.country = country;
    if (league) filter.league = league;
    if (search) {
      filter.$or = [
        { name: { $regex: search, $options: 'i' } },
        { shortName: { $regex: search, $options: 'i' } }
      ];
    }

    const teams = await db.collection('teams')
      .find(filter)
      .skip(parseInt(skip))
      .limit(parseInt(limit))
      .toArray();

    const normalized = teams.map(t => ({
      ...t,
      id: t.id || t._id?.toString(),
      _id: undefined
    }));

    res.json(normalized);
  } catch (error) {
    console.error('Teams list error:', error);
    res.status(500).json({ error: 'Failed to fetch teams' });
  }
});

// GET /api/teams/search
router.get('/search', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.json([]);

    const { q, limit = 20 } = req.query;
    if (!q) return res.json([]);

    const teams = await db.collection('teams')
      .find({
        $or: [
          { name: { $regex: q, $options: 'i' } },
          { shortName: { $regex: q, $options: 'i' } },
          { league: { $regex: q, $options: 'i' } }
        ]
      })
      .limit(parseInt(limit))
      .toArray();

    const normalized = teams.map(t => ({
      ...t,
      id: t.id || t._id?.toString(),
      _id: undefined
    }));

    res.json(normalized);
  } catch (error) {
    console.error('Teams search error:', error);
    res.status(500).json({ error: 'Search failed' });
  }
});

// GET /api/teams/:id
router.get('/:id', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.status(404).json({ error: 'Team not found' });

    let team = await db.collection('teams').findOne({ id: req.params.id });
    if (!team) {
      try {
        const { ObjectId } = require('mongodb');
        team = await db.collection('teams').findOne({ _id: new ObjectId(req.params.id) });
      } catch (e) { /* ignore */ }
    }
    
    if (!team) return res.status(404).json({ error: 'Team not found' });

    team.id = team.id || team._id?.toString();
    delete team._id;
    res.json(team);
  } catch (error) {
    console.error('Team get error:', error);
    res.status(500).json({ error: 'Failed to fetch team' });
  }
});

// POST /api/teams
router.post('/', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.status(503).json({ error: 'Database unavailable' });

    const { v4: uuidv4 } = require('uuid');
    const team = {
      id: uuidv4(),
      ...req.body,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    await db.collection('teams').insertOne(team);
    res.status(201).json(team);
  } catch (error) {
    console.error('Team create error:', error);
    res.status(500).json({ error: 'Failed to create team' });
  }
});

// PUT /api/teams/:id
router.put('/:id', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.status(503).json({ error: 'Database unavailable' });

    const result = await db.collection('teams').findOneAndUpdate(
      { id: req.params.id },
      { $set: { ...req.body, updatedAt: new Date().toISOString() } },
      { returnDocument: 'after' }
    );

    if (!result) return res.status(404).json({ error: 'Team not found' });
    res.json(result);
  } catch (error) {
    console.error('Team update error:', error);
    res.status(500).json({ error: 'Failed to update team' });
  }
});

module.exports = router;
