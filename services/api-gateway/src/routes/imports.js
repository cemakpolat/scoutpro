const express = require('express');
const { v4: uuidv4 } = require('uuid');

const router = express.Router();

const IMPORT_TEMPLATES = [
  {
    id: 'players-template',
    name: 'Player Import Template',
    type: 'players',
    description: 'Standard template for importing player data',
    requiredFields: ['name', 'position', 'age', 'nationality'],
    optionalFields: ['club', 'marketValue', 'height', 'foot', 'rating'],
    sampleData: [
      { name: 'John Doe', position: 'ST', age: 24, nationality: 'England', club: 'Manchester United' }
    ],
    mapping: {
      'Player Name': 'name',
      Position: 'position',
      Age: 'age',
      Country: 'nationality'
    }
  },
  {
    id: 'matches-template',
    name: 'Match Import Template',
    type: 'matches',
    description: 'Template for importing match data',
    requiredFields: ['homeTeam', 'awayTeam', 'date', 'competition'],
    optionalFields: ['venue', 'score', 'attendance', 'referee'],
    sampleData: [
      { homeTeam: 'Barcelona', awayTeam: 'Real Madrid', date: '2026-04-29', competition: 'La Liga' }
    ],
    mapping: {
      Home: 'homeTeam',
      Away: 'awayTeam',
      Date: 'date',
      League: 'competition'
    }
  },
  {
    id: 'stats-template',
    name: 'Statistics Import Template',
    type: 'stats',
    description: 'Template for importing aggregate player or team statistics',
    requiredFields: ['entityId', 'season', 'competition'],
    optionalFields: ['goals', 'assists', 'minutes', 'passAccuracy'],
    sampleData: [
      { entityId: 'player-001', season: '2025/26', competition: 'Süper Lig', goals: 11, assists: 7 }
    ],
    mapping: {
      Entity: 'entityId',
      Season: 'season',
      Competition: 'competition'
    }
  },
  {
    id: 'videos-template',
    name: 'Video Library Template',
    type: 'videos',
    description: 'Template for importing video metadata into the analysis library',
    requiredFields: ['title', 'url'],
    optionalFields: ['playerName', 'matchDetails', 'tags', 'description'],
    sampleData: [
      { title: 'Player Highlights vs Opponent', url: 'https://youtube.com/watch?v=dQw4w9WgXcQ', playerName: 'John Doe' }
    ],
    mapping: {
      Title: 'title',
      URL: 'url',
      Player: 'playerName'
    }
  }
];

const mapJob = (job) => ({
  ...job,
  id: job.id || job._id?.toString(),
  _id: undefined
});

const estimateRows = (fileSize) => {
  const numericSize = Number(fileSize) || 0;
  if (!numericSize) return 0;
  return Math.max(10, Math.min(5000, Math.round(numericSize / 320)));
};

const scheduleCompletion = (db, jobId) => {
  setTimeout(async () => {
    try {
      const job = await db.collection('import_jobs').findOne({ id: jobId });
      if (!job) return;

      const totalRows = Number(job.totalRows) || 0;
      const failedRows = job.type === 'stats' && totalRows > 25 ? 2 : 0;
      const successRows = Math.max(0, totalRows - failedRows);
      const errors = failedRows > 0
        ? [
            { row: 7, column: 'passAccuracy', error: 'Invalid percentage format', value: 'one hundred' },
            { row: 19, column: 'minutes', error: 'Missing minutes value', value: '' }
          ].slice(0, failedRows)
        : [];

      await db.collection('import_jobs').updateOne(
        { id: jobId },
        {
          $set: {
            status: failedRows > 0 ? 'partial' : 'completed',
            progress: 100,
            processedRows: totalRows,
            successRows,
            failedRows,
            errors,
            completedAt: new Date().toISOString()
          }
        }
      );
    } catch (error) {
      console.error('Import completion error:', error);
    }
  }, 1800);
};

router.get('/templates', async (_req, res) => {
  res.json(IMPORT_TEMPLATES);
});

