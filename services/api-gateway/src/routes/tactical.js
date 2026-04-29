/**
 * Tactical Routes - Tactical pattern analysis endpoints
 */
const express = require('express');
const router = express.Router();

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

// GET /api/tactical/formations
router.get('/formations', (req, res) => {
  res.json([
    { id: '4-3-3', name: '4-3-3', popularity: 45, topTeams: ['Manchester City', 'Barcelona', 'Real Madrid'] },
    { id: '4-4-2', name: '4-4-2', popularity: 22, topTeams: ['Atlético Madrid', 'Juventus'] },
    { id: '3-5-2', name: '3-5-2', popularity: 15, topTeams: ['Inter Milan', 'Atalanta'] },
    { id: '4-2-3-1', name: '4-2-3-1', popularity: 18, topTeams: ['Bayern Munich', 'Dortmund'] }
  ]);
});

module.exports = router;
