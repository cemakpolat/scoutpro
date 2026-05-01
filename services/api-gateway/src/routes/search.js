/**
 * Search routes.
 */
const express = require('express');
const { v4: uuidv4 } = require('uuid');
const router = express.Router();

const {
  ensureSuccess,
  normalizeList,
  requestJson,
  sendGatewayError,
  unwrapPayload,
} = require('../utils/serviceClient');

const searchServiceUrl = (process.env.SEARCH_SERVICE_URL || 'http://search-service:8000').replace(/\/$/, '');
const playerServiceUrl = (process.env.PLAYER_SERVICE_URL || 'http://player-service:8000').replace(/\/$/, '');
const teamServiceUrl = (process.env.TEAM_SERVICE_URL || 'http://team-service:8000').replace(/\/$/, '');
const matchServiceUrl = (process.env.MATCH_SERVICE_URL || 'http://match-service:8000').replace(/\/$/, '');
const DEFAULT_OWNER_ID = 'u1';

const clampLimit = (value, fallback) => {
  const parsed = Number.parseInt(String(value || fallback), 10);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallback;
  }
  return Math.min(parsed, 100);
};

const includesQuery = (value, query) => String(value || '').toLowerCase().includes(query);

const serializeDoc = (doc) => ({
  ...doc,
  id: doc.id || doc._id?.toString(),
  _id: undefined,
});

const requireDb = (req, res) => {
  const db = req.app.locals.db;
  if (!db) {
    res.status(503).json({ error: 'Database unavailable' });
    return null;
  }
  return db;
};

const getOwnerId = (req) => {
  if (typeof req.query.ownerId === 'string' && req.query.ownerId.trim()) {
    return req.query.ownerId.trim();
  }

  if (typeof req.body?.ownerId === 'string' && req.body.ownerId.trim()) {
    return req.body.ownerId.trim();
  }

  return DEFAULT_OWNER_ID;
};

const matchIncludesQuery = (match, query) => {
  if (!query) return true;

  return [
    match.homeTeam,
    match.awayTeam,
    match.home_team,
    match.away_team,
    match.competition,
    match.venue,
    match.date,
  ].some((value) => includesQuery(value, query));
};

router.get('/', async (req, res) => {
  try {
    const query = typeof req.query.q === 'string' ? req.query.q.trim() : '';
    const normalizedQuery = query.toLowerCase();
    const limit = clampLimit(req.query.limit, 10);
    const requestedType = typeof req.query.type === 'string' ? req.query.type.toLowerCase() : 'all';

    const includePlayers = requestedType === 'all' || requestedType === 'player' || requestedType === 'players';
    const includeTeams = requestedType === 'all' || requestedType === 'team' || requestedType === 'teams';
    const includeMatches = requestedType === 'all' || requestedType === 'match' || requestedType === 'matches';

    const [playerResult, teamResult, matchResult] = await Promise.allSettled([
      includePlayers
        ? requestJson(playerServiceUrl, '/api/v2/players', {
            query: {
              q: query || undefined,
              limit,
            },
          })
        : Promise.resolve({ ok: true, payload: [] }),
      includeTeams
        ? requestJson(teamServiceUrl, '/api/v2/teams/search', {
            query: {
              q: query || undefined,
              limit,
            },
          })
        : Promise.resolve({ ok: true, payload: [] }),
      includeMatches
        ? requestJson(matchServiceUrl, '/api/v2/matches', {
            query: {
              limit: Math.max(limit * 5, 25),
            },
          })
        : Promise.resolve({ ok: true, payload: [] }),
    ]);

    const players = playerResult.status === 'fulfilled' && playerResult.value.ok
      ? normalizeList(unwrapPayload(playerResult.value.payload)).map((player) => ({ ...player, type: 'player' }))
      : [];

    const teams = teamResult.status === 'fulfilled' && teamResult.value.ok
      ? normalizeList(unwrapPayload(teamResult.value.payload)).map((team) => ({ ...team, type: 'team' }))
      : [];

    const rawMatches = matchResult.status === 'fulfilled' && matchResult.value.ok
      ? unwrapPayload(matchResult.value.payload)
      : [];

    const matches = Array.isArray(rawMatches)
      ? rawMatches.filter((match) => matchIncludesQuery(match, normalizedQuery)).slice(0, limit)
      : [];

    res.json({
      players,
      teams,
      matches,
    });
  } catch (error) {
    console.error('Search error:', error);
    sendGatewayError(res, error, 'Search failed');
  }
});

router.get('/saved', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    const ownerId = getOwnerId(req);
    const saved = await db.collection('saved_searches')
      .find({ ownerId })
      .sort({ updatedAt: -1, createdAt: -1 })
      .limit(50)
      .toArray();

    res.json(saved.map(serializeDoc));
  } catch (error) {
    console.error('List saved searches error:', error);
    res.status(500).json({ error: 'Failed to list saved searches' });
  }
});

