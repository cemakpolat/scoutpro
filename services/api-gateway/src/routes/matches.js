/**
 * Matches Routes - Proxies to match-service (which owns MongoDB access).
 * Normalizes the service response to the unified frontend Match shape.
 */
const express = require('express');
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
 * Map a match-service response object to the frontend Match interface.
 * The service returns snake_case (home_team_id, home_score, home_team_name …)
 * after going through _normalize_match_doc; the frontend expects camelCase.
 */
function toFrontendMatch(m) {
  if (!m) return null;

  const status = (() => {
    const s = (m.status || '').toLowerCase();
    if (s === 'played' || s === 'finished') return 'finished';
    if (s === 'fixture' || s === 'scheduled' || s === '') return 'scheduled';
    return s;
  })();

  return {
    id: String(m.id || m.uID || ''),
    homeTeam: m.home_team_name || m.homeTeamName || m.home_team || `Team ${m.home_team_id || m.homeTeamID || ''}`,
    awayTeam: m.away_team_name || m.awayTeamName || m.away_team || `Team ${m.away_team_id || m.awayTeamID || ''}`,
    homeTeamId: String(m.home_team_id || m.homeTeamID || ''),
    awayTeamId: String(m.away_team_id || m.awayTeamID || ''),
    homeScore: m.home_score ?? m.homeScore ?? 0,
    awayScore: m.away_score ?? m.awayScore ?? 0,
    date: m.date || null,
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
      if (req.query.status) query.status = new RegExp(`^${escapeRegex(req.query.status)}$`, 'i');
      if (req.query.team_id) query.$or = [{ homeTeamId: req.query.team_id }, { awayTeamId: req.query.team_id }];

      // Pull all matches, sort finished first then by date desc
      const docs = await db.collection('matches').find(query).limit(limit * 3).toArray();

      const statusRank = (s) => {
        const n = String(s || '').toLowerCase();
        if (n === 'finished' || n === 'played') return 0;
        if (n === 'live' || n === 'in_progress') return 1;
        return 2;
      };
      docs.sort((a, b) =>
        statusRank(a.status) - statusRank(b.status) ||
        new Date(b.date || 0) - new Date(a.date || 0)
      );

      return res.json(docs.slice(0, limit).map(toFrontendMatch).filter(Boolean));
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
    res.json((Array.isArray(raw) ? raw : (raw?.matches || [])).map(toFrontendMatch));
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
    res.json(list.map(toFrontendMatch));
  } catch (error) {
    console.error('Live matches error:', error);
    sendGatewayError(res, error, 'Failed to fetch live matches');
  }
});

router.get('/search', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.status(503).json({ success: false, error: 'Database not available' });
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
      query.status = new RegExp(`^${escapeRegex(status)}$`, 'i');
    }

    const matches = await db
      .collection('matches')
      .find(query)
      .sort({ status: 1, date: -1 })
      .limit(limit)
      .toArray();

    // Put finished matches first so picker shows real scores before scheduled fixtures
    const statusRank = (s) => {
      const n = String(s || '').toLowerCase();
      if (n === 'finished' || n === 'played') return 0;
      if (n === 'live') return 1;
      return 2;
    };
    matches.sort((a, b) => statusRank(a.status) - statusRank(b.status) || new Date(b.date || 0) - new Date(a.date || 0));

    res.json(matches.map(toFrontendMatch).filter(Boolean));
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

    const mIdNum = Number(req.params.id);
    const mIdStr = req.params.id;

    const events = await db.collection('match_events').find({
      $or: [
        { matchID: mIdNum }, { matchID: mIdStr },
        { match_id: mIdNum }, { match_id: mIdStr },
      ],
    }).toArray();

    const data = events.map(e => ({
      id: String(e._id),
      match_id: String(e.match_id || e.matchID || req.params.id),
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
      return res.status(503).json({ success: false, error: 'Database not available' });
    }

    const mIdNum = Number(req.params.id);
    const mIdStr = req.params.id;

    // Fetch all shots for this match
    const events = await db.collection('match_events').find({
      $or: [{ matchID: mIdNum }, { matchID: mIdStr }, { match_id: mIdNum }, { match_id: mIdStr }],
      type_name: 'shot'
    }).toArray();

    const data = events.map(e => ({
      id: String(e._id),
      player_id: String(e.player_id || ''),
      player_name: e.player_name || `Player ${e.player_id || 'Unknown'}`,
      x: e.location?.x || 0,
      y: e.location?.y || 0,
      is_goal: !!e.is_goal,
      xg: e.qualifiers?.expected_goals || 0,
      is_successful: !!e.is_goal,
      body_part: 'foot', // fallback or map from qualifiers if known
      shot_type: 'regular',
      timestamp: e.minute ? `${e.minute}'` : ''
    }));

    res.json({ success: true, data });
  } catch (error) {
    console.error('Shots map error:', error);
    sendGatewayError(res, error, 'Failed to fetch shots map');
  }
});

// GET /api/matches/:id/heat-map
router.get('/:id/heat-map', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.status(503).json({ success: false, error: 'Database not available' });
    }

    const { team_id, player_id } = req.query;
    const mIdNum = Number(req.params.id);
    const mIdStr = req.params.id;

    const query = {
      $or: [{ matchID: mIdNum }, { matchID: mIdStr }, { match_id: mIdNum }, { match_id: mIdStr }],
      'location.x': { $exists: true },
      'location.y': { $exists: true }
    };

    if (team_id) query.team_id = isNaN(Number(team_id)) ? team_id : { $in: [team_id, Number(team_id)] };
    if (player_id) query.player_id = isNaN(Number(player_id)) ? player_id : { $in: [player_id, Number(player_id)] };

    const events = await db.collection('match_events').find(query).toArray();

    // Map any positional event to a HeatMapData point
    const data = events.map(e => ({
      x: e.location.x,
      y: e.location.y,
      intensity: 1,
      count: 1,
      player_name: e.player_name || `Player ${e.player_id || 'Unknown'}`
    }));

    res.json({ success: true, data });
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
      return res.status(503).json({ success: false, error: 'Database not available' });
    }

    const { team_id } = req.query;
    const mIdNum = Number(req.params.id);
    const mIdStr = req.params.id;

    const query = {
      $or: [{ matchID: mIdNum }, { matchID: mIdStr }, { match_id: mIdNum }, { match_id: mIdStr }],
      type_name: 'pass',
      'location.x': { $exists: true },
      'location.y': { $exists: true }
    };

    if (team_id) query.team_id = isNaN(Number(team_id)) ? team_id : { $in: [team_id, Number(team_id)] };

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

    res.json({ success: true, data: { players, connections } });
  } catch (error) {
    console.error('Pass map error:', error);
    sendGatewayError(res, error, 'Failed to fetch pass map');
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

    const matchId = req.params.id;
    const match = await db.collection('matches').findOne(
      { $or: [{ uID: matchId }, { uID: Number(matchId) }] },
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
      return res.status(503).json({ success: false, error: 'Database not available' });
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
      id: String(m.uID || m._id || ''),
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
