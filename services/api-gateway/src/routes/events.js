const express = require('express');
const router = express.Router();

const {
  ensureSuccess,
  requestJson,
  sendGatewayError,
  unwrapPayload,
} = require('../utils/serviceClient');

const statisticsServiceUrl = (process.env.STATISTICS_SERVICE_URL || 'http://statistics-service:8000').replace(/\/$/, '');

router.get('/', (req, res) => {
  res.json({
    status: 'active',
    endpoints: {
      playerHeatmap: '/api/v2/events/heatmap/player/:playerId',
      playerCompositeIndex: '/api/v2/events/composite-index/player/:playerId',
      playerExpectedMetrics: '/api/v2/events/expected-metrics/player/:playerId',
      playerEnhancedPassStats: '/api/v2/events/passes/enhanced/player/:playerId',
      playerSimilarity: '/api/v2/events/similarity/player/:playerId',
    },
  });
});

router.use(async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(statisticsServiceUrl, `/api/v2/events${req.path}`, {
        method: req.method,
        query: req.query,
        body: ['GET', 'HEAD'].includes(req.method) ? undefined : req.body,
      }),
      'Failed to fetch event analytics'
    );

    res.json(unwrapPayload(payload));
  } catch (error) {
    console.error('Event analytics error:', error);
    sendGatewayError(res, error, 'Failed to fetch event analytics');
  }
});

module.exports = router;