router.post('/saved', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    if (!req.body?.name || !req.body?.query) {
      return res.status(400).json({ error: 'name and query are required' });
    }

    const timestamp = new Date().toISOString();
    const savedSearch = {
      id: req.body.id || uuidv4(),
      ownerId: getOwnerId(req),
      name: req.body.name,
      query: req.body.query,
      filters: req.body.filters || {},
      type: req.body.type || 'all',
      createdAt: req.body.createdAt || timestamp,
      updatedAt: timestamp,
    };

    await db.collection('saved_searches').insertOne(savedSearch);
    res.status(201).json(savedSearch);
  } catch (error) {
    console.error('Create saved search error:', error);
    res.status(500).json({ error: 'Failed to save search' });
  }
});

router.put('/saved/:savedSearchId', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    const ownerId = getOwnerId(req);
    const existing = await db.collection('saved_searches').findOne({ id: req.params.savedSearchId, ownerId });
    if (!existing) {
      return res.status(404).json({ error: 'Saved search not found' });
    }

    const updatedSearch = {
      ...existing,
      ...req.body,
      id: existing.id,
      ownerId,
      updatedAt: new Date().toISOString(),
    };

    await db.collection('saved_searches').updateOne(
      { id: req.params.savedSearchId, ownerId },
      { $set: updatedSearch }
    );

    res.json(serializeDoc(updatedSearch));
  } catch (error) {
    console.error('Update saved search error:', error);
    res.status(500).json({ error: 'Failed to update saved search' });
  }
});

router.delete('/saved/:savedSearchId', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    const ownerId = getOwnerId(req);
    const result = await db.collection('saved_searches').deleteOne({ id: req.params.savedSearchId, ownerId });
    if (result.deletedCount === 0) {
      return res.status(404).json({ error: 'Saved search not found' });
    }

    res.json({ success: true });
  } catch (error) {
    console.error('Delete saved search error:', error);
    res.status(500).json({ error: 'Failed to delete saved search' });
  }
});

router.get('/history', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    const ownerId = getOwnerId(req);
    const history = await db.collection('search_history')
      .find({ ownerId })
      .sort({ timestamp: -1 })
      .limit(50)
      .toArray();

    res.json(history.map(serializeDoc));
  } catch (error) {
    console.error('List search history error:', error);
    res.status(500).json({ error: 'Failed to list search history' });
  }
});

router.post('/history', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    if (!req.body?.query) {
      return res.status(400).json({ error: 'query is required' });
    }

    const ownerId = getOwnerId(req);
    const latestDuplicate = await db.collection('search_history').findOne(
      { ownerId, query: req.body.query },
      { sort: { timestamp: -1 } }
    );

    if (latestDuplicate) {
      const duplicateAgeMs = Date.now() - new Date(latestDuplicate.timestamp).getTime();
      if (duplicateAgeMs < 60_000) {
        return res.json(serializeDoc(latestDuplicate));
      }
    }

    const historyItem = {
      id: req.body.id || uuidv4(),
      ownerId,
      query: req.body.query,
      filters: req.body.filters || {},
      type: req.body.type || 'all',
      resultCount: Number(req.body.resultCount) || 0,
      timestamp: new Date().toISOString(),
    };

    await db.collection('search_history').insertOne(historyItem);
    res.status(201).json(historyItem);
  } catch (error) {
    console.error('Create search history entry error:', error);
    res.status(500).json({ error: 'Failed to add search history entry' });
  }
});

router.delete('/history', async (req, res) => {
  try {
    const db = requireDb(req, res);
    if (!db) {
      return;
    }

    const ownerId = getOwnerId(req);
    await db.collection('search_history').deleteMany({ ownerId });
    res.json({ success: true });
  } catch (error) {
    console.error('Clear search history error:', error);
    res.status(500).json({ error: 'Failed to clear search history' });
  }
});

router.get('/players', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(searchServiceUrl, '/api/v2/search/players', {
        query: {
          q: req.query.q,
          position: req.query.position,
          club: req.query.club,
          size: req.query.limit || 20,
        },
      }),
      'Search failed'
    );

    res.json(normalizeList(unwrapPayload(payload)));
  } catch (error) {
    console.error('Search players error:', error);
    sendGatewayError(res, error, 'Search failed');
  }
});

router.get('/teams', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(searchServiceUrl, '/api/v2/search/teams', {
        query: {
          q: req.query.q,
          size: req.query.limit || 20,
        },
      }),
      'Search failed'
    );

    res.json(normalizeList(unwrapPayload(payload)));
  } catch (error) {
    console.error('Search teams error:', error);
    sendGatewayError(res, error, 'Search failed');
  }
});

router.get('/events', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(searchServiceUrl, '/api/v2/search/events', {
        query: {
          player_id: req.query.player_id,
          event_type: req.query.event_type,
          match_id: req.query.match_id,
          team_id: req.query.team_id,
          size: req.query.limit || 50,
        },
      }),
      'Search failed'
    );

    res.json(unwrapPayload(payload) || []);
  } catch (error) {
    console.error('Search events error:', error);
    sendGatewayError(res, error, 'Search failed');
  }
});

module.exports = router;
