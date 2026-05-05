/**
 * Matches Routes - Proxies to match-service (which owns MongoDB access).
 * Normalizes the service response to the unified frontend Match shape.
 */
const express = require('express');
const { Long } = require('mongodb');
const router = express.Router();

const {
  ensureSuccess,
  normalizeEntity,
  normalizeList,
  requestJson,
  sendGatewayError,
  unwrapPayload,
} = require('../utils/serviceClient');

const matchServiceUrl = (process.env.MATCH_SERVICE_URL || 'http://match-service:8000').replace(/\/$/, '');

function escapeRegex(value = '') {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Build a MongoDB $or query that finds events for a given match ID.
 * Supports:
 *   - scoutpro_match_id (BSON Long) — canonical ScoutPro integer
 *   - matchID / match_id (Opta numeric string) — pre-migration fallback
 *
 * IMPORTANT: JavaScript Number loses precision on 64-bit ScoutPro IDs.
 * Always use Long.fromString() for the scoutpro_match_id comparison.
 */
function buildEventMatchQuery(id) {
  const strId = String(id);
  const variants = [];

  // ScoutPro integer ID — use BSON Long to avoid JS float64 precision loss
  try {
    variants.push({ scoutpro_match_id: Long.fromString(strId) });
  } catch (_) { /* not a valid integer string */ }

  // Opta string fallbacks
  variants.push({ matchID: strId }, { match_id: strId });

  // Opta numeric fallback (for small IDs that fit in JS Number safely)
  const num = Number(strId);
  if (!isNaN(num) && num <= Number.MAX_SAFE_INTEGER) {
    variants.push({ matchID: num }, { match_id: num });
  }

  return { $or: variants };
}

/**
 * Build a MongoDB $or query to find a match document by its ID.
 * Supports scoutpro_id (integer), uID with/without 'g' prefix, and legacy id hash.
 */
function buildMatchQuery(id) {
  const strId = String(id);
  const variants = [];
  // BSON Long for 64-bit scoutpro_id / id fields (Number() loses precision)
  try { variants.push({ scoutpro_id: Long.fromString(strId) }); } catch (_) {}
  try { variants.push({ id: Long.fromString(strId) }); } catch (_) {}
  variants.push({ uID: strId }, { uID: `g${strId}` }, { id: strId }, { scoutpro_id: strId });
  const num = Number(strId);
  if (!isNaN(num) && num <= Number.MAX_SAFE_INTEGER) {
    variants.push({ uID: num }, { scoutpro_id: num });
  }
  return { $or: variants };
}

/** Strip leading 't' prefix from team IDs (DB stores numeric; frontend passes "t405") */
function normalizeTeamIdQuery(team_id) {
  if (!team_id) return undefined;
  const stripped = String(team_id).replace(/^t/i, '');
  const num = Number(stripped);
  return isNaN(num) ? { $in: [team_id, stripped] } : { $in: [num, stripped, team_id] };
}

function normalizeTeamIdValue(teamId) {
  if (teamId == null) return '';
  const raw = String(teamId).trim();
  if (!raw) return '';
  if (/^[a-zA-Z]\d+$/.test(raw)) return raw.slice(1);
  return raw;
}

function collectTeamIdVariants(teamId) {
  const raw = String(teamId || '').trim();
  if (!raw) return [];

  const normalized = normalizeTeamIdValue(raw);
  const variants = new Set([raw, normalized]);
  if (/^\d+$/.test(normalized)) {
    variants.add(`t${normalized}`);
    const numeric = Number(normalized);
    if (Number.isSafeInteger(numeric)) variants.add(numeric);
  }

  return Array.from(variants).filter(Boolean);
}

function extractEventTeamId(event) {
  return normalizeTeamIdValue(event?.team_id);
}

// ---------------------------------------------------------------------------
// Visualization cache — match event data is immutable once seeded so TTL is 1hr
// ---------------------------------------------------------------------------
const _vizCache = new Map();
const VIZ_CACHE_TTL_MS = Number(process.env.VIZ_CACHE_TTL_MS || 3600000); // 1 hour

function _vizCacheGet(key) {
  const entry = _vizCache.get(key);
  if (!entry) return null;
  if (Date.now() > entry.expiresAt) { _vizCache.delete(key); return null; }
  return entry.data;
}

function _vizCacheSet(key, data) {
  _vizCache.set(key, { data, expiresAt: Date.now() + VIZ_CACHE_TTL_MS });
}

// Pre-compute a 10×10 heatmap grid from a list of {x, y, intensity} points.
function computeHeatmapGrid(points) {
  const GRID = 10;
  const grid = {};
  const cellCounts = {};
  for (const pt of points) {
    const cx = Math.min(Math.floor((pt.x / 100) * GRID), GRID - 1);
    const cy = Math.min(Math.floor((pt.y / 100) * GRID), GRID - 1);
    const key = `${cx},${cy}`;
    grid[key] = (grid[key] || 0) + (pt.intensity || 1);
    cellCounts[key] = (cellCounts[key] || 0) + 1;
  }
  const maxIntensity = Math.max(...Object.values(grid), 1);
  return { grid, cellCounts, maxIntensity, totalPoints: points.length };
}

/** Cache of teamId → teamName from the local MongoDB teams collection. */
const _teamNameCache = new Map();
let _teamCacheBuiltAt = 0;
const TEAM_CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

async function getTeamNameMap(db) {
  if (!db) return _teamNameCache;
  const now = Date.now();
  if (_teamNameCache.size > 0 && now - _teamCacheBuiltAt < TEAM_CACHE_TTL_MS) {
    return _teamNameCache;
  }
  const teams = await db.collection('teams')
    .find({}, { projection: { _id: 0, uID: 1, id: 1, name: 1, shortName: 1 } })
    .toArray();
  _teamNameCache.clear();
  for (const t of teams) {
    const name = t.name || t.shortName || '';
    const uid = String(t.uID || '');
    const sid = String(t.id || t.scoutpro_id || '');
    if (uid) _teamNameCache.set(uid, name);
    if (sid && sid !== uid) _teamNameCache.set(sid, name);
  }
  _teamCacheBuiltAt = now;
  return _teamNameCache;
}

function resolveTeamLabel(rawName, rawId, teamMap) {
  const name = rawName || '';
  if (name && !/^team\s+\d+$/i.test(name)) return name;
  const id = String(rawId || '');
  if (id && teamMap.has(id)) return teamMap.get(id);
  return id ? `Team ${id}` : 'Unknown Team';
}

/**
 * Map a match-service response object to the frontend Match interface.
 * The service returns snake_case (home_team_id, home_score, home_team_name …)
 * after going through _normalize_match_doc; the frontend expects camelCase.
 *
 * NOTE: MongoDB documents store m.date as the ingestion timestamp and m.status
 * as "scheduled" for all records. The real match date, period (status), and
 * scores live inside provider_data.opta.data — read those first.
 */
function toFrontendMatch(m, teamMap = new Map()) {
  if (!m) return null;

  // ── Pull the canonical Opta sub-document (may be absent for non-Opta records) ──
  const optaData = m.provider_data?.opta?.data || {};

  // ── Status: prefer Opta period, fall back to stored status field ──────────
  const status = (() => {
    const optaPeriod = (optaData.period || '').toLowerCase();
    if (optaPeriod === 'fulltime' || optaPeriod === 'postgame') return 'finished';
    if (optaPeriod === 'firsthalf' || optaPeriod === 'secondhalf') return 'live';
    const s = (m.status || '').toLowerCase();
    if (s === 'played' || s === 'finished') return 'finished';
    if (s === 'fixture' || s === 'scheduled' || s === '') return 'scheduled';
    return s;
  })();

  // ── Date: prefer Opta match date over ingestion timestamp ─────────────────
  const date = (() => {
    const raw = optaData.date;          // e.g. "2019-08-16 18:30:00" or a Date object
    if (raw) {
      // raw may be a JS Date (MongoDB ISODate) or a string
      if (raw instanceof Date) return isNaN(raw.getTime()) ? (m.date || null) : raw.toISOString();
      const str = String(raw);
      const iso = str.includes('T') ? str : str.replace(' ', 'T') + (str.endsWith('Z') ? '' : 'Z');
      const d = new Date(iso);
      return isNaN(d.getTime()) ? (m.date || null) : d.toISOString();
    }
    return m.date || null;
  })();

  // ── Scores: prefer Opta scores over root-level fields ────────────────────
  const homeScore = optaData.home_score ?? m.home_score ?? m.homeScore ?? 0;
  const awayScore = optaData.away_score ?? m.away_score ?? m.awayScore ?? 0;

  const homeTeamId = String(m.home_team_id || m.homeTeamID || '');
  const awayTeamId = String(m.away_team_id || m.awayTeamID || '');

  return {
    id: m.scoutpro_id != null ? String(m.scoutpro_id) : String(m.uID || m.id || '').replace(/^g/, ''),
    homeTeam: resolveTeamLabel(m.home_team_name || m.homeTeamName, homeTeamId, teamMap),
    awayTeam: resolveTeamLabel(m.away_team_name || m.awayTeamName, awayTeamId, teamMap),
    homeTeamId,
    awayTeamId,
    homeScore,
    awayScore,
    date,
    venue: m.venue || null,
    attendance: m.attendance ? String(m.attendance) : null,
    status,
    matchDay: m.match_day || m.matchDay || null,
    homeFormation: m.home_formation || m.homeFormation || null,
    awayFormation: m.away_formation || m.awayFormation || null,
    competition: m.competition || 'Turkish Süper Lig',
    referee: m.referee || null,
    weather: m.weather || null,
    homeXG: m.home_xg ?? m.homeXG ?? null,
    awayXG: m.away_xg ?? m.awayXG ?? null,
    homePossession: m.home_possession ?? m.homePossession ?? null,
    awayPossession: m.away_possession ?? m.awayPossession ?? null,
    homeShots: m.home_shots ?? m.homeShots ?? null,
    awayShots: m.away_shots ?? m.awayShots ?? null,
    createdAt: m.createdAt || m.created_at || new Date().toISOString(),
    updatedAt: m.updatedAt || m.updated_at || new Date().toISOString(),
    data_source: 'opta_f1',
  };
}

router.get('/', async (req, res) => {
  try {
    const db = req.app.locals.db;

    // When DB is available query it directly so we can sort finished matches first
    // across the full dataset, not just the page the match-service returns.
    if (db) {
      const limit = Math.min(parseInt(req.query.limit, 10) || 400, 1000);
      const query = {};

      // NOTE: All MongoDB match documents have status:"scheduled" regardless of
      // their actual Opta state. The real status is encoded in
      // provider_data.opta.data.period (FullTime / FirstHalf / etc.).
      // Use that field for all status-based filtering and sorting.
      if (req.query.status) {
        const rawStatus = String(req.query.status).toLowerCase();
        if (rawStatus === 'finished' || rawStatus === 'played') {
          query['provider_data.opta.data.period'] = { $in: ['FullTime', 'PostGame'] };
        } else if (rawStatus === 'live') {
          query['provider_data.opta.data.period'] = { $in: ['FirstHalf', 'SecondHalf'] };
        } else if (rawStatus === 'scheduled' || rawStatus === 'fixture') {
          query['provider_data.opta.data.period'] = { $nin: ['FullTime', 'PostGame', 'FirstHalf', 'SecondHalf'] };
        }
        // For unknown status values fall through — return all documents
      }
      if (req.query.team_id) {
        const teamNum = Number(req.query.team_id);
        const tq = isNaN(teamNum) ? req.query.team_id : { $in: [teamNum, req.query.team_id] };
        query.$or = [{ home_team_id: tq }, { away_team_id: tq }];
      }

      // Pull all matches, sort by derived status (opta period) then real match date
      const docs = await db.collection('matches').find(query).limit(limit * 3).toArray();

      const optaStatusRank = (doc) => {
        const period = (doc.provider_data?.opta?.data?.period || '').toLowerCase();
        const s = (doc.status || '').toLowerCase();
        if (period === 'fulltime' || period === 'postgame' || s === 'finished' || s === 'played') return 0;
        if (period === 'firsthalf' || period === 'secondhalf' || s === 'live') return 1;
        return 2;
      };
      const optaDate = (doc) => {
        const raw = doc.provider_data?.opta?.data?.date;
        if (!raw) return 0;
        // raw may be a JS Date (MongoDB ISODate) or a string like "2019-08-16 18:30:00"
        if (raw instanceof Date) return raw.getTime();
        const str = String(raw);
        const iso = str.includes('T') ? str : str.replace(' ', 'T') + (str.endsWith('Z') ? '' : 'Z');
        const t = Date.parse(iso);
        return isNaN(t) ? 0 : t;
      };
      docs.sort((a, b) =>
        optaStatusRank(a) - optaStatusRank(b) ||
        optaDate(b) - optaDate(a)
      );

      const teamMap = await getTeamNameMap(db);
      return res.json(docs.slice(0, limit).map((m) => toFrontendMatch(m, teamMap)).filter(Boolean));
    }

    // Fallback: proxy to match-service
    const payload = ensureSuccess(
      await requestJson(matchServiceUrl, '/api/v2/matches', {
        query: {
          status: req.query.status,
          competition_id: req.query.competition || req.query.competition_id,
          season_id: req.query.season || req.query.season_id,
          team_id: req.query.team_id,
          limit: req.query.limit || 400,
        },
      }),
      'Failed to fetch matches'
    );
    const raw = unwrapPayload(payload);
    const list = Array.isArray(raw) ? raw : (raw?.matches || []);
    const teamMap = await getTeamNameMap(req.app.locals.db);
    res.json(list.map((m) => toFrontendMatch(m, teamMap)));
  } catch (error) {
    console.error('Matches list error:', error);
    sendGatewayError(res, error, 'Failed to fetch matches');
  }
});

router.get('/live', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(matchServiceUrl, '/api/v2/matches/live'),
      'Failed to fetch live matches'
    );

    const raw = unwrapPayload(payload);
    const list = Array.isArray(raw) ? raw : (raw?.matches || []);
    const teamMap = await getTeamNameMap(req.app.locals.db);
    res.json(list.map((m) => toFrontendMatch(m, teamMap)));
  } catch (error) {
    console.error('Live matches error:', error);
    sendGatewayError(res, error, 'Failed to fetch live matches');
  }
});

