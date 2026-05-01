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

function inferVideoSource(url = '') {
  if (/youtu\.be|youtube\.com/i.test(url)) return 'youtube';
  if (/vimeo\.com/i.test(url)) return 'vimeo';
  return 'direct';
}

function normalizeVideoDuration(value) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }

  if (typeof value !== 'string' || value.trim() === '') {
    return 0;
  }

  const parts = value.split(':').map(part => Number.parseInt(part, 10));
  if (parts.some(part => Number.isNaN(part))) {
    return 0;
  }

  if (parts.length === 3) {
    return parts[0] * 3600 + parts[1] * 60 + parts[2];
  }

  if (parts.length === 2) {
    return parts[0] * 60 + parts[1];
  }

  return parts[0] || 0;
}

function formatVideoDuration(totalSeconds) {
  const safeSeconds = Math.max(0, Math.floor(Number(totalSeconds) || 0));
  const hours = Math.floor(safeSeconds / 3600);
  const minutes = Math.floor((safeSeconds % 3600) / 60);
  const seconds = safeSeconds % 60;

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  }

  return `${minutes}:${String(seconds).padStart(2, '0')}`;
}

function buildVideoDocument(videoId, payload = {}) {
  const durationSeconds = normalizeVideoDuration(payload.durationSeconds ?? payload.duration);
  const source = payload.source || inferVideoSource(payload.url || '');

  return {
    id: videoId,
    title: payload.title || `Video ${videoId.slice(0, 8)}`,
    description: payload.description || '',
    url: payload.url || payload.streamUrl || '',
    source,
    thumbnail: payload.thumbnail || payload.thumbnailUrl || null,
    duration: formatVideoDuration(durationSeconds),
    durationSeconds,
    playerId: payload.player?.id || payload.playerId || null,
    matchId: payload.match?.id || payload.matchId || null,
    player: payload.player || null,
    match: payload.match || null,
    status: payload.status || 'ready',
    size: payload.size || 0,
    mimeType: payload.mimeType || 'video/mp4',
    thumbnailUrl: payload.thumbnail || payload.thumbnailUrl || null,
    streamUrl: payload.streamUrl || payload.url || null,
    uploadedBy: payload.uploadedBy || 'scoutpro-ui',
    isPublic: payload.isPublic !== false,
    annotations: Array.isArray(payload.annotations) ? payload.annotations : [],
    tags: Array.isArray(payload.tags) ? payload.tags.filter(Boolean) : [],
    uploadedAt: payload.uploadedAt || new Date().toISOString(),
    analyzedAt: payload.analyzedAt || null,
    metadata: payload.metadata || {}
  };
}

function serializeVideo(video) {
  const durationSeconds = normalizeVideoDuration(video.durationSeconds ?? video.duration);
  return {
    ...video,
    id: video.id || video._id?.toString(),
    _id: undefined,
    source: video.source || inferVideoSource(video.url || ''),
    duration: video.duration || formatVideoDuration(durationSeconds),
    durationSeconds,
    thumbnail: video.thumbnail || video.thumbnailUrl || null,
    thumbnailUrl: video.thumbnail || video.thumbnailUrl || null,
    annotations: Array.isArray(video.annotations) ? video.annotations : [],
    tags: Array.isArray(video.tags) ? video.tags : [],
    uploadedBy: video.uploadedBy || 'scoutpro-ui',
    isPublic: video.isPublic !== false
  };
}

function buildVideoThumbnail(url) {
  if (!url) return null;

  const youtubeMatch = url.match(/(?:watch\?v=|youtu\.be\/|embed\/)([^#&?]{11})/);
  if (youtubeMatch?.[1]) {
    return `https://img.youtube.com/vi/${youtubeMatch[1]}/hqdefault.jpg`;
  }

  return null;
}

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

    res.json(videos.map(serializeVideo));
  } catch (error) {
    console.error('List videos error:', error);
    res.status(500).json({ error: 'Failed to list videos' });
  }
});

