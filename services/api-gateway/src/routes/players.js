/**
 * Players Routes - Direct MongoDB read for list/search; proxies to player-service for detail.
 */
const express = require('express');
const { ObjectId, Long } = require('mongodb');
const router = express.Router();

/** Normalise a raw MongoDB player document to the frontend Player shape. */
function toFrontendPlayer(doc) {
  const scoutproId = doc.scoutpro_id ?? doc.id;
  const uid = String(doc.uID || '');
  const provOpta = (doc.provider_ids || {}).opta || (uid.startsWith('p') ? uid.slice(1) : uid) || null;
  const name = doc.name
    || [doc.first_name, doc.last_name].filter(Boolean).join(' ')
    || [doc.first, doc.last].filter(Boolean).join(' ')
    || 'Unknown Player';

  return {
    id: scoutproId != null ? String(scoutproId) : uid,
    name,
    firstName: doc.first_name || doc.first || null,
    lastName: doc.last_name || doc.last || null,
    position: doc.position || doc.detailedPosition || null,
    age: doc.age ?? null,
    nationality: doc.nationality || null,
    club: doc.club || doc.current_team_name || doc.team_name || null,
    height: doc.height_cm ? String(doc.height_cm) : (doc.height || null),
    weight: doc.weight_kg ? String(doc.weight_kg) : (doc.weight || null),
    shirtNumber: doc.shirt_number || doc.shirtNumber || null,
    preferredFoot: doc.preferred_foot || doc.preferredFoot || null,
    birth_date: doc.birth_date
      ? String(doc.birth_date).substring(0, 10)
      : (doc.birthDate ? String(doc.birthDate).substring(0, 10) : null),
    opta_uid: uid || null,
    provider_ids: doc.provider_ids || (provOpta ? { opta: provOpta } : {}),
    team_id: doc.team_id != null ? String(doc.team_id) : null,
    current_team_id: doc.current_team_id != null ? String(doc.current_team_id) : null,
    current_team_name: doc.current_team_name || doc.team_name || null,
    competition_id: doc.competition_id || null,
    season_id: doc.season_id || null,
    statsbombEnrichment: doc.statsbombEnrichment || null,
  };
}