router.get('/search', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.json([]);
    }

    const q = String(req.query.q || '').trim();
    const status = String(req.query.status || '').trim();
    const limit = Math.min(parseInt(req.query.limit, 10) || 30, 100);

    const query = {};
    if (q) {
      const regex = new RegExp(escapeRegex(q), 'i');
      query.$or = [
        { home_team: regex },
        { away_team: regex },
        { home_team_name: regex },
        { away_team_name: regex },
        { competition: regex },
        { competition_name: regex },
        { date: regex },
        { uID: regex },
      ];
    }

    if (status) {
      // Use Opta period field since all documents have status="scheduled"
      const s = status.toLowerCase();
      if (s === 'finished' || s === 'played') {
        // Merge with existing $or using $and if needed
        const periodCond = { 'provider_data.opta.data.period': { $in: ['FullTime', 'PostGame'] } };
        if (query.$or) {
          query.$and = [{ $or: query.$or }, periodCond];
          delete query.$or;
        } else {
          Object.assign(query, periodCond);
        }
      } else if (s === 'scheduled' || s === 'fixture') {
        const periodCond = { 'provider_data.opta.data.period': { $nin: ['FullTime', 'PostGame', 'FirstHalf', 'SecondHalf'] } };
        if (query.$or) {
          query.$and = [{ $or: query.$or }, periodCond];
          delete query.$or;
        } else {
          Object.assign(query, periodCond);
        }
      }
    }

    const matches = await db
      .collection('matches')
      .find(query)
      .sort({ 'provider_data.opta.data.date': -1 })
      .limit(limit)
      .toArray();

    // Sort finished matches first using the opta period, then by real match date
    const optaStatusRank = (doc) => {
      const period = (doc.provider_data?.opta?.data?.period || '').toLowerCase();
      if (period === 'fulltime' || period === 'postgame') return 0;
      if (period === 'firsthalf' || period === 'secondhalf') return 1;
      return 2;
    };
    const optaDate = (doc) => {
      const raw = doc.provider_data?.opta?.data?.date;
      if (!raw) return 0;
      if (raw instanceof Date) return raw.getTime();
      const str = String(raw);
      const iso = str.includes('T') ? str : str.replace(' ', 'T') + (str.endsWith('Z') ? '' : 'Z');
      const t = Date.parse(iso);
      return isNaN(t) ? 0 : t;
    };
    matches.sort((a, b) => optaStatusRank(a) - optaStatusRank(b) || optaDate(b) - optaDate(a));

    const teamMap = await getTeamNameMap(db);
    res.json(matches.map((m) => toFrontendMatch(m, teamMap)).filter(Boolean));
  } catch (error) {
    console.error('Match search error:', error);
    sendGatewayError(res, error, 'Failed to search matches');
  }
});

