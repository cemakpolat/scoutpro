const express = require('express');
const router = express.Router();
const { requestJson, ensureSuccess, unwrapPayload, sendGatewayError } = require('../utils/serviceClient');

const batchDataManagerUrl = process.env.BATCH_DATA_MANAGER_URL || 'http://batch-data-manager:8200';

router.post('/', async (req, res) => {
  const { provider, resource_type, start_date, end_date, competition_id, season_id, idempotency_token } = req.body;

  try {
    if (!idempotency_token) {
      return res.status(400).json({ error: 'idempotency_token is required' });
    }

    const payload = ensureSuccess(
      await requestJson(batchDataManagerUrl, '/api/v2/batch-jobs', {
        method: 'POST',
        body: { provider, resource_type, start_date, end_date, competition_id, season_id, idempotency_token },
      }),
      'Failed to create batch job'
    );

    res.json(unwrapPayload(payload) || {});
  } catch (error) {
    sendGatewayError(res, error, 'Failed to create batch job');
  }
});

router.get('/', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(batchDataManagerUrl, '/api/v2/batch-jobs', {}),
      'Failed to fetch batch jobs'
    );

    res.json(unwrapPayload(payload) || {});
  } catch (error) {
    sendGatewayError(res, error, 'Failed to fetch batch jobs');
  }
});

router.get('/:job_id', async (req, res) => {
  const { job_id } = req.params;
  try {
    const payload = ensureSuccess(
      await requestJson(batchDataManagerUrl, `/api/v2/batch-jobs/${job_id}`, {}),
      'Failed to fetch batch job'
    );
    res.json(unwrapPayload(payload) || {});
  } catch (error) {
    sendGatewayError(res, error, 'Failed to fetch batch job');
  }
});

router.post('/:job_id/cancel', async (req, res) => {
  const { job_id } = req.params;
  try {
    const payload = ensureSuccess(
      await requestJson(batchDataManagerUrl, `/api/v2/batch-jobs/${job_id}/cancel`, { method: 'POST' }),
      'Failed to cancel batch job'
    );
    res.json(unwrapPayload(payload) || {});
  } catch (error) {
    sendGatewayError(res, error, 'Failed to cancel batch job');
  }
});

router.post('/:job_id/retry', async (req, res) => {
  const { job_id } = req.params;
  try {
    const payload = ensureSuccess(
      await requestJson(batchDataManagerUrl, `/api/v2/batch-jobs/${job_id}/retry`, { method: 'POST' }),
      'Failed to retry batch job'
    );
    res.json(unwrapPayload(payload) || {});
  } catch (error) {
    sendGatewayError(res, error, 'Failed to retry batch job');
  }
});

router.get('/admin/providers', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(batchDataManagerUrl, '/api/v2/admin/providers', {}),
      'Failed to fetch providers'
    );
    res.json(unwrapPayload(payload) || {});
  } catch (error) {
    sendGatewayError(res, error, 'Failed to fetch providers');
  }
});

router.get('/admin/providers/:provider/credentials', async (req, res) => {
  const { provider } = req.params;
  try {
    const payload = ensureSuccess(
      await requestJson(batchDataManagerUrl, `/api/v2/admin/providers/${provider}/credentials`, {}),
      'Failed to fetch provider credentials'
    );
    res.json(unwrapPayload(payload) || {});
  } catch (error) {
    sendGatewayError(res, error, 'Failed to fetch provider credentials');
  }
});

router.put('/admin/providers/:provider/credentials', async (req, res) => {
  const { provider } = req.params;
  const { api_key, username, password, environment, is_active } = req.body;
  try {
    const payload = ensureSuccess(
      await requestJson(batchDataManagerUrl, `/api/v2/admin/providers/${provider}/credentials`, {
        method: 'PUT',
        body: { provider, api_key, username, password, environment, is_active },
      }),
      'Failed to update provider credentials'
    );
    res.json(unwrapPayload(payload) || {});
  } catch (error) {
    sendGatewayError(res, error, 'Failed to update provider credentials');
  }
});

module.exports = router;