/** Build a MongoDB query from request query params (search, position, nationality, club). */
function buildPlayerListQuery(params) {
  const query = {};
  if (params.q || params.search) {
    const term = params.q || params.search;
    const rx = new RegExp(String(term).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i');
    query.$or = [
      { name: rx }, { first_name: rx }, { last_name: rx },
      { first: rx }, { last: rx }, { nationality: rx },
      { club: rx }, { current_team_name: rx },
    ];
  }
  if (params.position) query.position = params.position;
  if (params.nationality) query.nationality = params.nationality;
  if (params.club) query.club = params.club;
  return query;
}

const {
  ensureSuccess,
  normalizeEntity,
  normalizeList,
  requestJson,
  sendGatewayError,
  unwrapPayload,
} = require('../utils/serviceClient');

const playerServiceUrl = (process.env.PLAYER_SERVICE_URL || 'http://player-service:8000').replace(/\/$/, '');
const analyticsServiceUrl = (process.env.ANALYTICS_SERVICE_URL || 'http://analytics-service:8012').replace(/\/$/, '');
const playerRequestTimeoutMs = Number(process.env.PLAYER_SERVICE_TIMEOUT_MS || 2500);
const analyticsRequestTimeoutMs = Number(process.env.ANALYTICS_SERVICE_TIMEOUT_MS || 2500);

function toFiniteNumber(value, fallback = null) {
  if (value === null || value === undefined || value === '') {
    return fallback;
  }

  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : fallback;
}

function deriveAgeFromBirthDate(value) {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  const today = new Date();
  const age = today.getFullYear() - parsed.getFullYear() - (
    today.getMonth() < parsed.getMonth() ||
    (today.getMonth() === parsed.getMonth() && today.getDate() < parsed.getDate())
      ? 1
      : 0
  );

  return age >= 0 ? age : null;
}

function hasMeaningfulValue(value) {
  return value !== undefined && value !== null && value !== '';
}

function mergePlayerEntity(base = {}, source = {}, overwriteExisting = true) {
  const merged = { ...base };

  Object.entries(normalizeEntity(source || {})).forEach(([key, value]) => {
    if (!hasMeaningfulValue(value)) {
      return;
    }

    if (overwriteExisting || !hasMeaningfulValue(merged[key])) {
      merged[key] = value;
    }
  });

  return merged;
}

function buildPlayerLookup(playerId) {
  const lookups = [];
  const seen = new Set();

  const addLookup = (field, value) => {
    if (!hasMeaningfulValue(value)) {
      return;
    }

    // Include value type so Long(X) and String(X) are treated as distinct lookups
    const key = `${field}:${typeof value}:${String(value)}`;
    if (seen.has(key)) {
      return;
    }

    seen.add(key);
    lookups.push({ [field]: value });
  };

  const addIdentifierVariants = (value) => {
    if (!hasMeaningfulValue(value)) {
      return;
    }

    const normalized = String(value).trim();
    if (!normalized) {
      return;
    }

    addLookup('id', normalized);
    addLookup('uID', normalized);
    addLookup('scoutpro_id', normalized);
    addLookup('opta_uid', normalized);

    if (/^p\d+$/i.test(normalized)) {
      const numericVariant = normalized.slice(1);
      addLookup('uID', numericVariant);
      addLookup('opta_uid', numericVariant);
      addLookup('provider_ids.opta', numericVariant);
    }

    if (/^\d+$/.test(normalized)) {
      // ScoutPro IDs are 64-bit integers stored as BSON Long — JS Number loses precision
      // above MAX_SAFE_INTEGER. Use Long.fromString for exact match.
      try { addLookup('scoutpro_id', Long.fromString(normalized)); } catch (_) {}
      try { addLookup('id', Long.fromString(normalized)); } catch (_) {}

      if (Number(normalized) <= Number.MAX_SAFE_INTEGER) {
        addLookup('uID', Number(normalized));
      }
      addLookup('uID', `p${normalized}`);
      addLookup('opta_uid', `p${normalized}`);
      addLookup('provider_ids.opta', normalized);
    }
  };

  addIdentifierVariants(playerId);

  if (ObjectId.isValid(playerId)) {
    lookups.push({ _id: new ObjectId(playerId) });
  }

  return lookups;
}

function playerSnapshotScore(player = {}) {
  let score = 0;

  if (hasMeaningfulValue(player.scoutpro_id)) {
    score += 5;
  }
  if (hasMeaningfulValue(player.name)) {
    score += 4;
  }
  if (hasMeaningfulValue(player.position)) {
    score += 3;
  }
  if (hasMeaningfulValue(player.detailed_position) || hasMeaningfulValue(player.detailedPosition)) {
    score += 2;
  }
  if (hasMeaningfulValue(player.team_name) || hasMeaningfulValue(player.teamName) || hasMeaningfulValue(player.club)) {
    score += 2;
  }
  if (hasMeaningfulValue(player.birth_date) || hasMeaningfulValue(player.birthDate)) {
    score += 1;
  }

  return score;
}

function buildAnalyticsCandidateIds(requestedPlayerId, player = {}) {
  const candidates = [];

  const addCandidate = (value) => {
    if (!hasMeaningfulValue(value)) {
      return;
    }

    const normalized = String(value).trim();
    if (!normalized || candidates.includes(normalized)) {
      return;
    }

    candidates.push(normalized);

    if (/^p\d+$/i.test(normalized)) {
      const numericVariant = normalized.slice(1);
      if (!candidates.includes(numericVariant)) {
        candidates.push(numericVariant);
      }
    }

    if (/^\d+$/.test(normalized)) {
      const prefixedVariant = `p${normalized}`;
      if (!candidates.includes(prefixedVariant)) {
        candidates.push(prefixedVariant);
      }
    }
  };

  addCandidate(player.provider_ids?.opta);
  addCandidate(player.opta_uid);
  addCandidate(player.uID);
  addCandidate(requestedPlayerId);
  addCandidate(player.scoutpro_id);
  addCandidate(player.id);

  return candidates;
}

function analyticsPayloadHasSignal(payload) {
  const summary = payload?.summary || {};
  const player = normalizeEntity(payload?.player || {});

  if (Object.keys(player).length > 0) {
    return true;
  }

  return [
    summary.rating,
    summary.goals,
    summary.assists,
    summary.appearances,
    summary.passAccuracy,
    summary.club,
    summary.position,
    summary.age,
  ].some(hasMeaningfulValue);
}

async function findAnalyticsSummary(requestedPlayerId, basePlayer = {}) {
  const candidates = buildAnalyticsCandidateIds(requestedPlayerId, basePlayer);
  let fallbackPayload = null;

  for (const candidate of candidates) {
    const result = await requestJson(analyticsServiceUrl, `/api/v2/analytics/insights/player/${candidate}`, {
      timeoutMs: analyticsRequestTimeoutMs,
    }).catch((error) => {
      console.warn(`Analytics summary request failed for ${candidate}:`, error.message);
      return null;
    });

    if (!result?.ok) {
      continue;
    }

    fallbackPayload = result.payload;
    if (analyticsPayloadHasSignal(result.payload)) {
      return result.payload;
    }
  }

  return fallbackPayload;
}

async function findPlayerSnapshot(db, playerId) {
  if (!db) {
    return null;
  }

  const docs = await db.collection('players').find({ $or: buildPlayerLookup(playerId) }).limit(10).toArray();
  if (!docs.length) {
    return null;
  }

  const merged = docs
    .sort((left, right) => playerSnapshotScore(right) - playerSnapshotScore(left))
    .reduce((player, doc) => mergePlayerEntity(player, doc, false), {});

  return normalizeEntity({
    ...merged,
    id: String(merged.scoutpro_id || merged.id || merged.uID || playerId),
  });
}

function mergePlayerReadModel(basePlayer = {}, analyticsPayload = null) {
  const analyticsPlayer = normalizeEntity(analyticsPayload?.player || {});
  const summary = analyticsPayload?.summary || {};
  const merged = normalizeEntity({ ...basePlayer, ...analyticsPlayer });
  const resolvedName = merged.name || [merged.first_name || merged.firstName, merged.last_name || merged.lastName].filter(Boolean).join(' ');

  return {
    ...merged,
    id: String(merged.id || analyticsPayload?.player_id || ''),
    name: resolvedName || 'Unknown Player',
    firstName: merged.firstName || merged.first_name || null,
    lastName: merged.lastName || merged.last_name || null,
    position: merged.position || merged.detailed_position || summary.position || null,
    club: merged.club || merged.team_name || summary.club || null,
    age: merged.age ?? summary.age ?? deriveAgeFromBirthDate(merged.birth_date || merged.birthDate),
    rating: toFiniteNumber(summary.rating, merged.rating ?? null),
    overallRating: toFiniteNumber(summary.rating, merged.overallRating ?? merged.rating ?? null),
    goals: toFiniteNumber(summary.goals, merged.goals ?? 0),
    assists: toFiniteNumber(summary.assists, merged.assists ?? 0),
    appearances: toFiniteNumber(summary.appearances, merged.appearances ?? 0),
    passAccuracy: toFiniteNumber(summary.passAccuracy, merged.passAccuracy ?? 0),
    shirtNumber: merged.shirtNumber || merged.shirt_number || null,
    analyticsInsights: analyticsPayload?.insights || [],
    analyticsUpdatedAt: analyticsPayload?.last_updated || null,
  };
}

router.get('/', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (db) {
      const limit = Math.min(parseInt(req.query.limit, 10) || 100, 500);
      const query = buildPlayerListQuery(req.query);
      const docs = await db.collection('players').find(query).limit(limit * 3).toArray();

      // Deduplicate by scoutpro_id / uID so dual-source docs don't appear twice
      const seen = new Set();
      const players = [];
      for (const doc of docs) {
        const key = String(doc.scoutpro_id ?? doc.id ?? doc.uID ?? '');
        if (!key || seen.has(key)) continue;
        seen.add(key);
        players.push(toFrontendPlayer(doc));
        if (players.length >= limit) break;
      }
      return res.json(players);
    }

    // Fallback: proxy to player-service when DB is not directly available
    const payload = ensureSuccess(
      await requestJson(playerServiceUrl, '/api/v2/players', {
        query: {
          q: req.query.search || req.query.q,
          position: req.query.position,
          nationality: req.query.nationality,
          club: req.query.club,
          age_min: req.query.ageMin || req.query.age_min,
          age_max: req.query.ageMax || req.query.age_max,
          limit: req.query.limit || 100,
        },
      }),
      'Failed to fetch players'
    );
    res.json(normalizeList(payload.players || unwrapPayload(payload)));
  } catch (error) {
    console.error('Players list error:', error);
    sendGatewayError(res, error, 'Failed to fetch players');
  }
});

