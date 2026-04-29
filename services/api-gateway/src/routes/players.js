/**
 * Players Routes - Proxies to player-service or serves from MongoDB directly
 */
const express = require('express');
const router = express.Router();

// GET /api/players - List all players
router.get('/', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.json([]);

    const { position, club, nationality, ageMin, ageMax, search, limit = 50, skip = 0 } = req.query;
    
    let filter = {};
    if (position) filter.position = { $in: Array.isArray(position) ? position : [position] };
    if (club) filter.club = { $in: Array.isArray(club) ? club : [club] };
    if (nationality) filter.nationality = nationality;
    if (ageMin || ageMax) {
      filter.age = {};
      if (ageMin) filter.age.$gte = parseInt(ageMin);
      if (ageMax) filter.age.$lte = parseInt(ageMax);
    }
    if (search) {
      filter.$or = [
        { name: { $regex: search, $options: 'i' } },
        { club: { $regex: search, $options: 'i' } },
        { nationality: { $regex: search, $options: 'i' } }
      ];
    }

    const players = await db.collection('players')
      .find(filter)
      .skip(parseInt(skip))
      .limit(parseInt(limit))
      .toArray();

    // Normalize _id to id
    const normalized = players.map(p => ({
      ...p,
      id: p.id || p._id?.toString(),
      _id: undefined
    }));

    res.json(normalized);
  } catch (error) {
    console.error('Players list error:', error);
    res.status(500).json({ error: 'Failed to fetch players' });
  }
});

// GET /api/players/search - Search players
router.get('/search', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.json([]);

    const { q, limit = 20 } = req.query;
    if (!q) return res.json([]);

    const players = await db.collection('players')
      .find({
        $or: [
          { name: { $regex: q, $options: 'i' } },
          { club: { $regex: q, $options: 'i' } },
          { position: { $regex: q, $options: 'i' } },
          { nationality: { $regex: q, $options: 'i' } }
        ]
      })
      .limit(parseInt(limit))
      .toArray();

    const normalized = players.map(p => ({
      ...p,
      id: p.id || p._id?.toString(),
      _id: undefined
    }));

    res.json(normalized);
  } catch (error) {
    console.error('Players search error:', error);
    res.status(500).json({ error: 'Search failed' });
  }
});

// GET /api/players/:id - Get player by ID
router.get('/:id', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.status(404).json({ error: 'Player not found' });

    let player = await db.collection('players').findOne({ id: req.params.id });
    if (!player) {
      try {
        const { ObjectId } = require('mongodb');
        player = await db.collection('players').findOne({ _id: new ObjectId(req.params.id) });
      } catch (e) { /* ignore invalid ObjectId */ }
    }
    
    if (!player) return res.status(404).json({ error: 'Player not found' });

    player.id = player.id || player._id?.toString();
    delete player._id;
    res.json(player);
  } catch (error) {
    console.error('Player get error:', error);
    res.status(500).json({ error: 'Failed to fetch player' });
  }
});

// POST /api/players - Create player
router.post('/', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.status(503).json({ error: 'Database unavailable' });

    const { v4: uuidv4 } = require('uuid');
    const player = {
      id: uuidv4(),
      ...req.body,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    await db.collection('players').insertOne(player);
    res.status(201).json(player);
  } catch (error) {
    console.error('Player create error:', error);
    res.status(500).json({ error: 'Failed to create player' });
  }
});

// PUT /api/players/:id - Update player
router.put('/:id', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.status(503).json({ error: 'Database unavailable' });

    const result = await db.collection('players').findOneAndUpdate(
      { id: req.params.id },
      { $set: { ...req.body, updatedAt: new Date().toISOString() } },
      { returnDocument: 'after' }
    );

    if (!result) return res.status(404).json({ error: 'Player not found' });
    res.json(result);
  } catch (error) {
    console.error('Player update error:', error);
    res.status(500).json({ error: 'Failed to update player' });
  }
});

module.exports = router;
