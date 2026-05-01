/**
 * Analytics Routes - Compatibility layer over analytics-service.
 */
const express = require('express');
const router = express.Router();

const {
  ensureSuccess,
  requestJson,
  sendGatewayError,
  unwrapPayload,
} = require('../utils/serviceClient');

const analyticsServiceUrl = (process.env.ANALYTICS_SERVICE_URL || 'http://analytics-service:8012').replace(/\/$/, '');
const analyticsCompatCacheTtlMs = Number(process.env.ANALYTICS_COMPAT_CACHE_TTL_MS || 15000);
const analyticsCompatCache = new Map();

function hasOverviewData(payload) {
  if (!payload || typeof payload !== 'object') {
    return false;
  }

  const summary = payload.summary || payload.data || payload;
  return Boolean(
    Number(summary.totalPlayers || 0)
    || Number(summary.totalTeams || 0)
    || Number(summary.totalMatches || 0)
    || (Array.isArray(payload.topPlayers) && payload.topPlayers.length)
    || (Array.isArray(payload.topTeams) && payload.topTeams.length)
    || (Array.isArray(payload.recentMatches) && payload.recentMatches.length)
  );
}

function getCachedAnalytics(key, loader, options = {}) {
  const {
    ttlMs = analyticsCompatCacheTtlMs,
    allowStaleOnError = false,
    shouldCache = () => true,
  } = options;
  const now = Date.now();
  const cached = analyticsCompatCache.get(key);

  if (cached?.value !== undefined && cached.expiresAt > now) {
    return Promise.resolve(cached.value);
  }

  if (cached?.promise) {
    return cached.promise;
  }

  const promise = loader()
    .then((value) => {
      if (!shouldCache(value)) {
        if (cached?.value !== undefined) {
          analyticsCompatCache.set(key, {
            value: cached.value,
            expiresAt: cached.expiresAt,
            promise: null,
          });
        } else {
          analyticsCompatCache.delete(key);
        }
        return value;
      }

      analyticsCompatCache.set(key, {
        value,
        expiresAt: Date.now() + ttlMs,
        promise: null,
      });
      return value;
    })
    .catch((error) => {
      if (allowStaleOnError && cached?.value !== undefined) {
        analyticsCompatCache.set(key, {
          value: cached.value,
          expiresAt: cached.expiresAt,
          promise: null,
        });
        return cached.value;
      }

      analyticsCompatCache.delete(key);
      throw error;
    });

  analyticsCompatCache.set(key, {
    value: cached?.value,
    expiresAt: cached?.expiresAt || 0,
    promise,
  });

  return promise;
}

function toLegacyOverview(payload) {
  const summary = payload.summary || payload.data || {};
  return {
    totalPlayers: summary.totalPlayers || 0,
    totalTeams: summary.totalTeams || 0,
    totalMatches: summary.totalMatches || 0,
    avgGoalsPerMatch: summary.avgGoalsPerMatch || 0,
    topLeagues: (payload.topTeams || []).map((team) => team.name).filter(Boolean),
    recentActivity: summary.recentActivity || 0,
    scoutingReports: summary.scoutingReports || 0,
    activeScouts: summary.activeScouts || 0,
    predictions: payload.predictions || {
      total: summary.transferPredictions || 0,
      accuracy: summary.modelAccuracy || 0,
    },
    modelAccuracy: summary.modelAccuracy || 0,
    transferPredictions: summary.transferPredictions || 0,
    responseTime: summary.responseTime || 0,
    topPlayers: payload.topPlayers || [],
    topTeams: payload.topTeams || [],
    recentMatches: payload.recentMatches || [],
  };
}