router.get('/search', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (db) {
      const limit = Math.min(parseInt(req.query.limit, 10) || 20, 100);
      const query = buildPlayerListQuery({ q: req.query.q });
      if (!Object.keys(query).length) return res.json([]);

      const docs = await db.collection('players').find(query).limit(limit * 3).toArray();
      const seen = new Set();
      const players = [];
      for (const doc of docs) {
        const key = String(doc.scoutpro_id ?? doc.id ?? doc.uID ?? '');
        if (!key || seen.has(key)) continue;
        seen.add(key);
        players.push(toFrontendPlayer(doc));
        if (players.length >= limit) break;
      }
      return res.json(players);
    }

    const payload = ensureSuccess(
      await requestJson(playerServiceUrl, '/api/v2/players/search', {
        query: { q: req.query.q, limit: req.query.limit || 20 },
      }),
      'Search failed'
    );
    res.json(normalizeList(payload.players || unwrapPayload(payload)));
  } catch (error) {
    console.error('Players search error:', error);
    sendGatewayError(res, error, 'Search failed');
  }
});

/**
 * GET /api/players/statistics
 * Returns player statistics (goals, shots, passes, etc.) aggregated from match events.
 */
router.get('/statistics', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.status(503).json({ success: false, error: 'Database not available' });
    }

    const limit = Math.min(parseInt(req.query.limit) || 100, 500);
    const skip = Math.max(parseInt(req.query.skip) || 0, 0);
    const sortBy = req.query.sortBy || 'goals';
    const sortOrder = req.query.sortOrder === 'asc' ? 1 : -1;

    // Fetch player statistics
    const stats = await db
      .collection('player_statistics')
      .find({})
      .sort({ [sortBy]: sortOrder })
      .skip(skip)
      .limit(limit)
      .toArray();

    const total = await db.collection('player_statistics').countDocuments({});

    res.json({
      success: true,
      data: stats,
      pagination: {
        total,
        skip,
        limit,
        pages: Math.ceil(total / limit),
      },
    });
  } catch (error) {
    console.error('Player statistics error:', error);
    sendGatewayError(res, error, 'Failed to fetch player statistics');
  }
});

