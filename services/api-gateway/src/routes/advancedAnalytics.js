/**
 * Advanced Analytics Routes
 * Proxies the frontend analytics surface to analytics-service with built-in caching.
 */
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const router = express.Router();
const analyticsServiceUrl = (process.env.ANALYTICS_SERVICE_URL || 'http://analytics-service:8012').replace(/\/$/, '');
const analyticsCacheTtlMs = Number(process.env.ANALYTICS_CACHE_TTL_MS || 300000); // 5 minutes default

// In-memory cache for analytics responses with TTL
const analyticsCache = new Map();
const requestDeduplication = new Map();

function buildCacheKey(method, path, query, body) {
  const queryStr = query ? `?${new URLSearchParams(query).toString()}` : '';
  const bodyStr = body && Object.keys(body).length > 0 ? JSON.stringify(body) : '';
  return `${method}:${path}${queryStr}:${bodyStr}`;
}

function getCachedResponse(key) {
  const now = Date.now();
  const cached = analyticsCache.get(key);

  if (cached && cached.expiresAt > now) {
    console.log(`[CACHE HIT] ${key}`);
    return cached.data;
  }

  if (cached) {
    analyticsCache.delete(key);
  }

  return null;
}

function setCachedResponse(key, data, ttlMs = analyticsCacheTtlMs) {
  analyticsCache.set(key, {
    data,
    expiresAt: Date.now() + ttlMs,
  });
  console.log(`[CACHE SET] ${key} (TTL: ${ttlMs}ms)`);
}

function deduplicateRequest(key, promise) {
  const existing = requestDeduplication.get(key);
  if (existing) {
    console.log(`[REQUEST DEDUPLICATED] ${key}`);
    return existing;
  }

  requestDeduplication.set(key, promise);
  promise
    .then(() => requestDeduplication.delete(key))
    .catch(() => requestDeduplication.delete(key));

  return promise;
}

function writeProxyBody(proxyReq, req) {
  if (!req.body || Object.keys(req.body).length === 0) {
    return;
  }

  const bodyData = JSON.stringify(req.body);
  proxyReq.setHeader('Content-Type', 'application/json');
  proxyReq.setHeader('Content-Length', Buffer.byteLength(bodyData));
  proxyReq.write(bodyData);
}

// GET /api/v2/analytics — root summary
router.get('/', (req, res) => {
  res.json({
    status: 'active',
    service: 'analytics-service',
    endpoints: {
      overview: '/api/v2/analytics/dashboard/overview',
      teamDashboard: '/api/v2/analytics/dashboard/team/:team_id',
      playerDashboard: '/api/v2/analytics/dashboard/player/:player_id',
      leagueTrends: '/api/v2/analytics/trends/league',
      playerRankings: '/api/v2/analytics/rankings/players',
      teamRankings: '/api/v2/analytics/rankings/teams',
      advancedMetrics: '/api/v2/analytics/advanced-metrics/:match_id',
      playerSequences: '/api/v2/analytics/insights/player/:player_id/sequences',
      playerComparison: '/api/v2/analytics/comparison/players',
    },
  });
});

// POST /insights/players/sequences — cache by sorted player_ids (25s computation)
router.post('/insights/players/sequences', async (req, res, next) => {
  const sortedIds = [...(req.body?.player_ids || [])].sort();
  if (!sortedIds.length) return next();

  const cacheKey = buildCacheKey('POST', '/insights/players/sequences', null, { player_ids: sortedIds });
  const cached = getCachedResponse(cacheKey);
  if (cached) return res.json(cached);

  const inFlight = requestDeduplication.get(cacheKey);
  if (inFlight) {
    inFlight.then(() => {
      const retried = getCachedResponse(cacheKey);
      if (retried) return res.json(retried);
      next();
    }).catch(() => next());
    return;
  }

  const promise = new Promise((resolve, reject) => {
    const originalJson = res.json.bind(res);
    res.json = function(data) {
      if (data && !data.error) setCachedResponse(cacheKey, data, analyticsCacheTtlMs);
      resolve(data);
      return originalJson(data);
    };
    const originalSend0 = res.send.bind(res);
    res.send = function(data) { reject(new Error('non-json')); return originalSend0(data); };
    next();
  });
  deduplicateRequest(cacheKey, promise);
});

// Cache-aware proxy middleware for expensive endpoints
router.get('/insights/player/:player_id/sequences', async (req, res, next) => {
  const cacheKey = buildCacheKey('GET', `/insights/player/${req.params.player_id}/sequences`, req.query, null);
  
  // Check cache
  const cached = getCachedResponse(cacheKey);
  if (cached) {
    return res.json(cached);
  }

  // Check for in-flight request
  const inFlight = requestDeduplication.get(cacheKey);
  if (inFlight) {
    inFlight
      .then(() => {
        const retried = getCachedResponse(cacheKey);
        if (retried) {
          return res.json(retried);
        }
        next();
      })
      .catch(() => next());
    return;
  }

  // Proxy the request with caching
  const promise = new Promise((resolve, reject) => {
    const originalJson = res.json.bind(res);
    res.json = function(data) {
      // Cache successful responses
      if (data && !data.error) {
        setCachedResponse(cacheKey, data, analyticsCacheTtlMs);
      }
      resolve(data);
      return originalJson(data);
    };

    const originalSend = res.send.bind(res);
    res.send = function(data) {
      reject(new Error('Response sent as string'));
      return originalSend(data);
    };

    next();
  });

  deduplicateRequest(cacheKey, promise);
});