router.get('/:id/events', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.json([]);
    }

    const events = await db.collection('match_events')
      .find(buildEventMatchQuery(req.params.id))
      .toArray();

    const data = events.map(e => ({
      id: String(e._id),
      match_id: e.scoutpro_match_id != null ? String(e.scoutpro_match_id) : String(e.match_id || e.matchID || req.params.id),
      player_id: e.player_id != null ? String(e.player_id) : null,
      player_name: e.player_name || null,
      team_id: e.team_id != null ? String(e.team_id) : null,
      type_name: e.type_name || e.type || null,
      minute: e.minute ?? null,
      is_goal: !!e.is_goal,
      is_key_pass: !!e.is_key_pass,
      is_assist: !!e.is_assist,
      is_successful: e.is_successful !== false,
      progressive_pass: !!e.progressive_pass,
      entered_final_third: !!e.entered_final_third,
      entered_box: !!e.entered_box,
      high_regain: !!e.high_regain,
      analytical_xg: e.analytical_xg ?? null,
      shot_distance: e.shot_distance ?? null,
      location: e.location || null,
      raw_event: e.raw_event || null,
    }));

    res.json(data);
  } catch (error) {
    console.error('Match events error:', error);
    // Return empty array instead of crashing — callers handle empty gracefully
    res.json([]);
  }
});