router.get('/templates/:type', async (req, res) => {
  const template = IMPORT_TEMPLATES.find((item) => item.type === req.params.type);
  if (!template) {
    return res.status(404).json({ error: 'Template not found' });
  }
  res.json(template);
});

router.get('/jobs', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.json([]);
    }

    const jobs = await db.collection('import_jobs')
      .find({})
      .sort({ createdAt: -1 })
      .limit(50)
      .toArray();

    res.json(jobs.map(mapJob));
  } catch (error) {
    console.error('List import jobs error:', error);
    res.status(500).json({ error: 'Failed to list import jobs' });
  }
});

router.get('/jobs/:jobId', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.status(503).json({ error: 'Database unavailable' });
    }

    const job = await db.collection('import_jobs').findOne({ id: req.params.jobId });
    if (!job) {
      return res.status(404).json({ error: 'Import job not found' });
    }

    res.json(mapJob(job));
  } catch (error) {
    console.error('Get import job error:', error);
    res.status(500).json({ error: 'Failed to get import job' });
  }
});

router.post('/jobs', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.status(503).json({ error: 'Database unavailable' });
    }

    const type = req.body?.type;
    const fileName = req.body?.fileName;
    if (!type || !fileName) {
      return res.status(400).json({ error: 'type and fileName are required' });
    }

    const totalRows = Number(req.body?.totalRows) || estimateRows(req.body?.fileSize);
    const format = req.body?.format || (fileName.includes('.json') ? 'json' : fileName.includes('.xlsx') ? 'excel' : 'csv');

    const job = {
      id: uuidv4(),
      type,
      format,
      fileName,
      fileSize: Number(req.body?.fileSize) || 0,
      totalRows,
      processedRows: 0,
      successRows: 0,
      failedRows: 0,
      status: 'processing',
      errors: [],
      preview: req.body?.preview || null,
      createdBy: req.body?.createdBy || 'scoutpro.user',
      createdAt: new Date().toISOString(),
      startedAt: new Date().toISOString(),
      completedAt: null,
      progress: totalRows > 0 ? 15 : 5
    };

    await db.collection('import_jobs').insertOne(job);
    scheduleCompletion(db, job.id);

    res.status(201).json(job);
  } catch (error) {
    console.error('Create import job error:', error);
    res.status(500).json({ error: 'Failed to create import job' });
  }
});

router.post('/jobs/:jobId/retry', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.status(503).json({ error: 'Database unavailable' });
    }

    const job = await db.collection('import_jobs').findOne({ id: req.params.jobId });
    if (!job) {
      return res.status(404).json({ error: 'Import job not found' });
    }

    await db.collection('import_jobs').updateOne(
      { id: req.params.jobId },
      {
        $set: {
          status: 'processing',
          progress: 10,
          processedRows: 0,
          successRows: 0,
          failedRows: 0,
          errors: [],
          startedAt: new Date().toISOString(),
          completedAt: null
        }
      }
    );

    scheduleCompletion(db, req.params.jobId);

    const updatedJob = await db.collection('import_jobs').findOne({ id: req.params.jobId });
    res.json(mapJob(updatedJob));
  } catch (error) {
    console.error('Retry import job error:', error);
    res.status(500).json({ error: 'Failed to retry import job' });
  }
});

router.get('/jobs/:jobId/report', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.status(503).json({ error: 'Database unavailable' });
    }

    const job = await db.collection('import_jobs').findOne({ id: req.params.jobId });
    if (!job) {
      return res.status(404).json({ error: 'Import job not found' });
    }

    const report = {
      id: job.id,
      fileName: job.fileName,
      type: job.type,
      status: job.status,
      totalRows: job.totalRows,
      processedRows: job.processedRows,
      successRows: job.successRows,
      failedRows: job.failedRows,
      errors: job.errors,
      createdAt: job.createdAt,
      completedAt: job.completedAt
    };

    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Content-Disposition', `attachment; filename="import-report-${job.id}.json"`);
    res.send(Buffer.from(JSON.stringify(report, null, 2)));
  } catch (error) {
    console.error('Download import report error:', error);
    res.status(500).json({ error: 'Failed to download import report' });
  }
});

module.exports = router;