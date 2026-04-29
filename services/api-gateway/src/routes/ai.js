/**
 * AI Routes - AI insights, predictions, and recommendations
 */
const express = require('express');
const router = express.Router();

function generateInsights(type) {
  const baseInsights = [
    {
      id: 'ai-1',
      type: 'scouting',
      title: 'Emerging Talent Alert',
      description: 'Lamine Yamal is showing exceptional development trajectory. His progressive carries and chance creation metrics place him in the top 1% of U18 players globally.',
      confidence: 0.92,
      priority: 'high',
      category: 'player_development',
      relatedEntityId: 'yamal-001',
      relatedEntityType: 'player',
      createdAt: new Date().toISOString(),
      tags: ['youth', 'high-potential', 'winger']
    },
    {
      id: 'ai-2',
      type: 'scouting',
      title: 'Transfer Window Opportunity',
      description: 'Florian Wirtz contract situation at Bayer Leverkusen creates acquisition opportunity. Market value expected to peak in Summer 2025.',
      confidence: 0.78,
      priority: 'medium',
      category: 'transfer',
      relatedEntityId: 'wirtz-001',
      relatedEntityType: 'player',
      createdAt: new Date().toISOString(),
      tags: ['transfer', 'contract', 'midfielder']
    },
    {
      id: 'ai-3',
      type: 'general',
      title: 'Tactical Trend Shift',
      description: 'Analysis shows 23% increase in successful high-press recoveries across top-5 leagues this season compared to last.',
      confidence: 0.85,
      priority: 'low',
      category: 'tactical',
      relatedEntityId: null,
      relatedEntityType: 'league',
      createdAt: new Date().toISOString(),
      tags: ['tactical', 'pressing', 'league-wide']
    },
    {
      id: 'ai-4',
      type: 'scouting',
      title: 'Undervalued Player Detection',
      description: 'Nico Williams metrics suggest he is significantly undervalued relative to output. xG contribution and progressive actions rank in top 5% of wingers.',
      confidence: 0.88,
      priority: 'high',
      category: 'valuation',
      relatedEntityId: 'nwilliams-001',
      relatedEntityType: 'player',
      createdAt: new Date().toISOString(),
      tags: ['undervalued', 'winger', 'spain']
    },
    {
      id: 'ai-5',
      type: 'general',
      title: 'Injury Risk Alert',
      description: 'Machine learning model detects elevated injury risk for players with >3200 minutes played this season and high sprint frequency.',
      confidence: 0.71,
      priority: 'medium',
      category: 'fitness',
      relatedEntityId: null,
      relatedEntityType: 'general',
      createdAt: new Date().toISOString(),
      tags: ['injury', 'fitness', 'workload']
    },
    {
      id: 'ai-6',
      type: 'general',
      title: 'Performance Prediction',
      description: 'Based on current form trajectory, Bukayo Saka projects to finish the season with 16 goals and 14 assists in the Premier League.',
      confidence: 0.74,
      priority: 'low',
      category: 'prediction',
      relatedEntityId: 'saka-001',
      relatedEntityType: 'player',
      createdAt: new Date().toISOString(),
      tags: ['prediction', 'goals', 'assists']
    }
  ];

  if (type && type !== 'all') {
    return baseInsights.filter(i => i.type === type);
  }
  return baseInsights;
}

// GET /api/ai/insights/:type
router.get('/insights/:type', (req, res) => {
  const insights = generateInsights(req.params.type);
  res.json(insights);
});

// GET /api/ai/insights/player/:playerId
router.get('/insights/player/:playerId', async (req, res) => {
  try {
    const db = req.app.locals.db;
    let playerName = 'Unknown Player';
    
    if (db) {
      const player = await db.collection('players').findOne({ id: req.params.playerId });
      if (player) playerName = player.name;
    }

    const insights = [
      {
        id: `pi-${req.params.playerId}-1`,
        type: 'player',
        title: `${playerName} - Performance Trend`,
        description: `${playerName} shows consistent improvement in key metrics over the last 10 matches. Expected performance index: 8.2/10.`,
        confidence: 0.82,
        priority: 'medium',
        category: 'performance',
        relatedEntityId: req.params.playerId,
        relatedEntityType: 'player',
        createdAt: new Date().toISOString()
      },
      {
        id: `pi-${req.params.playerId}-2`,
        type: 'player',
        title: `${playerName} - Market Value Projection`,
        description: `Based on current trajectory, market value expected to increase by 15-20% by end of season.`,
        confidence: 0.75,
        priority: 'low',
        category: 'valuation',
        relatedEntityId: req.params.playerId,
        relatedEntityType: 'player',
        createdAt: new Date().toISOString()
      }
    ];

    res.json(insights);
  } catch (error) {
    console.error('Player insights error:', error);
    res.status(500).json({ error: 'Failed to fetch player insights' });
  }
});

// GET /api/ai/recommendations
router.get('/recommendations', (req, res) => {
  res.json([
    { id: 'rec-1', type: 'signing', player: 'Florian Wirtz', reason: 'Exceptional creative output, contract leverage', priority: 'high' },
    { id: 'rec-2', type: 'signing', player: 'Nico Williams', reason: 'Undervalued, elite dribbling profile', priority: 'medium' },
    { id: 'rec-3', type: 'tactic', recommendation: 'Increase pressing intensity in first 15 minutes', reason: 'Data shows 40% higher conversion from early pressing', priority: 'medium' }
  ]);
});

module.exports = router;