router.get('/:id/shots-map', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.json({ success: true, data: [] });
    }

    const cacheKey = `shots:${req.params.id}`;
    const cached = _vizCacheGet(cacheKey);
    if (cached) return res.json(cached);

    const shotLikeTypes = ['shot', 'goal', 'miss', 'attempt_saved', 'blocked_shot', 'chance_missed', 'post'];

    const events = await db.collection('match_events').find({
      $and: [
        buildEventMatchQuery(req.params.id),
        {
          $or: [
            { type_name: { $in: shotLikeTypes } },
            { analytical_xg: { $exists: true, $ne: null } },
            { shot_distance: { $exists: true, $ne: null } },
          ],
        },
        { 'location.x': { $exists: true } },
        { 'location.y': { $exists: true } },
      ],
    }).toArray();

    const data = events.map(e => {
      const x = e.location?.x ?? 0;
      const y = e.location?.y ?? 0;
      const dist = Math.sqrt(Math.pow(x - 100, 2) + Math.pow(y - 50, 2));
      const xg = Math.round(Math.exp(-dist / 30) * 10000) / 10000;

      return {
        id: String(e._id),
        player_id: String(e.player_id || e.playerID || ''),
        player_name: e.player_name || `Player ${e.player_id || 'Unknown'}`,
        x,
        y,
        is_goal: !!e.is_goal,
        xg,
        is_successful: !!e.is_goal,
        body_part: e.raw_event?.body_part || 'foot',
        shot_type: e.raw_event?.shot_type || 'regular',
        minute: e.minute ?? null,
        period: e.period ?? null,
        timestamp: e.minute != null ? `${e.minute}'` : '',
      };
    });

    const result = { success: true, data };
    _vizCacheSet(cacheKey, result);
    res.json(result);
  } catch (error) {
    console.error('Shots map error:', error);
    sendGatewayError(res, error, 'Failed to fetch shots map');
  }
});

// GET /api/matches/:id/heat-map — returns a pre-computed 10×10 grid (cached)
router.get('/:id/heat-map', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.json({ success: true, data: { grid: {}, cellCounts: {}, maxIntensity: 1, totalPoints: 0 } });
    }

    const { team_id, player_id } = req.query;
    const cacheKey = `heatmap:${req.params.id}:${team_id || ''}:${player_id || ''}`;
    const cached = _vizCacheGet(cacheKey);
    if (cached) return res.json(cached);

    const query = {
      ...buildEventMatchQuery(req.params.id),
      'location.x': { $exists: true },
      'location.y': { $exists: true }
    };

    if (team_id) query.team_id = normalizeTeamIdQuery(team_id);
    if (player_id) query.player_id = isNaN(Number(player_id)) ? player_id : { $in: [player_id, Number(player_id)] };

    const events = await db.collection('match_events').find(query).toArray();

    const points = events.map(e => ({
      x: e.location.x,
      y: e.location.y,
      intensity: 1,
      player_name: e.player_name || `Player ${e.player_id || 'Unknown'}`
    }));

    // Pre-compute grid on the backend so the frontend only renders
    const gridData = computeHeatmapGrid(points);
    const result = { success: true, data: gridData };
    _vizCacheSet(cacheKey, result);
    res.json(result);
  } catch (error) {
    console.error('Heat map error:', error);
    sendGatewayError(res, error, 'Failed to fetch heat map');
  }
});

// GET /api/matches/:id/pass-map
router.get('/:id/pass-map', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.json({ success: true, data: { players: [], connections: [] } });
    }

    const { team_id } = req.query;
    const cacheKey = `passmap:${req.params.id}:${team_id || ''}`;
    const cached = _vizCacheGet(cacheKey);
    if (cached) return res.json(cached);

    const query = {
      ...buildEventMatchQuery(req.params.id),
      type_name: 'pass',
      'location.x': { $exists: true },
      'location.y': { $exists: true }
    };

    if (team_id) query.team_id = normalizeTeamIdQuery(team_id);

    const events = await db.collection('match_events').find(query).toArray();

    // Group passes by player
    const playersMap = {};
    const connectionsMap = {};

    events.forEach((p, i) => {
      const pid = String(p.player_id || 'unknown');
      if (!playersMap[pid]) {
        playersMap[pid] = {
          player_id: pid,
          player_name: p.player_name || `Player ${pid}`,
          totalX: 0,
          totalY: 0,
          touches: 0,
          passes: 0
        };
      }
      
      playersMap[pid].touches += 1;
      playersMap[pid].passes += 1;
      playersMap[pid].totalX += p.location.x;
      playersMap[pid].totalY += p.location.y;

      // Simplistic assumption: next event might be receiver if successful 
      // For accurate Pass Network, need to compute receiver_id
      // We will try an educated guess or mock a receiver for visualization purposes if not found
      const nextEv = events[i + 1];
      if (nextEv && nextEv.team_id === p.team_id && nextEv.player_id && nextEv.player_id !== p.player_id) {
        const receiverId = String(nextEv.player_id);
        const pair = [pid, receiverId].sort().join('-'); // undirected
        
        if (!connectionsMap[pair]) {
          connectionsMap[pair] = {
            from_player_id: pid,
            to_player_id: receiverId,
            passes: 0,
            successful: 0
          };
        }
        connectionsMap[pair].passes += 1;
        // In Opta, outcome=1 (or similar) means successful. If outcome=1, we consider it smooth
        const isSuccess = p.raw_event?.outcome === 1 || p.qualifiers?.['140'] ? 1 : 0; 
        connectionsMap[pair].successful += isSuccess;
      }
    });

    const players = Object.values(playersMap).map(pv => ({
      player_id: pv.player_id,
      player_name: pv.player_name,
      x: pv.totalX / pv.touches,
      y: pv.totalY / pv.touches,
      touches: pv.touches,
      passes: pv.passes
    }));

    const connections = Object.values(connectionsMap).map(conn => ({
      from_player_id: conn.from_player_id,
      to_player_id: conn.to_player_id,
      passes: conn.passes,
      accuracy: conn.passes > 0 ? Math.round((conn.successful / conn.passes) * 100) : 0
    })).filter(c => c.passes > 2); // only show connections with > 2 passes

    const result = { success: true, data: { players, connections } };
    _vizCacheSet(cacheKey, result);
    res.json(result);
  } catch (error) {
    console.error('Pass map error:', error);
    sendGatewayError(res, error, 'Failed to fetch pass map');
  }
});

