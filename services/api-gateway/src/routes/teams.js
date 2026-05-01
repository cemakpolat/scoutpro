/**
 * Teams Routes - Proxies to team-service.
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

const teamServiceUrl = (process.env.TEAM_SERVICE_URL || 'http://team-service:8000').replace(/\/$/, '');

router.get('/', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(teamServiceUrl, '/api/v2/teams', {
        query: {
          country: req.query.country,
          league: req.query.league,
          limit: req.query.limit || 50,
        },
      }),
      'Failed to fetch teams'
    );

    res.json(normalizeList(unwrapPayload(payload)));
  } catch (error) {
    console.error('Teams list error:', error);
    sendGatewayError(res, error, 'Failed to fetch teams');
  }
});

router.get('/search', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(teamServiceUrl, '/api/v2/teams/search', {
        query: {
          q: req.query.q,
          limit: req.query.limit || 20,
        },
      }),
      'Search failed'
    );

    res.json(normalizeList(unwrapPayload(payload)));
  } catch (error) {
    console.error('Teams search error:', error);
    sendGatewayError(res, error, 'Search failed');
  }
});

router.get('/:id/squad', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(teamServiceUrl, `/api/v2/teams/${req.params.id}/squad`),
      'Failed to fetch team squad'
    );

    res.json(normalizeList(unwrapPayload(payload)));
  } catch (error) {
    console.error('Team squad error:', error);
    sendGatewayError(res, error, 'Failed to fetch team squad');
  }
});

router.get('/:id', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(teamServiceUrl, `/api/v2/teams/${req.params.id}`),
      'Failed to fetch team'
    );

    res.json(normalizeEntity(unwrapPayload(payload)));
  } catch (error) {
    console.error('Team get error:', error);
    sendGatewayError(res, error, 'Failed to fetch team');
  }
});

router.post('/', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(teamServiceUrl, '/api/v2/teams', {
        method: 'POST',
        body: req.body,
      }),
      'Failed to create team'
    );

    res.status(201).json(unwrapPayload(payload));
  } catch (error) {
    console.error('Team create error:', error);
    sendGatewayError(res, error, 'Failed to create team');
  }
});

router.put('/:id', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(teamServiceUrl, `/api/v2/teams/${req.params.id}`, {
        method: 'PUT',
        body: req.body,
      }),
      'Failed to update team'
    );

    res.json(unwrapPayload(payload));
  } catch (error) {
    console.error('Team update error:', error);
    sendGatewayError(res, error, 'Failed to update team');
  }
});

router.get('/:id/events', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(teamServiceUrl, `/api/v2/teams/${req.params.id}/events`, {
        query: {
          event_type: req.query.event_type,
          limit: req.query.limit || 100,
        },
      }),
      'Failed to fetch team events'
    );

    res.json(unwrapPayload(payload) || []);
  } catch (error) {
    console.error('Team events error:', error);
    sendGatewayError(res, error, 'Failed to fetch team events');
  }
});

module.exports = router;