router.get('/:id', async (req, res) => {
  try {
    const db = req.app.locals.db;
    const [playerResult, dbPlayer] = await Promise.all([
      requestJson(playerServiceUrl, `/api/v2/players/${req.params.id}`, {
        timeoutMs: playerRequestTimeoutMs,
      }).catch((error) => {
        console.warn(`Player service request failed for ${req.params.id}:`, error.message);
        return null;
      }),
      findPlayerSnapshot(db, req.params.id).catch((error) => {
        console.warn(`Mongo player fallback failed for ${req.params.id}:`, error.message);
        return null;
      }),
    ]);

    const playerPayload = playerResult?.ok ? unwrapPayload(playerResult.payload) : null;
    const resolvedPlayer = mergePlayerEntity(
      mergePlayerEntity({}, dbPlayer || {}, false),
      playerPayload || {},
      true,
    );
    const analyticsPayload = await findAnalyticsSummary(req.params.id, resolvedPlayer);
    const basePlayer = mergePlayerEntity(
      mergePlayerEntity({}, resolvedPlayer || {}, true),
      analyticsPayload?.player || {},
      true,
    );

    if (hasMeaningfulValue(basePlayer.scoutpro_id)) {
      basePlayer.id = String(basePlayer.scoutpro_id);
    } else if (hasMeaningfulValue(basePlayer.id)) {
      basePlayer.id = String(basePlayer.id);
    } else if (hasMeaningfulValue(basePlayer.uID)) {
      basePlayer.id = String(basePlayer.uID);
    }

    if (!Object.keys(basePlayer || {}).length && !analyticsPayload?.player) {
      if (playerResult && !playerResult.ok) {
        return sendGatewayError(res, ensureSuccess(playerResult, 'Failed to fetch player'), 'Failed to fetch player');
      }

      return res.status(404).json({
        error: 'Player not found',
        message: `Player ${req.params.id} could not be resolved from available backends.`,
      });
    }

    res.json(mergePlayerReadModel(basePlayer || {}, analyticsPayload));
  } catch (error) {
    console.error('Player get error:', error);
    sendGatewayError(res, error, 'Failed to fetch player');
  }
});