function toLegacyPlayerAnalytics(payload) {
  const player = payload.player || {};
  const summary = payload.summary || {};
  return {
    playerId: payload.player_id,
    name: player.name,
    performance: {
      appearances: summary.appearances || 0,
      goals: summary.goals || 0,
      assists: summary.assists || 0,
      passAccuracy: summary.passAccuracy || 0,
      rating: summary.rating || 0,
    },
    trends: {
      goalsPerMatch: [summary.goals || 0],
      ratingTrend: [summary.rating || 0],
    },
    player,
    statistics: payload.statistics || {},
  };
}

function toLegacyMatchAnalytics(payload) {
  return {
    matchId: payload.match_id,
    homeTeam: payload.match?.homeTeamID || payload.match?.home_team_id || null,
    awayTeam: payload.match?.awayTeamID || payload.match?.away_team_id || null,
    stats: payload.metrics || {},
    match: payload.match || {},
  };
}

async function fetchAnalytics(path, fallbackMessage, options = {}) {
  const payload = ensureSuccess(
    await requestJson(analyticsServiceUrl, path, options),
    fallbackMessage
  );

  if (payload && typeof payload === 'object' && payload.success === true && 'data' in payload) {
    return unwrapPayload(payload);
  }

  return payload;
}

// GET /api/analytics/player/:playerId
// GET /api/analytics — root summary
router.get('/', (req, res) => {
  res.json({
    status: 'active',
    endpoints: {
      overview:       '/api/analytics/overview',
      topPerformers:  '/api/analytics/top-performers',
      playerAnalytics: '/api/analytics/player/:playerId',
      matchAnalytics:  '/api/analytics/match/:matchId',
    },
    note: 'For advanced analytics use /api/v2/analytics',
  });
});

router.get('/player/:playerId', async (req, res) => {
  try {
    const payload = await fetchAnalytics(
      `/api/v2/analytics/dashboard/player/${req.params.playerId}`,
      'Failed to fetch player analytics'
    );

    res.json(toLegacyPlayerAnalytics(payload || {}));
  } catch (error) {
    console.error('Player analytics error:', error);
    sendGatewayError(res, error, 'Failed to fetch player analytics');
  }
});

// GET /api/analytics/match/:matchId
router.get('/match/:matchId', async (req, res) => {
  try {
    const payload = await fetchAnalytics(
      `/api/v2/analytics/advanced-metrics/${req.params.matchId}`,
      'Failed to fetch match analytics'
    );

    res.json(toLegacyMatchAnalytics(payload || {}));
  } catch (error) {
    console.error('Match analytics error:', error);
    sendGatewayError(res, error, 'Failed to fetch match analytics');
  }
});

// GET /api/analytics/:type - Generic analytics 
router.get('/:type', async (req, res) => {
  try {
    const type = req.params.type;

    const overviewPromise = () => getCachedAnalytics(
      'overview',
      () => fetchAnalytics('/api/v2/analytics/dashboard/overview', 'Failed to fetch analytics overview'),
      {
        allowStaleOnError: true,
        shouldCache: hasOverviewData,
      }
    );

    if (type === 'top-performers') {
      const [overview, rankings] = await Promise.all([
        overviewPromise(),
        getCachedAnalytics('rankings:players:goals:6', () => fetchAnalytics('/api/v2/analytics/rankings/players', 'Failed to fetch player rankings', {
          query: {
            metric: 'goals',
            limit: 6,
          },
        }).catch(() => [])),
      ]);

      const legacyOverview = toLegacyOverview(overview || {});
      legacyOverview.topPlayers = Array.isArray(rankings?.rankings) ? rankings.rankings : rankings || legacyOverview.topPlayers;
      return res.json(legacyOverview);
    }

    if (type === 'overview' || type === 'dashboard') {
      const overview = await overviewPromise();
      return res.json(toLegacyOverview(overview || {}));
    }

    const overview = await overviewPromise();
    res.json(toLegacyOverview(overview || {}));
  } catch (error) {
    console.error('Analytics error:', error);
    sendGatewayError(res, error, 'Failed to fetch analytics');
  }
});

module.exports = router;
