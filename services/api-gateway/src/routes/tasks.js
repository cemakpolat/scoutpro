const express = require('express');
const router = express.Router();

const TASK_WORKER_URL = process.env.TASK_WORKER_URL || 'http://task-worker-service:8013';

async function proxyToWorker(path, method = 'GET', body = null) {
  const fetch = (await import('node-fetch')).default;
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${TASK_WORKER_URL}${path}`, opts);
  if (!res.ok) {
    const text = await res.text();
    const err = new Error(text || res.statusText);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

// Submit a new background task
// POST /api/tasks
// Body: { task_type, payload }
router.post('/', async (req, res) => {
  try {
    const { task_type, payload } = req.body;
    if (!task_type || !payload) {
      return res.status(400).json({ error: 'task_type and payload are required' });
    }
    const task = await proxyToWorker('/tasks', 'POST', { task_type, payload });
    res.status(202).json(task);
  } catch (err) {
    res.status(err.status || 500).json({ error: err.message });
  }
});

// Get task status + inline result
// GET /api/tasks/:id
router.get('/:id', async (req, res) => {
  try {
    const task = await proxyToWorker(`/tasks/${req.params.id}`);
    res.json(task);
  } catch (err) {
    res.status(err.status || 500).json({ error: err.message });
  }
});

// Get task result (presigned URL if stored in MinIO)
// GET /api/tasks/:id/result
router.get('/:id/result', async (req, res) => {
  try {
    const result = await proxyToWorker(`/tasks/${req.params.id}/result`);
    res.json(result);
  } catch (err) {
    res.status(err.status || 500).json({ error: err.message });
  }
});

// List recent tasks
// GET /api/tasks?limit=50
router.get('/', async (req, res) => {
  try {
    const limit = Math.min(parseInt(req.query.limit || '50', 10), 200);
    const tasks = await proxyToWorker(`/tasks?limit=${limit}`);
    res.json(tasks);
  } catch (err) {
    res.status(err.status || 500).json({ error: err.message });
  }
});

module.exports = router;
