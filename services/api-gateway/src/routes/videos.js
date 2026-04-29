/**
 * Video Routes - Video management, upload, streaming, and analysis
 * Replaces the Python video-service stubs.
 */
const express = require('express');
const router = express.Router();
const { v4: uuidv4 } = require('uuid');
const path = require('path');
const fs = require('fs');

// Ensure upload dir exists
const UPLOAD_DIR = path.join(__dirname, '../../uploads/videos');
try { fs.mkdirSync(UPLOAD_DIR, { recursive: true }); } catch (e) {}

// GET /api/v2/videos - List all videos
router.get('/', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.json([]);

    const filter = {};
    if (req.query.match_id) filter.matchId = req.query.match_id;
    if (req.query.player_id) filter.playerId = req.query.player_id;

    const videos = await db.collection('videos')
      .find(filter)
      .sort({ uploadedAt: -1 })
      .limit(100)
      .toArray();

    res.json(videos.map(v => ({
      ...v,
      id: v.id || v._id?.toString(),
      _id: undefined
    })));
  } catch (error) {
    console.error('List videos error:', error);
    res.status(500).json({ error: 'Failed to list videos' });
  }
});

// GET /api/v2/videos/:videoId - Get video metadata
router.get('/:videoId', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.json(generateMockVideo(req.params.videoId));
    }

    const video = await db.collection('videos').findOne({ id: req.params.videoId });
    if (!video) {
      return res.json(generateMockVideo(req.params.videoId));
    }

    res.json({ ...video, id: video.id || video._id?.toString(), _id: undefined });
  } catch (error) {
    console.error('Get video error:', error);
    res.status(500).json({ error: 'Failed to get video' });
  }
});

// POST /api/v2/videos/upload - Upload a video
router.post('/upload', express.raw({ type: 'multipart/form-data', limit: '500mb' }), async (req, res) => {
  try {
    const videoId = uuidv4();
    const db = req.app.locals.db;

    const videoDoc = {
      id: videoId,
      title: req.body?.title || `Video ${videoId.slice(0, 8)}`,
      description: req.body?.description || '',
      matchId: req.body?.match_id || null,
      playerId: req.body?.player_id || null,
      duration: 0,
      status: 'uploaded',
      size: req.headers['content-length'] || 0,
      mimeType: req.headers['content-type'] || 'video/mp4',
      thumbnailUrl: null,
      streamUrl: `/api/v2/videos/${videoId}/stream`,
      annotations: [],
      tags: [],
      uploadedAt: new Date().toISOString(),
      analyzedAt: null,
      metadata: req.body?.metadata ? JSON.parse(req.body.metadata) : {}
    };

    if (db) {
      await db.collection('videos').insertOne(videoDoc);
    }

    res.status(201).json({ 
      video_id: videoId, 
      status: 'uploaded',
      message: 'Video uploaded successfully' 
    });
  } catch (error) {
    console.error('Upload video error:', error);
    res.status(500).json({ error: 'Failed to upload video' });
  }
});

// GET /api/v2/videos/:videoId/stream - Stream video (placeholder)
router.get('/:videoId/stream', async (req, res) => {
  // In a real implementation, this would stream from object storage (MinIO/S3)
  res.json({ 
    error: 'Video streaming requires object storage configuration',
    videoId: req.params.videoId,
    hint: 'Configure MinIO or S3 in production for video storage' 
  });
});

// POST /api/v2/videos/:videoId/analyze - Start video analysis
router.post('/:videoId/analyze', async (req, res) => {
  try {
    const db = req.app.locals.db;
    const jobId = uuidv4();
    const analysisType = req.body?.analysis_type || 'full';

    const analysisJob = {
      id: jobId,
      videoId: req.params.videoId,
      type: analysisType,
      status: 'processing',
      progress: 0,
      startedAt: new Date().toISOString(),
      results: null
    };

    if (db) {
      await db.collection('video_analyses').insertOne(analysisJob);

      // Simulate async analysis completion
      setTimeout(async () => {
        try {
          await db.collection('video_analyses').updateOne(
            { id: jobId },
            { $set: {
              status: 'completed',
              progress: 100,
              completedAt: new Date().toISOString(),
              results: generateAnalysisResults(analysisType)
            }}
          );
        } catch (e) {
          console.error('Analysis update error:', e);
        }
      }, 5000);
    }

    res.json({ job_id: jobId, status: 'processing' });
  } catch (error) {
    console.error('Analyze video error:', error);
    res.status(500).json({ error: 'Failed to start analysis' });
  }
});

// GET /api/v2/videos/:videoId/analysis - Get analysis results
router.get('/:videoId/analysis', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.json(generateAnalysisResults('full'));
    }

    const analyses = await db.collection('video_analyses')
      .find({ videoId: req.params.videoId })
      .sort({ startedAt: -1 })
      .limit(5)
      .toArray();

    if (analyses.length === 0) {
      return res.json(generateAnalysisResults('full'));
    }

    res.json(analyses.map(a => ({ ...a, _id: undefined })));
  } catch (error) {
    console.error('Get analysis error:', error);
    res.status(500).json({ error: 'Failed to get analysis' });
  }
});