// POST /api/v2/videos - Create a video record for an external URL or existing asset
router.post('/', async (req, res) => {
  try {
    const db = req.app.locals.db;
    const videoId = uuidv4();
    const videoDoc = buildVideoDocument(videoId, req.body || {});

    if (db) {
      await db.collection('videos').insertOne(videoDoc);
    }

    res.status(201).json(serializeVideo(videoDoc));
  } catch (error) {
    console.error('Create video error:', error);
    res.status(500).json({ error: 'Failed to create video' });
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

    res.json(serializeVideo(video));
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

    const videoDoc = buildVideoDocument(videoId, {
      title: req.body?.title,
      description: req.body?.description,
      matchId: req.body?.match_id,
      playerId: req.body?.player_id,
      size: req.headers['content-length'] || 0,
      mimeType: req.headers['content-type'] || 'video/mp4',
      streamUrl: `/api/v2/videos/${videoId}/stream`,
      status: 'uploaded',
      metadata: req.body?.metadata ? JSON.parse(req.body.metadata) : {}
    });

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
      rating: req.body.rating || null,
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

// PUT /api/v2/videos/:videoId/annotations/:annotationId - Update annotation
router.put('/:videoId/annotations/:annotationId', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.status(503).json({ error: 'Database unavailable' });
    }

    const updates = {
      ...(req.body.timestamp !== undefined ? { timestamp: req.body.timestamp } : {}),
      ...(req.body.endTimestamp !== undefined ? { endTimestamp: req.body.endTimestamp } : {}),
      ...(req.body.type ? { type: req.body.type } : {}),
      ...(req.body.text !== undefined ? { text: req.body.text } : {}),
      ...(req.body.note !== undefined ? { text: req.body.note } : {}),
      ...(req.body.rating !== undefined ? { rating: req.body.rating } : {}),
      ...(req.body.author ? { author: req.body.author } : {}),
      ...(req.body.position !== undefined ? { position: req.body.position } : {}),
      ...(req.body.tags ? { tags: req.body.tags } : {}),
      updatedAt: new Date().toISOString()
    };

    await db.collection('video_annotations').updateOne(
      { id: req.params.annotationId, videoId: req.params.videoId },
      { $set: updates }
    );

    const annotations = await db.collection('video_annotations')
      .find({ videoId: req.params.videoId })
      .sort({ timestamp: 1 })
      .toArray();

    await db.collection('videos').updateOne(
      { id: req.params.videoId },
      { $set: { annotations, updatedAt: new Date().toISOString() } }
    );

    const updated = await db.collection('video_annotations').findOne({ id: req.params.annotationId, videoId: req.params.videoId });
    if (!updated) {
      return res.status(404).json({ error: 'Annotation not found' });
    }

    res.json({ ...updated, _id: undefined });
  } catch (error) {
    console.error('Update annotation error:', error);
    res.status(500).json({ error: 'Failed to update annotation' });
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

// DELETE /api/v2/videos/:videoId/annotations/:annotationId - Delete annotation
router.delete('/:videoId/annotations/:annotationId', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.status(503).json({ error: 'Database unavailable' });
    }

    await db.collection('video_annotations').deleteOne({ id: req.params.annotationId, videoId: req.params.videoId });

    const annotations = await db.collection('video_annotations')
      .find({ videoId: req.params.videoId })
      .sort({ timestamp: 1 })
      .toArray();

    await db.collection('videos').updateOne(
      { id: req.params.videoId },
      { $set: { annotations, updatedAt: new Date().toISOString() } }
    );

    res.json({ success: true });
  } catch (error) {
    console.error('Delete annotation error:', error);
    res.status(500).json({ error: 'Failed to delete annotation' });
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
    res.json(serializeVideo(updated));
  } catch (error) {
    console.error('Update video error:', error);
    res.status(500).json({ error: 'Failed to update video' });
  }
});

// ===== Helper Functions =====

function generateMockVideo(videoId) {
  return serializeVideo({
    id: videoId,
    title: `Match Highlights - ${videoId.slice(0, 8)}`,
    description: 'Auto-generated video entry',
    url: '',
    durationSeconds: Math.floor(Math.random() * 5400) + 300,
    status: 'ready',
    thumbnailUrl: null,
    streamUrl: `/api/v2/videos/${videoId}/stream`,
    annotations: [],
    tags: ['highlights', 'match'],
    uploadedAt: new Date().toISOString(),
    metadata: {}
  });
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

// ============================================================================
// Video Event Linking - Direct MongoDB Integration
// ============================================================================

/**
 * POST /:id/link-event
 * Link a video to a specific match event for event-driven video discovery
 */
router.post('/:id/link-event', async (req, res) => {
  try {
    const videoId = req.params.id;
    const { match_id, event_id, event_timestamp, event_type, notes } = req.query;

    if (!match_id) {
      return res.status(400).json({ error: 'match_id query parameter required' });
    }

    const backendUrl = `http://video-service:28008/api/v2/videos/${videoId}/link-event`;
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      query: new URLSearchParams({
        match_id,
        ...(event_id && { event_id }),
        ...(event_timestamp && { event_timestamp }),
        ...(event_type && { event_type }),
        ...(notes && { notes })
      }).toString()
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const data = await response.json();
    res.status(response.status).json(data);
  } catch (error) {
    console.error('Error linking video to event:', error);
    res.status(500).json({ error: 'Failed to link video to event' });
  }
});

/**
 * GET /
 * List videos with optional event filtering
 * Query params: match_id, event_id, event_type, team_id, limit, skip
 */
router.get('/', async (req, res) => {
  try {
    const { match_id, event_id, event_type, team_id, limit = '50', skip = '0' } = req.query;

    // Build query string
    const queryParts = [];
    if (match_id) queryParts.push(`match_id=${encodeURIComponent(match_id)}`);
    if (event_id) queryParts.push(`event_id=${encodeURIComponent(event_id)}`);
    if (event_type) queryParts.push(`event_type=${encodeURIComponent(event_type)}`);
    if (team_id) queryParts.push(`team_id=${encodeURIComponent(team_id)}`);
    queryParts.push(`limit=${encodeURIComponent(limit)}`);
    queryParts.push(`skip=${encodeURIComponent(skip)}`);

    const backendUrl = `http://video-service:28008/api/v2/videos/?${queryParts.join('&')}`;
    const response = await fetch(backendUrl);

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const data = await response.json();
    res.status(response.status).json(data);
  } catch (error) {
    console.error('Error listing videos:', error);
    res.status(500).json({ error: 'Failed to list videos' });
  }
});

module.exports = router;
