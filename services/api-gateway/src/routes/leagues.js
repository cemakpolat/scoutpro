/**
 * Leagues Routes - Serves league/competition data
 */
const express = require('express');
const router = express.Router();

const leagues = [
  {
    id: 'premier-league',
    name: 'Premier League',
    country: 'England',
    logo: '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
    season: '2024/25',
    teams: 20,
    currentMatchday: 15,
    startDate: '2024-08-17',
    endDate: '2025-05-25'
  },
  {
    id: 'la-liga',
    name: 'La Liga',
    country: 'Spain',
    logo: '🇪🇸',
    season: '2024/25',
    teams: 20,
    currentMatchday: 15,
    startDate: '2024-08-18',
    endDate: '2025-05-25'
  },
  {
    id: 'bundesliga',
    name: 'Bundesliga',
    country: 'Germany',
    logo: '🇩🇪',
    season: '2024/25',
    teams: 18,
    currentMatchday: 14,
    startDate: '2024-08-23',
    endDate: '2025-05-17'
  },
  {
    id: 'serie-a',
    name: 'Serie A',
    country: 'Italy',
    logo: '🇮🇹',
    season: '2024/25',
    teams: 20,
    currentMatchday: 15,
    startDate: '2024-08-18',
    endDate: '2025-05-25'
  },
  {
    id: 'ligue-1',
    name: 'Ligue 1',
    country: 'France',
    logo: '🇫🇷',
    season: '2024/25',
    teams: 18,
    currentMatchday: 14,
    startDate: '2024-08-16',
    endDate: '2025-05-18'
  },
  {
    id: 'champions-league',
    name: 'UEFA Champions League',
    country: 'Europe',
    logo: '🏆',
    season: '2024/25',
    teams: 36,
    currentMatchday: 6,
    startDate: '2024-09-17',
    endDate: '2025-05-31'
  }
];

// GET /api/leagues
router.get('/', (req, res) => {
  res.json(leagues);
});

// GET /api/leagues/:id
router.get('/:id', (req, res) => {
  const league = leagues.find(l => l.id === req.params.id);
  if (!league) {
    return res.status(404).json({ error: 'League not found' });
  }
  res.json(league);
});

module.exports = router;