// GET /api/matches/:id/events/filter — filter F24 events by type/team/player/period
router.get('/:id/events/filter', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.json({ success: true, data: [], count: 0 });

    const { type_name, team_id, player_id, period } = req.query;

    const query = { ...buildEventMatchQuery(req.params.id) };

    if (type_name) query.type_name = type_name;
    if (period) query.period = Number(period);
    if (team_id) {
      const tidNum = Number(team_id);
      query.team_id = Number.isFinite(tidNum)
        ? { $in: [team_id, tidNum] }
        : team_id;
    }
    if (player_id) {
      const pidNum = Number(player_id);
      const pidVariants = Number.isFinite(pidNum) ? [player_id, pidNum] : [player_id];
      query.$and = query.$and || [];
      query.$and.push({
        $or: [
          { player_id: { $in: pidVariants } },
          { playerID: { $in: pidVariants } },
        ],
      });
    }

    const events = await db.collection('match_events')
      .find(query)
      .sort({ timestamp: 1 })
      .toArray();
    events.forEach(e => { delete e._id; });

    res.json({ success: true, data: events, count: events.length });
  } catch (error) {
    console.error('Events filter error:', error);
    sendGatewayError(res, error, 'Failed to filter match events');
  }
});

// GET /api/matches/:id/players/:playerId/stats — per-player per-match aggregated F24 stats
router.get('/:id/players/:playerId/stats', async (req, res) => {
  try {
    const analyticsServiceUrl = (process.env.ANALYTICS_SERVICE_URL || 'http://analytics-service:8012').replace(/\/$/, '');
    const payload = await requestJson(
      analyticsServiceUrl,
      `/api/v2/analytics/match/${req.params.id}/player/${req.params.playerId}/stats`,
      { timeoutMs: 15000 }
    );
    if (!payload.ok) {
      return res.status(payload.status || 502).json(payload.payload || { error: 'Analytics unavailable' });
    }
    res.json(payload.payload);
  } catch (error) {
    console.error('Player match stats error:', error);
    sendGatewayError(res, error, 'Failed to fetch player match stats');
  }
});