// Cache-aware proxy for player comparison
router.post('/comparison/players', async (req, res, next) => {
  const cacheKey = buildCacheKey('POST', '/comparison/players', null, req.body);
  
  // Check cache
  const cached = getCachedResponse(cacheKey);
  if (cached) {
    return res.json(cached);
  }

  // Check for in-flight request
  const inFlight = requestDeduplication.get(cacheKey);
  if (inFlight) {
    inFlight
      .then(() => {
        const retried = getCachedResponse(cacheKey);
        if (retried) {
          return res.json(retried);
        }
        next();
      })
      .catch(() => next());
    return;
  }

  // Proxy the request with caching
  const promise = new Promise((resolve, reject) => {
    const originalJson = res.json.bind(res);
    res.json = function(data) {
      // Cache successful responses
      if (data && !data.error) {
        setCachedResponse(cacheKey, data, analyticsCacheTtlMs);
      }
      resolve(data);
      return originalJson(data);
    };

    const originalSend = res.send.bind(res);
    res.send = function(data) {
      reject(new Error('Response sent as string'));
      return originalSend(data);
    };

    next();
  });

  deduplicateRequest(cacheKey, promise);
});

// Cache-aware proxy for tactical match metrics — 1hr TTL (match data is immutable)
const MATCH_CACHE_TTL_MS = Number(process.env.MATCH_VIZ_CACHE_TTL_MS || 3600000);

router.get('/tactical/:matchId', async (req, res, next) => {
  const cacheKey = buildCacheKey('GET', `/tactical/${req.params.matchId}`, req.query, null);
  const cached = getCachedResponse(cacheKey);
  if (cached) return res.json(cached);

  const promise = new Promise((resolve, reject) => {
    const originalJson = res.json.bind(res);
    res.json = function(data) {
      if (data && !data.error) setCachedResponse(cacheKey, data, MATCH_CACHE_TTL_MS);
      resolve(data);
      return originalJson(data);
    };
    const originalSend1 = res.send.bind(res);
    res.send = function(data) { reject(new Error('non-json')); return originalSend1(data); };
    next();
  });
  deduplicateRequest(cacheKey, promise);
});

// Cache-aware proxy for match sequence insights — 1hr TTL
router.get('/sequences/:matchId', async (req, res, next) => {
  const cacheKey = buildCacheKey('GET', `/sequences/${req.params.matchId}`, req.query, null);
  const cached = getCachedResponse(cacheKey);
  if (cached) return res.json(cached);

  const promise = new Promise((resolve, reject) => {
    const originalJson = res.json.bind(res);
    res.json = function(data) {
      if (data && !data.error) setCachedResponse(cacheKey, data, MATCH_CACHE_TTL_MS);
      resolve(data);
      return originalJson(data);
    };
    const originalSend2 = res.send.bind(res);
    res.send = function(data) { reject(new Error('non-json')); return originalSend2(data); };
    next();
  });
  deduplicateRequest(cacheKey, promise);
});

// POST /multi-match — cache by sorted match_ids (same set of matches = same result)
router.post('/multi-match', async (req, res, next) => {
  const sortedIds = [...(req.body?.match_ids || [])].sort();
  const cacheKey = buildCacheKey('POST', '/multi-match', null, { match_ids: sortedIds });
  const cached = getCachedResponse(cacheKey);
  if (cached) return res.json(cached);

  const promise = new Promise((resolve, reject) => {
    const originalJson = res.json.bind(res);
    res.json = function(data) {
      if (data && !data.error) setCachedResponse(cacheKey, data, analyticsCacheTtlMs);
      resolve(data);
      return originalJson(data);
    };
    const originalSend3 = res.send.bind(res);
    res.send = function(data) { reject(new Error('non-json')); return originalSend3(data); };
    next();
  });
  deduplicateRequest(cacheKey, promise);
});

// Default proxy for all other analytics endpoints
// http-proxy-middleware v2 inside an Express sub-router forwards req.url (the full path)
// to the target, which already includes the /api/v2/analytics prefix because of how
// Express mounts the router.  No pathRewrite is needed.
router.use(
  '/',
  createProxyMiddleware({
    target: analyticsServiceUrl,
    changeOrigin: true,
    proxyTimeout: 30000,
    timeout: 30000,
    onProxyReq: writeProxyBody,
    onError: (error, req, res) => {
      res.status(502).json({
        error: 'Analytics service unavailable',
        message: error.message,
      });
    },
  })
);

module.exports = router;