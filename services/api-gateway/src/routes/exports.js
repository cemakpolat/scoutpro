/**
 * Exports Routes - Data export endpoints
 */
const express = require('express');
const router = express.Router();

// Helper to format data as CSV
function toCSV(data, columns) {
  if (!data || data.length === 0) return '';
  const cols = columns || Object.keys(data[0]).filter(k => k !== '_id');
  const header = cols.join(',');
  const rows = data.map(row => cols.map(col => {
    const val = row[col];
    if (typeof val === 'string' && val.includes(',')) return `"${val}"`;
    return val ?? '';
  }).join(','));
  return [header, ...rows].join('\n');
}

// GET /api/v2/exports/players
router.get('/players', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.status(503).json({ error: 'Database unavailable' });

    const format = req.query.format || 'csv';
    const players = await db.collection('players').find({}).limit(500).toArray();
    const normalized = players.map(p => ({ ...p, id: p.id || p._id?.toString(), _id: undefined }));

    if (format === 'json') {
      res.setHeader('Content-Type', 'application/json');
      res.setHeader('Content-Disposition', 'attachment; filename="players.json"');
      return res.json(normalized);
    }

    // CSV
    const csv = toCSV(normalized, ['id', 'name', 'age', 'position', 'club', 'nationality', 'rating', 'marketValue', 'goals', 'assists', 'appearances']);
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename="players.csv"');
    res.send(csv);
  } catch (error) {
    console.error('Export players error:', error);
    res.status(500).json({ error: 'Export failed' });
  }
});

// GET /api/v2/exports/teams
router.get('/teams', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.status(503).json({ error: 'Database unavailable' });

    const format = req.query.format || 'csv';
    const teams = await db.collection('teams').find({}).limit(200).toArray();
    const normalized = teams.map(t => ({ ...t, id: t.id || t._id?.toString(), _id: undefined }));

    if (format === 'json') {
      res.setHeader('Content-Type', 'application/json');
      res.setHeader('Content-Disposition', 'attachment; filename="teams.json"');
      return res.json(normalized);
    }

    const csv = toCSV(normalized, ['id', 'name', 'shortName', 'league', 'country', 'manager', 'formation', 'marketValue']);
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename="teams.csv"');
    res.send(csv);
  } catch (error) {
    console.error('Export teams error:', error);
    res.status(500).json({ error: 'Export failed' });
  }
});

// GET /api/v2/exports/matches
router.get('/matches', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.status(503).json({ error: 'Database unavailable' });

    const format = req.query.format || 'csv';
    const matches = await db.collection('matches').find({}).limit(500).toArray();
    const normalized = matches.map(m => ({ ...m, id: m.id || m._id?.toString(), _id: undefined }));

    if (format === 'json') {
      res.setHeader('Content-Type', 'application/json');
      res.setHeader('Content-Disposition', 'attachment; filename="matches.json"');
      return res.json(normalized);
    }

    const csv = toCSV(normalized, ['id', 'homeTeam', 'awayTeam', 'homeScore', 'awayScore', 'date', 'competition', 'status']);
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename="matches.csv"');
    res.send(csv);
  } catch (error) {
    console.error('Export matches error:', error);
    res.status(500).json({ error: 'Export failed' });
  }
});

// GET /api/v2/exports/statistics
router.get('/statistics', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.status(503).json({ error: 'Database unavailable' });

    const format = req.query.format || 'csv';
    const players = await db.collection('players').find({}).limit(500).toArray();
    const stats = players.map(p => ({
      name: p.name,
      position: p.position,
      club: p.club,
      goals: p.goals,
      assists: p.assists,
      appearances: p.appearances,
      rating: p.rating,
      passAccuracy: p.passAccuracy,
      xG: p.xG,
      xA: p.xA
    }));

    if (format === 'json') {
      res.setHeader('Content-Type', 'application/json');
      res.setHeader('Content-Disposition', 'attachment; filename="statistics.json"');
      return res.json(stats);
    }

    const csv = toCSV(stats);
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename="statistics.csv"');
    res.send(csv);
  } catch (error) {
    console.error('Export statistics error:', error);
    res.status(500).json({ error: 'Export failed' });
  }
});

// POST /api/v2/exports/custom
router.post('/custom', async (req, res) => {
  try {
    const { data, format, columns } = req.body;
    
    if (format === 'json') {
      res.setHeader('Content-Type', 'application/json');
      res.setHeader('Content-Disposition', 'attachment; filename="custom-export.json"');
      return res.json(data);
    }

    const csv = toCSV(data, columns);
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename="custom-export.csv"');
    res.send(csv);
  } catch (error) {
    console.error('Custom export error:', error);
    res.status(500).json({ error: 'Export failed' });
  }
});

// GET /api/v2/exports/templates/:entityType
router.get('/templates/:entityType', (req, res) => {
  const templates = {
    players: {
      columns: ['name', 'age', 'position', 'club', 'nationality', 'rating', 'goals', 'assists'],
      formats: ['csv', 'json', 'excel']
    },
    teams: {
      columns: ['name', 'league', 'country', 'manager', 'formation', 'marketValue'],
      formats: ['csv', 'json', 'excel']
    },
    matches: {
      columns: ['homeTeam', 'awayTeam', 'homeScore', 'awayScore', 'date', 'competition', 'status'],
      formats: ['csv', 'json', 'excel']
    }
  };

  res.json(templates[req.params.entityType] || templates.players);
});

module.exports = router;