// GET /api/matches/:id/viz?home_team_id=X&away_team_id=Y
// Consolidated endpoint: returns shots + both heatmaps + both pass-networks in one call.
// Eliminates 5 parallel round-trips from the match detail page.
router.get('/:id/viz', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      console.info(`[match-viz] match=${req.params.id} db=missing`);
      return res.json({ success: true, data: { shots: [], heatmap_home: null, heatmap_away: null, home_passes: { players: [], connections: [] }, away_passes: { players: [], connections: [] } } });
    }

    const matchId = req.params.id;
    const { home_team_id, away_team_id } = req.query;

    const cacheKey = `viz:${matchId}:${home_team_id || ''}:${away_team_id || ''}`;
    const cached = _vizCacheGet(cacheKey);
    if (cached) {
      console.info(`[match-viz] match=${matchId} cache=hit home=${home_team_id || '-'} away=${away_team_id || '-'} shots=${cached?.data?.shots?.length || 0} homeHeat=${cached?.data?.heatmap_home?.totalPoints || 0} awayHeat=${cached?.data?.heatmap_away?.totalPoints || 0} homePassPlayers=${cached?.data?.pass_network_home?.players?.length || 0} awayPassPlayers=${cached?.data?.pass_network_away?.players?.length || 0}`);
      return res.json(cached);
    }

    const matchQuery = buildEventMatchQuery(matchId);
    const hasLocation = { 'location.x': { $exists: true }, 'location.y': { $exists: true } };

    // Resolve ScoutPro IDs, raw Opta numeric IDs, and t-prefixed Opta IDs to the
    // raw Opta team_id strings stored on match_events documents.
    async function resolveOptaTeamId(scoutproId) {
      if (!scoutproId) return null;
      const rawId = String(scoutproId).trim();
      const normalizedId = normalizeTeamIdValue(rawId);

      if (/^t\d+$/i.test(rawId)) return normalizedId;
      if (/^\d+$/.test(rawId) && rawId.length <= 10) return rawId;

      let teamDoc = null;
      const lookupClauses = [];
      for (const variant of collectTeamIdVariants(rawId)) {
        lookupClauses.push({ uID: variant });
        lookupClauses.push({ id: variant });
        lookupClauses.push({ scoutpro_id: variant });
        lookupClauses.push({ 'provider_ids.opta': variant });
      }

      try {
        lookupClauses.push({ scoutpro_id: Long.fromString(rawId) });
        lookupClauses.push({ id: Long.fromString(rawId) });
      } catch (_) { /* invalid Long string */ }
      try {
        if (normalizedId !== rawId) {
          lookupClauses.push({ scoutpro_id: Long.fromString(normalizedId) });
          lookupClauses.push({ id: Long.fromString(normalizedId) });
        }
      } catch (_) { /* invalid Long string */ }

      teamDoc = await db.collection('teams').findOne(
        { $or: lookupClauses },
        { projection: { uID: 1, provider_ids: 1 } }
      );

      if (!teamDoc) return null;

      const providerOpta = teamDoc.provider_ids?.opta;
      if (providerOpta != null) return normalizeTeamIdValue(providerOpta);

      const uid = normalizeTeamIdValue(teamDoc.uID || '');
      return uid || null;
    }

    const [optaHomeId, optaAwayId] = await Promise.all([
      resolveOptaTeamId(home_team_id),
      resolveOptaTeamId(away_team_id),
    ]);

    // Build team_id filter for events using resolved Opta IDs
    function teamFilter(optaId) {
      if (!optaId) return null;
      const num = Number(optaId);
      const vals = [optaId];
      if (!isNaN(num) && num <= Number.MAX_SAFE_INTEGER) vals.push(num);
      return { $in: vals };
    }

    const homeTeamFilter = optaHomeId ? teamFilter(optaHomeId) : null;
    const awayTeamFilter = optaAwayId ? teamFilter(optaAwayId) : null;

    // If ScoutPro ID resolution failed, try the raw Opta team IDs stored on the match doc
    async function getMatchDoc() {
      try {
        return await db.collection('matches').findOne(buildMatchQuery(matchId),
          { projection: { home_opta_team_id: 1, away_opta_team_id: 1, home_team_name: 1, away_team_name: 1 } });
      } catch (_) { return null; }
    }
    let effectiveHomeFilter = homeTeamFilter;
    let effectiveAwayFilter = awayTeamFilter;
    if (!effectiveHomeFilter || !effectiveAwayFilter) {
      const matchDoc = await getMatchDoc();
      if (matchDoc) {
        if (!effectiveHomeFilter && matchDoc.home_opta_team_id) {
          effectiveHomeFilter = teamFilter(String(matchDoc.home_opta_team_id));
        }
        if (!effectiveAwayFilter && matchDoc.away_opta_team_id) {
          effectiveAwayFilter = teamFilter(String(matchDoc.away_opta_team_id));
        }
      }
    }

    const [shotEvents, allLocationEvents, allPassEvents] = await Promise.all([
      // shots — include all shot-like events regardless of team
      db.collection('match_events').find({
        $and: [
          matchQuery,
          { $or: [
            { type_name: { $in: ['shot', 'goal', 'miss', 'attempt_saved', 'blocked_shot', 'chance_missed', 'post'] } },
            { analytical_xg: { $exists: true, $ne: null } },
            { shot_distance: { $exists: true, $ne: null } },
          ]},
          hasLocation,
        ],
      }).toArray(),
      // all events with location for heatmap filtering
      db.collection('match_events').find({ ...matchQuery, ...hasLocation }).toArray(),
      // pass events are fetched once and split by inferred team IDs below.
      db.collection('match_events').find({
        ...matchQuery,
        type_name: 'pass',
        ...hasLocation,
      }).toArray(),
    ]);

    // --- shots ---
    const shots = shotEvents.map(e => {
      const x = e.location?.x ?? 0;
      const y = e.location?.y ?? 0;
      const dist = Math.sqrt(Math.pow(x - 100, 2) + Math.pow(y - 50, 2));
      return {
        id: String(e._id),
        player_id: String(e.player_id || e.playerID || ''),
        player_name: e.player_name || `Player ${e.player_id || 'Unknown'}`,
        opta_id: e.player_id || e.playerID,
        x, y,
        is_goal: !!e.is_goal,
        xg: Math.round(Math.exp(-dist / 30) * 10000) / 10000,
        is_successful: !!e.is_goal,
        body_part: e.raw_event?.body_part || 'foot',
        shot_type: e.raw_event?.shot_type || 'regular',
        minute: e.minute ?? null,
        period: e.period ?? null,
        timestamp: e.minute != null ? `${e.minute}'` : '',
      };
    });

    // Enrich shots with real player names and ScoutPro IDs
    async function enrichShotsWithRealNames(shotList) {
      return Promise.all(
        shotList.map(async (shot) => {
          const playerInfo = await getPlayerInfo(shot.opta_id);
          return {
            ...shot,
            scoutpro_player_id: playerInfo.scoutproId,
            player_name: playerInfo.name,
          };
        })
      );
    }

    // --- heatmaps: filter by Opta team_id from the already-fetched allLocationEvents ---
    function filterByOptaTeam(events, optaId) {
      if (!optaId) return events;
      const num = Number(optaId);
      return events.filter(e => String(e.team_id) === optaId || (Number.isFinite(num) && e.team_id === num));
    }

    // Extract the raw Opta team ID string from the effective filter (if it was resolved)
    function extractOptaIdFromFilter(filter) {
      if (!filter || !filter.$in) return null;
      const strVals = filter.$in.filter(v => typeof v === 'string');
      return strVals[0] || null;
    }

    let effectiveHomeOptaId = optaHomeId || extractOptaIdFromFilter(effectiveHomeFilter);
    let effectiveAwayOptaId = optaAwayId || extractOptaIdFromFilter(effectiveAwayFilter);

    function inferTeamIds(events) {
      const counts = new Map();
      for (const event of events) {
        const teamId = extractEventTeamId(event);
        if (!teamId) continue;
        counts.set(teamId, (counts.get(teamId) || 0) + 1);
      }
      return Array.from(counts.entries())
        .sort((left, right) => right[1] - left[1])
        .map(([teamId]) => teamId);
    }

    const inferredTeamIds = inferTeamIds(allPassEvents.length ? allPassEvents : allLocationEvents);
    if (!effectiveHomeOptaId) {
      effectiveHomeOptaId = inferredTeamIds[0] || null;
    }
    if (!effectiveAwayOptaId) {
      effectiveAwayOptaId = inferredTeamIds.find(teamId => teamId !== effectiveHomeOptaId) || null;
    }

    const homePoints = filterByOptaTeam(allLocationEvents, effectiveHomeOptaId)
      .map(e => ({ x: e.location.x, y: e.location.y, intensity: 1 }));
    const awayPoints = filterByOptaTeam(allLocationEvents, effectiveAwayOptaId)
      .map(e => ({ x: e.location.x, y: e.location.y, intensity: 1 }));

    // If no team IDs provided or resolution failed, split by distinct team_ids
    const fallbackPoints = (!effectiveHomeOptaId && !effectiveAwayOptaId)
      ? allLocationEvents.map(e => ({ x: e.location.x, y: e.location.y, intensity: 1 }))
      : null;

    const homePassEvents = filterByOptaTeam(allPassEvents, effectiveHomeOptaId);
    const awayPassEvents = filterByOptaTeam(allPassEvents, effectiveAwayOptaId);

    // Cache for player lookup (Opta ID → { scoutproId, name })
    const playerLookupCache = new Map();
    async function getPlayerInfo(optaPlayerId) {
      const optaIdStr = String(optaPlayerId || '');
      if (!optaIdStr) return { scoutproId: null, name: 'Unknown' };

      if (playerLookupCache.has(optaIdStr)) {
        return playerLookupCache.get(optaIdStr);
      }

      try {
        const playerDoc = await db.collection('players').findOne(
          { $or: [{ 'provider_ids.opta': optaIdStr }, { uID: `p${optaIdStr}` }] },
          { projection: { scoutpro_id: 1, id: 1, name: 1, first_name: 1, last_name: 1 } }
        );
        
        if (playerDoc) {
          const scoutproId = playerDoc.scoutpro_id ?? playerDoc.id;
          const name = playerDoc.name || [playerDoc.first_name, playerDoc.last_name].filter(Boolean).join(' ') || `Player ${optaIdStr}`;
          const result = { scoutproId: String(scoutproId), name };
          playerLookupCache.set(optaIdStr, result);
          return result;
        }
      } catch (err) {
        console.warn(`Player lookup failed for Opta ID ${optaIdStr}:`, err.message);
      }

      const notFound = { scoutproId: null, name: `Player ${optaIdStr}` };
      playerLookupCache.set(optaIdStr, notFound);
      return notFound;
    }

    // --- pass networks ---
    function buildPassNetwork(passEvents) {
      const playersMap = {};
      const connectionsMap = {};
      passEvents.forEach((p, i) => {
        const pid = String(p.player_id || 'unknown');
        if (!playersMap[pid]) {
          playersMap[pid] = { player_id: pid, player_name: p.player_name || `Player ${pid}`, totalX: 0, totalY: 0, touches: 0, passes: 0, opta_id: p.player_id };
        }
        playersMap[pid].touches++;
        playersMap[pid].passes++;
        playersMap[pid].totalX += p.location.x;
        playersMap[pid].totalY += p.location.y;
        const nextEv = passEvents[i + 1];
        if (nextEv && nextEv.team_id === p.team_id && nextEv.player_id && nextEv.player_id !== p.player_id) {
          const receiverId = String(nextEv.player_id);
          const pair = [pid, receiverId].sort().join('-');
          if (!connectionsMap[pair]) {
            connectionsMap[pair] = { from_player_id: pid, to_player_id: receiverId, passes: 0, successful: 0 };
          }
          connectionsMap[pair].passes++;
          connectionsMap[pair].successful += (p.raw_event?.outcome === 1 || p.qualifiers?.['140']) ? 1 : 0;
        }
      });
      const players = Object.values(playersMap).map(pv => ({
        player_id: pv.player_id, player_name: pv.player_name, opta_id: pv.opta_id,
        x: pv.totalX / pv.touches, y: pv.totalY / pv.touches,
        touches: pv.touches, passes: pv.passes,
      }));
      const connections = Object.values(connectionsMap)
        .filter(c => c.passes > 2)
        .map(c => ({ from_player_id: c.from_player_id, to_player_id: c.to_player_id, passes: c.passes, accuracy: Math.round((c.successful / c.passes) * 100) }));
      return { players, connections };
    }

    // Build visualizations with player info
    const homePassNet = buildPassNetwork(homePassEvents);
    const awayPassNet = buildPassNetwork(awayPassEvents);

    // Resolve ScoutPro IDs and real names for pass network players
    async function enrichPassNetworkWithRealNames(passNet) {
      if (!passNet || !passNet.players) return passNet;
      
      const enrichedPlayers = await Promise.all(
        passNet.players.map(async (player) => {
          const playerInfo = await getPlayerInfo(player.opta_id);
          return {
            ...player,
            scoutpro_id: playerInfo.scoutproId,
            player_name: playerInfo.name,
          };
        })
      );

      return {
        ...passNet,
        players: enrichedPlayers,
      };
    }

    // Enrich with real player names and ScoutPro IDs
    const enrichedShots = await enrichShotsWithRealNames(shots);
    const enrichedHomePassNet = await enrichPassNetworkWithRealNames(homePassNet);
    const enrichedAwayPassNet = await enrichPassNetworkWithRealNames(awayPassNet);

    const result = {
      success: true,
      data: {
        shots: enrichedShots,
        heatmap_home: computeHeatmapGrid(homePoints.length ? homePoints : (fallbackPoints || [])),
        heatmap_away: computeHeatmapGrid(awayPoints),
        pass_network_home: enrichedHomePassNet,
        pass_network_away: enrichedAwayPassNet,
      },
    };

    console.info(`[match-viz] match=${matchId} cache=miss resolvedHome=${effectiveHomeOptaId || '-'} resolvedAway=${effectiveAwayOptaId || '-'} shots=${enrichedShots.length} homeHeat=${result.data.heatmap_home?.totalPoints || 0} awayHeat=${result.data.heatmap_away?.totalPoints || 0} homePassPlayers=${enrichedHomePassNet?.players?.length || 0} awayPassPlayers=${enrichedAwayPassNet?.players?.length || 0}`);

    _vizCacheSet(cacheKey, result);
    res.json(result);
  } catch (error) {
    console.error('Match viz error:', error);
    sendGatewayError(res, error, 'Failed to fetch match visualization data');
  }
});

