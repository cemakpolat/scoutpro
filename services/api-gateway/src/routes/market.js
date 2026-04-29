/**
 * Market Routes - Market trends, transfer predictions, valuations
 */
const express = require('express');
const router = express.Router();

// GET /api/market/trends
router.get('/trends', async (req, res) => {
  try {
    const db = req.app.locals.db;
    let players = [];
    
    if (db) {
      players = await db.collection('players').find({})
        .sort({ marketValue: -1 })
        .limit(10)
        .toArray();
    }

    const trends = players.length > 0 ? players.map((p, i) => ({
      id: `trend-${i + 1}`,
      playerName: p.name,
      playerId: p.id,
      club: p.club,
      position: p.position,
      currentValue: p.marketValue || 50000000,
      previousValue: (p.marketValue || 50000000) * 0.85,
      change: 15 + Math.random() * 20,
      trend: Math.random() > 0.3 ? 'up' : 'down',
      age: p.age,
      nationality: p.nationality,
      lastUpdated: new Date().toISOString()
    })) : [
      { id: 'trend-1', playerName: 'Jude Bellingham', club: 'Real Madrid', position: 'MF', currentValue: 180000000, previousValue: 120000000, change: 50.0, trend: 'up', age: 21, nationality: 'England', lastUpdated: new Date().toISOString() },
      { id: 'trend-2', playerName: 'Erling Haaland', club: 'Manchester City', position: 'FW', currentValue: 200000000, previousValue: 170000000, change: 17.6, trend: 'up', age: 24, nationality: 'Norway', lastUpdated: new Date().toISOString() },
      { id: 'trend-3', playerName: 'Kylian Mbappé', club: 'Real Madrid', position: 'FW', currentValue: 250000000, previousValue: 260000000, change: -3.8, trend: 'down', age: 25, nationality: 'France', lastUpdated: new Date().toISOString() },
      { id: 'trend-4', playerName: 'Vinícius Jr.', club: 'Real Madrid', position: 'FW', currentValue: 200000000, previousValue: 150000000, change: 33.3, trend: 'up', age: 24, nationality: 'Brazil', lastUpdated: new Date().toISOString() },
      { id: 'trend-5', playerName: 'Bukayo Saka', club: 'Arsenal', position: 'FW', currentValue: 140000000, previousValue: 110000000, change: 27.3, trend: 'up', age: 23, nationality: 'England', lastUpdated: new Date().toISOString() },
      { id: 'trend-6', playerName: 'Florian Wirtz', club: 'Bayer Leverkusen', position: 'MF', currentValue: 130000000, previousValue: 80000000, change: 62.5, trend: 'up', age: 21, nationality: 'Germany', lastUpdated: new Date().toISOString() }
    ];

    res.json(trends);
  } catch (error) {
    console.error('Market trends error:', error);
    res.status(500).json({ error: 'Failed to fetch market trends' });
  }
});

// GET /api/market/predictions
router.get('/predictions', async (req, res) => {
  try {
    const predictions = [
      { id: 'pred-1', playerName: 'Florian Wirtz', fromClub: 'Bayer Leverkusen', toClub: 'Real Madrid', probability: 0.65, estimatedFee: 130000000, window: 'Summer 2025' },
      { id: 'pred-2', playerName: 'Lamine Yamal', fromClub: 'Barcelona', toClub: 'Barcelona', probability: 0.90, estimatedFee: 0, window: 'Contract Extension' },
      { id: 'pred-3', playerName: 'Alexander Isak', fromClub: 'Newcastle', toClub: 'Arsenal', probability: 0.35, estimatedFee: 100000000, window: 'Summer 2025' },
      { id: 'pred-4', playerName: 'Khvicha Kvaratskhelia', fromClub: 'Napoli', toClub: 'PSG', probability: 0.55, estimatedFee: 80000000, window: 'Winter 2025' },
      { id: 'pred-5', playerName: 'Xavi Simons', fromClub: 'PSG', toClub: 'Bayern Munich', probability: 0.60, estimatedFee: 90000000, window: 'Summer 2025' }
    ];
    res.json(predictions);
  } catch (error) {
    console.error('Market predictions error:', error);
    res.status(500).json({ error: 'Failed to fetch predictions' });
  }
});

// GET /api/market/valuations
router.get('/valuations', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (db) {
      const players = await db.collection('players').find({})
        .sort({ marketValue: -1 })
        .limit(20)
        .project({ name: 1, club: 1, position: 1, marketValue: 1, age: 1, nationality: 1, id: 1 })
        .toArray();
      return res.json(players);
    }
    res.json([]);
  } catch (error) {
    console.error('Market valuations error:', error);
    res.status(500).json({ error: 'Failed to fetch valuations' });
  }
});

module.exports = router;