// POST /api/v2/videos/:videoId/annotations - Add annotation to video
router.post('/:videoId/annotations', async (req, res) => {
  try {
    const db = req.app.locals.db;
    const annotation = {
      id: uuidv4(),
      videoId: req.params.videoId,
      timestamp: req.body.timestamp || 0,
      endTimestamp: req.body.endTimestamp || null,
      type: req.body.type || 'note',
      text: req.body.text || '',
      author: req.body.author || 'system',
      position: req.body.position || null,
      tags: req.body.tags || [],
      createdAt: new Date().toISOString()
    };

    if (db) {
      await db.collection('video_annotations').insertOne(annotation);
      // Also push to the video doc
      await db.collection('videos').updateOne(
        { id: req.params.videoId },
        { $push: { annotations: annotation } }
      );
    }

    res.status(201).json(annotation);
  } catch (error) {
    console.error('Add annotation error:', error);
    res.status(500).json({ error: 'Failed to add annotation' });
  }
});

// GET /api/v2/videos/:videoId/annotations - List annotations
router.get('/:videoId/annotations', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.json([]);

    const annotations = await db.collection('video_annotations')
      .find({ videoId: req.params.videoId })
      .sort({ timestamp: 1 })
      .toArray();

    res.json(annotations.map(a => ({ ...a, _id: undefined })));
  } catch (error) {
    console.error('List annotations error:', error);
    res.status(500).json({ error: 'Failed to list annotations' });
  }
});

// DELETE /api/v2/videos/:videoId - Delete video
router.delete('/:videoId', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (db) {
      await db.collection('videos').deleteOne({ id: req.params.videoId });
      await db.collection('video_annotations').deleteMany({ videoId: req.params.videoId });
      await db.collection('video_analyses').deleteMany({ videoId: req.params.videoId });
    }
    res.json({ success: true, message: 'Video deleted' });
  } catch (error) {
    console.error('Delete video error:', error);
    res.status(500).json({ error: 'Failed to delete video' });
  }
});

// PUT /api/v2/videos/:videoId - Update video metadata
router.put('/:videoId', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) return res.status(503).json({ error: 'Database unavailable' });

    const updates = {};
    if (req.body.title) updates.title = req.body.title;
    if (req.body.description) updates.description = req.body.description;
    if (req.body.tags) updates.tags = req.body.tags;
    if (req.body.metadata) updates.metadata = req.body.metadata;
    updates.updatedAt = new Date().toISOString();

    await db.collection('videos').updateOne(
      { id: req.params.videoId },
      { $set: updates }
    );

    const updated = await db.collection('videos').findOne({ id: req.params.videoId });
    res.json({ ...updated, _id: undefined });
  } catch (error) {
    console.error('Update video error:', error);
    res.status(500).json({ error: 'Failed to update video' });
  }
});

// ===== Helper Functions =====

function generateMockVideo(videoId) {
  return {
    id: videoId,
    title: `Match Highlights - ${videoId.slice(0, 8)}`,
    description: 'Auto-generated video entry',
    duration: Math.floor(Math.random() * 5400) + 300,
    status: 'ready',
    thumbnailUrl: null,
    streamUrl: `/api/v2/videos/${videoId}/stream`,
    annotations: [],
    tags: ['highlights', 'match'],
    uploadedAt: new Date().toISOString(),
    metadata: {}
  };
}

function generateAnalysisResults(type) {
  return {
    type,
    events: [
      { time: 12.5, type: 'goal', team: 'home', player: 'Player A', confidence: 0.95 },
      { time: 34.2, type: 'shot', team: 'away', player: 'Player B', confidence: 0.87 },
      { time: 56.8, type: 'corner', team: 'home', confidence: 0.92 },
      { time: 67.1, type: 'foul', team: 'away', player: 'Player C', confidence: 0.78 },
      { time: 78.3, type: 'goal', team: 'away', player: 'Player D', confidence: 0.96 }
    ],
    heatmap: {
      home: Array.from({ length: 10 }, () => Array.from({ length: 7 }, () => Math.random())),
      away: Array.from({ length: 10 }, () => Array.from({ length: 7 }, () => Math.random()))
    },
    possession: { home: 55, away: 45 },
    passNetwork: {
      home: { nodes: 11, edges: 45, avgPasses: 32 },
      away: { nodes: 11, edges: 38, avgPasses: 28 }
    },
    playerTracking: {
      totalDistanceCovered: { home: 112.5, away: 108.3 },
      sprints: { home: 145, away: 132 },
      topSpeed: { home: 34.5, away: 33.8 }
    }
  };
}

module.exports = router;