router.get('/:id', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(matchServiceUrl, `/api/v2/matches/${req.params.id}`),
      'Failed to fetch match'
    );

    const raw = unwrapPayload(payload);
    res.json(toFrontendMatch(normalizeEntity(raw)));
  } catch (error) {
    console.error('Match get error:', error);
    sendGatewayError(res, error, 'Failed to fetch match');
  }
});

// GET /api/matches/:id/lineup  — F9 lineup from MongoDB (does not require match-service)
// f9_summary is stored as an array: [{team_ref, side, score, lineup:[{player_ref,position,shirt_number,status}], goals, bookings, team_stats}, ...]
router.get('/:id/lineup', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.json({ teams: [], data_source: 'unavailable' });

    const match = await db.collection('matches').findOne(
      buildMatchQuery(req.params.id),
      { projection: { f9_summary: 1, homeTeamName: 1, awayTeamName: 1,
                      homeTeamID: 1, awayTeamID: 1, homeScore: 1, awayScore: 1, uID: 1 } },
    );

    if (!match) return res.status(404).json({ error: 'Match not found' });

    const f9 = match.f9_summary;
    if (!f9 || (Array.isArray(f9) && f9.length === 0)) {
      return res.json({
        match_id: match.uID,
        homeTeam: match.homeTeamName,
        awayTeam: match.awayTeamName,
        homeScore: match.homeScore,
        awayScore: match.awayScore,
        teams: [],
        data_source: 'no_f9_data',
        message: 'No F9 lineup data available for this match.',
      });
    }

    // f9_summary is an array indexed by position [home, away]
    const rawTeams = Array.isArray(f9) ? f9 : Object.values(f9);

    // Collect all player_refs so we can batch-resolve names from the players collection
    const allPlayerRefs = rawTeams.flatMap(t =>
      (t.lineup || []).map(p => String(p.player_ref)).filter(Boolean)
    );
    const playerDocs = allPlayerRefs.length
      ? await db.collection('players').find(
          { uID: { $in: allPlayerRefs } },
          { projection: { uID: 1, name: 1, first: 1, last: 1, position: 1, nationality: 1 } },
        ).toArray()
      : [];
    const playerMap = {};
    playerDocs.forEach(p => { playerMap[p.uID] = p; });

    // Resolve team names from DB
    const teamRefs = rawTeams.map(t => String(t.team_ref)).filter(Boolean);
    const teamDocs = teamRefs.length
      ? await db.collection('teams').find(
          { uID: { $in: teamRefs } },
          { projection: { uID: 1, name: 1 } },
        ).toArray()
      : [];
    const teamMap = {};
    teamDocs.forEach(t => { teamMap[t.uID] = t.name; });

    const teams = rawTeams.map(t => ({
      team_id: String(t.team_ref),
      team_name: teamMap[String(t.team_ref)] || (t.side === 'home' ? match.homeTeamName : match.awayTeamName) || `Team ${t.team_ref}`,
      side: t.side,
      score: t.score,
      formation: t.formation || null,
      lineup: (t.lineup || []).map(p => {
        const pInfo = playerMap[String(p.player_ref)] || {};
        return {
          player_id: String(p.player_ref),
          player_name: pInfo.name || `Player ${p.player_ref}`,
          position: p.position || pInfo.position || '',
          shirt_number: p.shirt_number,
          status: p.status,  // 'Start' or 'Sub'
          nationality: pInfo.nationality || null,
        };
      }),
      goals: (t.goals || []).map(g => {
        const scorer = playerMap[String(g.player_ref)] || {};
        const assister = g.assist ? (playerMap[String(g.assist.player_ref)] || {}) : null;
        return {
          player: scorer.name || `Player ${g.player_ref}`,
          minute: g.min,
          period: g.period,
          assist: assister ? assister.name : null,
        };
      }),
      bookings: (t.bookings || []).map(b => {
        const booked = playerMap[String(b.player_ref)] || {};
        return {
          player: booked.name || `Player ${b.player_ref}`,
          card: b.card,
          minute: b.min,
        };
      }),
      substitutions: (t.substitutions || []).map(s => {
        const pIn = playerMap[String(s.player_ref)] || {};
        const pOut = playerMap[String(s.player_off_ref)] || {};
        return {
          player_on: pIn.name || `Player ${s.player_ref}`,
          player_off: pOut.name || `Player ${s.player_off_ref}`,
          minute: s.min,
        };
      }),
    }));

    res.json({
      match_id: match.uID,
      homeTeam: match.homeTeamName,
      awayTeam: match.awayTeamName,
      homeScore: match.homeScore,
      awayScore: match.awayScore,
      teams,
      data_source: 'opta_f9',
    });
  } catch (error) {
    console.error('Match lineup error:', error);
    res.status(500).json({ error: 'Failed to fetch match lineup' });
  }
});