router.post('/', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(playerServiceUrl, '/api/v2/players', {
        method: 'POST',
        body: req.body,
      }),
      'Failed to create player'
    );

    res.status(201).json(unwrapPayload(payload));
  } catch (error) {
    console.error('Player create error:', error);
    sendGatewayError(res, error, 'Failed to create player');
  }
});

router.put('/:id', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(playerServiceUrl, `/api/v2/players/${req.params.id}`, {
        method: 'PUT',
        body: req.body,
      }),
      'Failed to update player'
    );

    res.json(unwrapPayload(payload));
  } catch (error) {
    console.error('Player update error:', error);
    sendGatewayError(res, error, 'Failed to update player');
  }
});

/**
 * POST /api/players/enrich/statsbomb
 * Triggers the StatsBomb enrichment pipeline in player-service.
 * Reads StatsBomb CSV files, aggregates per-player xG/OBV/pass stats,
 * and writes statsbombEnrichment onto matching player documents.
 *
 * Query params:
 *   match_id (optional) – specific StatsBomb match_id; omit for all CSVs
 */
router.post('/enrich/statsbomb', async (req, res) => {
  try {
    const qs = req.query.match_id ? `?match_id=${encodeURIComponent(req.query.match_id)}` : '';
    const payload = ensureSuccess(
      await requestJson(playerServiceUrl, `/api/v2/players/enrich/statsbomb${qs}`, {
        method: 'POST',
        timeoutMs: 30000,  // enrichment can take a moment
      }),
      'Failed to run StatsBomb enrichment'
    );
    res.json(unwrapPayload(payload));
  } catch (error) {
    console.error('StatsBomb enrichment error:', error);
    sendGatewayError(res, error, 'StatsBomb enrichment failed');
  }
});

/**
 * GET /api/players/statistics
 * Returns player statistics (goals, shots, passes, etc.) aggregated from match events.
 */
router.get('/statistics', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.status(503).json({ success: false, error: 'Database not available' });
    }

    const limit = Math.min(parseInt(req.query.limit) || 100, 500);
    const skip = Math.max(parseInt(req.query.skip) || 0, 0);
    const sortBy = req.query.sortBy || 'goals';
    const sortOrder = req.query.sortOrder === 'asc' ? 1 : -1;

    // Fetch player statistics
    const stats = await db
      .collection('player_statistics')
      .find({})
      .sort({ [sortBy]: sortOrder })
      .skip(skip)
      .limit(limit)
      .toArray();

    const total = await db.collection('player_statistics').countDocuments({});

    res.json({
      success: true,
      data: stats,
      pagination: {
        total,
        skip,
        limit,
        pages: Math.ceil(total / limit),
      },
    });
  } catch (error) {
    console.error('Player statistics error:', error);
    sendGatewayError(res, error, 'Failed to fetch player statistics');
  }
});

/**
 * GET /api/players/:id/statistics
 * Returns statistics for a specific player.
 */
router.get('/:id/statistics', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.status(503).json({ success: false, error: 'Database not available' });
    }

    const playerIdNum = parseInt(req.params.id);
    const stats = await db.collection('player_statistics').findOne({ player_id: playerIdNum });

    if (!stats) {
      return res.status(404).json({ success: false, error: 'Player statistics not found' });
    }

    res.json({ success: true, data: stats });
  } catch (error) {
    console.error('Player statistics error:', error);
    sendGatewayError(res, error, 'Failed to fetch player statistics');
  }
});

router.get('/:id/events', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(playerServiceUrl, `/api/v2/players/${req.params.id}/events`, {
        query: {
          match_id: req.query.match_id,
          event_type: req.query.event_type,
          limit: req.query.limit || 100,
        },
      }),
      'Failed to fetch player events'
    );

    res.json(unwrapPayload(payload) || []);
  } catch (error) {
    console.error('Player events error:', error);
    sendGatewayError(res, error, 'Failed to fetch player events');
  }
});

router.get('/:id/matches', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(playerServiceUrl, `/api/v2/players/${req.params.id}/matches`, {
        query: {
          limit: req.query.limit || 50,
        },
      }),
      'Failed to fetch player matches'
    );

    const raw = unwrapPayload(payload);
    const matches = Array.isArray(raw) ? raw : (raw?.matches || []);
    res.json(matches.map(toFrontendMatch));
  } catch (error) {
    console.error('Player matches error:', error);
    sendGatewayError(res, error, 'Failed to fetch player matches');
  }
});

module.exports = router;
