/**
 * Statistics Routes - Proxies to statistics-service.
 * Rankings are enriched with player/team names by calling player-service and team-service.
 */
const express = require('express');
const router = express.Router();

const {
  ensureSuccess,
  requestJson,
  sendGatewayError,
  unwrapPayload,
} = require('../utils/serviceClient');

const statisticsServiceUrl = (process.env.STATISTICS_SERVICE_URL || 'http://statistics-service:8000').replace(/\/$/, '');
const playerServiceUrl = (process.env.PLAYER_SERVICE_URL || 'http://player-service:8000').replace(/\/$/, '');
const teamServiceUrl = (process.env.TEAM_SERVICE_URL || 'http://team-service:8000').replace(/\/$/, '');

// GET /api/statistics — root summary
router.get('/', (req, res) => {
  res.json({
    status: 'active',
    endpoints: {
      playerStats:  '/api/statistics/player/:playerId',
      teamStats:    '/api/statistics/team/:teamId',
      playerRankings: '/api/statistics/rankings/players',
      teamRankings:   '/api/statistics/rankings/teams',
      comparePlayers: '/api/statistics/compare/players',
      aggregatePlayer: '/api/statistics/aggregate/player/:playerId',
    },
  });
});

router.get('/player/:playerId', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(statisticsServiceUrl, `/api/v2/statistics/player/${req.params.playerId}`, {
        query: {
          competition_id: req.query.competition_id,
          season_id: req.query.season_id,
          per_90: req.query.per_90,
        },
      }),
      'Failed to fetch player statistics'
    );

    res.json(unwrapPayload(payload));
  } catch (error) {
    console.error('Player statistics error:', error);
    sendGatewayError(res, error, 'Failed to fetch player statistics');
  }
});

router.get('/team/:teamId', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(statisticsServiceUrl, `/api/v2/statistics/team/${req.params.teamId}`, {
        query: {
          competition_id: req.query.competition_id,
          season_id: req.query.season_id,
        },
      }),
      'Failed to fetch team statistics'
    );

    res.json(unwrapPayload(payload));
  } catch (error) {
    console.error('Team statistics error:', error);
    sendGatewayError(res, error, 'Failed to fetch team statistics');
  }
});

router.get('/rankings/players', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(statisticsServiceUrl, '/api/v2/statistics/rankings/players', {
        query: {
          stat_name: req.query.stat_name || 'passes',  // default to passes when not specified
          position: req.query.position,
          competition_id: req.query.competition_id,
          limit: req.query.limit || 50,
        },
      }),
      'Failed to fetch player rankings'
    );

    const rankingRows = unwrapPayload(payload) || [];

    // The statistics-service now resolves player_name/player_position/player_team itself.
    // Enrich further via player-service only when the service couldn't resolve the name.
    const enriched = await Promise.all(
      rankingRows.map(async (row) => {
        const pid = String(row.playerID || row.player_id || '');
        let name = row.player_name || null;
        let position = row.player_position || null;
        let club = row.player_team || null;

        if (!name) {
          // Fallback: ask player-service (works when ID is in F40 namespace)
          try {
            const pResult = await requestJson(playerServiceUrl, `/api/v2/players/${pid}`, { timeoutMs: 1000 });
            if (pResult?.ok) {
              const p = pResult.payload?.player || pResult.payload || {};
              name = p.name || null;
              position = position || p.position || null;
              club = club || p.team_name || p.club || null;
            }
          } catch (_) { /* F24 namespace — no match in F40 player-service */ }
        }

        return {
          ...row,
          name: name || `Player ${pid}`,
          position,
          club,
          value: row.passes || row.total_events || 0,
          rank: row.rank || null,
        };
      })
    );

    res.json(enriched);
  } catch (error) {
    console.error('Player rankings error:', error);
    sendGatewayError(res, error, 'Failed to fetch player rankings');
  }
});

router.get('/rankings/teams', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(statisticsServiceUrl, '/api/v2/statistics/rankings/teams', {
        query: {
          stat_name: req.query.stat_name || 'passes',  // default to passes
          competition_id: req.query.competition_id,
          limit: req.query.limit || 50,
        },
      }),
      'Failed to fetch team rankings'
    );

    const rankingRows = unwrapPayload(payload) || [];

    // Statistics-service now resolves team_name/team_country itself.
    // Fall back to team-service only when not resolved.
    const enriched = await Promise.all(
      rankingRows.map(async (row) => {
        const tid = String(row.teamID || row.team_id || '');
        let name = row.team_name || null;
        let country = row.team_country || null;

        if (!name) {
          try {
            const tResult = await requestJson(teamServiceUrl, `/api/v2/teams/${tid}`, { timeoutMs: 1000 });
            if (tResult?.ok) {
              const t = tResult.payload?.team || tResult.payload || {};
              name = t.name || null;
              country = country || t.country || null;
            }
          } catch (_) { /* team not found */ }
        }

        return {
          ...row,
          name: name || `Team ${tid}`,
          country,
          value: row.total_events || row.passes || 0,
          rank: row.rank || null,
        };
      })
    );

    // Deduplicate teams that appear under multiple Opta IDs (e.g. Besiktas/Beşiktaş).
    // Normalise name for comparison: strip accents and lowercase.
    function normaliseName(n) {
      return (n || '')
        .toLowerCase()
        .replace(/ş/g, 's').replace(/ğ/g, 'g').replace(/ı/g, 'i')
        .replace(/ö/g, 'o').replace(/ü/g, 'u').replace(/ç/g, 'c')
        .replace(/[^a-z0-9]/g, '');
    }
    const seen = new Map(); // normalisedName → index in deduplicated array
    const deduplicated = [];
    for (const row of enriched) {
      const key = normaliseName(row.name);
      if (seen.has(key)) {
        // Merge: add passes/value to the existing entry
        const existing = deduplicated[seen.get(key)];
        existing.value = (existing.value || 0) + (row.value || 0);
        existing.passes = (existing.passes || 0) + (row.passes || 0);
      } else {
        seen.set(key, deduplicated.length);
        deduplicated.push({ ...row });
      }
    }
    // Re-rank after deduplication
    deduplicated.sort((a, b) => (b.passes || b.value || 0) - (a.passes || a.value || 0));
    deduplicated.forEach((r, i) => { r.rank = i + 1; });

    res.json(deduplicated);
  } catch (error) {
    console.error('Team rankings error:', error);
    sendGatewayError(res, error, 'Failed to fetch team rankings');
  }
});

router.post('/compare/players', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(statisticsServiceUrl, '/api/v2/statistics/compare/players', {
        method: 'POST',
        body: req.body,
      }),
      'Failed to compare players'
    );

    res.json(unwrapPayload(payload));
  } catch (error) {
    console.error('Compare players error:', error);
    sendGatewayError(res, error, 'Failed to compare players');
  }
});

router.get('/aggregate/player/:playerId', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(statisticsServiceUrl, `/api/v2/statistics/aggregate/player/${req.params.playerId}`, {
        query: {
          start_date: req.query.start_date,
          end_date: req.query.end_date,
        },
      }),
      'Failed to aggregate player statistics'
    );

    res.json(unwrapPayload(payload));
  } catch (error) {
    console.error('Aggregate player statistics error:', error);
    sendGatewayError(res, error, 'Failed to aggregate player statistics');
  }
});

module.exports = router;