router.post('/', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(matchServiceUrl, '/api/v2/matches', {
        method: 'POST',
        body: req.body,
      }),
      'Failed to create match'
    );

    res.status(201).json(unwrapPayload(payload));
  } catch (error) {
    console.error('Match create error:', error);
    sendGatewayError(res, error, 'Failed to create match');
  }
});

router.put('/:id', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(matchServiceUrl, `/api/v2/matches/${req.params.id}`, {
        method: 'PUT',
        body: req.body,
      }),
      'Failed to update match'
    );

    res.json(unwrapPayload(payload));
  } catch (error) {
    console.error('Match update error:', error);
    sendGatewayError(res, error, 'Failed to update match');
  }
});

/**
 * GET /api/matches/enriched/list
 * Returns matches with enriched team names from MongoDB.
 */
router.get('/enriched/list', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.json({ success: true, data: [], total: 0, limit: 50, skip: 0 });
    }

    const limit = Math.min(parseInt(req.query.limit) || 50, 500);
    const skip = Math.max(parseInt(req.query.skip) || 0, 0);

    const matches = await db
      .collection('matches')
      .find({})
      .sort({ date: -1 })
      .skip(skip)
      .limit(limit)
      .toArray();

    const total = await db.collection('matches').countDocuments({});

    // Convert to frontend format
    const formatted = matches.map(m => ({
      id: String(m.uID || m._id || '').replace(/^g/, ''),
      homeTeam: m.home_team || `Team ${m.homeTeamID || ''}`,
      awayTeam: m.away_team || `Team ${m.awayTeamID || ''}`,
      homeTeamId: String(m.homeTeamID || ''),
      awayTeamId: String(m.awayTeamID || ''),
      homeScore: m.homeScore || 0,
      awayScore: m.awayScore || 0,
      date: m.date || null,
      status: m.status || 'unknown',
    }));

    res.json({
      success: true,
      data: formatted,
      pagination: {
        total,
        skip,
        limit,
        pages: Math.ceil(total / limit),
      },
    });
  } catch (error) {
    console.error('Enriched matches error:', error);
    sendGatewayError(res, error, 'Failed to fetch enriched matches');
  }
});

module.exports = router;
