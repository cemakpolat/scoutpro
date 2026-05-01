/**
 * Detailed Player Statistics Routes
 * Exposes computed event evaluation data (passes, shots, aerials, tackles, etc.)
 * 
 * Endpoints:
 * - GET /api/players/:id/detailed-stats  - Career-level aggregated statistics
 * - GET /api/players/:id/match-stats/:matchId  - Match-specific detailed stats
 * - GET /api/players/stats/leaders/passes  - Players ranked by pass accuracy
 * - GET /api/players/stats/leaders/aerials  - Players ranked by aerial success
 */

const express = require('express');
const router = express.Router();
const { MongoClient } = require('mongodb');

let mongoDb = null;

// Middleware to ensure MongoDB connection
function ensureDb(req, res, next) {
  if (!mongoDb) {
    const mongoUri = process.env.MONGO_URI || 'mongodb://root:scoutpro123@scoutpro-mongo:27017/scoutpro?authSource=admin';
    MongoClient.connect(mongoUri)
      .then(client => {
        mongoDb = client.db('scoutpro');
        next();
      })
      .catch(err => res.status(500).json({ error: 'Database connection failed', details: err.message }));
  } else {
    next();
  }
}

router.use(ensureDb);

/**
 * GET /api/players/:id/detailed-stats
 * 
 * Career-level aggregated statistics computed from all match events.
 * Shows total passes, accuracy, goals, shooting stats, aerial duels, tackles, etc.
 * 
 * Response:
 * {
 *   player_id: "112323",
 *   matches: 5,
 *   statistics: {
 *     passing: { total: 234, successful: 201, accuracy: 85.9 },
 *     shooting: { total: 12, onTarget: 8, goals: 2 },
 *     aerials: { duels: 45, won: 28, accuracy: 62.2 },
 *     defending: { tackles: 34, interceptions: 8 }
 *   },
 *   last_updated: "2026-04-30T15:43:40.000Z"
 * }
 */
router.get('/:id/detailed-stats', async (req, res) => {
  try {
    const playerId = parseInt(req.params.id);
    
    const stats = await mongoDb
      .collection('unified_player_career_stats')
      .findOne({ _id: playerId });
    
    if (!stats) {
      return res.status(404).json({
        error: 'Detailed statistics not found',
        player_id: playerId,
        message: 'This player may not have events evaluated yet. Run event aggregation pipeline.'
      });
    }
    
    // Extract event source info
    const eventSource = stats.event_source || {};
    
    // Transform to response format
    const response = {
      player_id: stats._id,
      event_source: {
        primary_source: eventSource.primary_source || 'unknown',
        all_sources: eventSource.all_sources || [],
        event_coverage: eventSource.event_coverage || 'No events',
        source_description: eventSource.primary_source === 'opta' 
          ? 'Powered by Opta Sports F24 (Official Events)'
          : eventSource.primary_source === 'statsbomb'
          ? 'Powered by StatsBomb (Tactical Events)'
          : 'Mixed Event Sources'
      },
      statistics: {
        passing: {
          total: stats.total_passes || 0,
          successful: stats.successful_passes || 0,
          accuracy: stats.pass_accuracy || 0
        },
        shooting: {
          total: stats.total_shots || 0,
          goals: stats.goals || 0,
          onTarget: (stats.total_shots || 0) - (stats.total_shots || 0 - (stats.goals || 0))
        },
        aerials: {
          duels: stats.aerial_duels_total || 0,
          won: stats.aerial_duels_won || 0,
          accuracy: stats.aerial_success_rate || 0
        },
        defending: {
          tackles: stats.tackles || 0,
          tackles_successful: stats.tackles || 0
        }
      },
      last_updated: stats.last_updated
    };
    
    res.json(response);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/players/:id/match-stats/:matchId
 * 
 * Detailed statistics for a specific player in a specific match.
 * Shows all event counts: passes by type, shot attempts, aerial duels, etc.
 * Useful for tactical analysis and match review.
 */
router.get('/:id/match-stats/:matchId', async (req, res) => {
  try {
    const playerId = parseInt(req.params.id);
    const matchId = parseInt(req.params.matchId);
    
    const stats = await mongoDb
      .collection('detailed_player_statistics')
      .findOne({ 
        player_id: playerId,
        match_id: matchId
      });
    
    if (!stats) {
      return res.status(404).json({
        error: 'Match statistics not found',
        player_id: playerId,
        match_id: matchId
      });
    }
    
    // Transform to response format
    const response = {
      player_id: stats.player_id,
      match_id: stats.match_id,
      team_id: stats.team_id,
      events: {
        passes: stats.passes || {},
        shots: stats.shots || {},
        aerials: stats.aerials || {},
        tackles: stats.tackles || {},
        duels: stats.duels || {},
        ball_control: stats.ball_control || {}
      },
      timestamp: stats.timestamp
    };
    
    res.json(response);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/players/stats/leaders/passes
 * 
 * Ranked list of players by pass accuracy or pass volume.
 * Query parameters:
 * - metric: 'accuracy' (default), 'total', 'successful'
 * - limit: number of results (default 20)
 * - minMatches: minimum matches played (default 1)
 */
router.get('/stats/leaders/passes', async (req, res) => {
  try {
    const metric = req.query.metric || 'accuracy';
    const limit = Math.min(parseInt(req.query.limit) || 20, 100);
    const minMatches = parseInt(req.query.minMatches) || 1;
    
    let sortField = 'pass_accuracy';
    if (metric === 'total') sortField = 'total_passes';
    if (metric === 'successful') sortField = 'successful_passes';
    
    const leaders = await mongoDb
      .collection('unified_player_career_stats')
      .find({})
      .sort({ [sortField]: -1 })
      .limit(limit)
      .toArray();
    
    const response = {
      metric: metric,
      minMatches: minMatches,
      results: leaders.map(p => ({
        player_id: p._id,
        event_source: p.event_source?.primary_source || 'unknown',
        event_coverage: p.event_source?.event_coverage || 'unknown',
        opta_events: p.opta_events || 0,
        statsbomb_events: p.statsbomb_events || 0,
        total_passes: p.total_passes || 0,
        successful_passes: p.successful_passes || 0,
        pass_accuracy: p.pass_accuracy || 0
      }))
    };
    
    res.json(response);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/players/stats/leaders/aerials
 * 
 * Ranked list of players by aerial duel success rate.
 * Query parameters:
 * - metric: 'success_rate' (default), 'duels_won', 'total_duels'
 * - limit: number of results (default 20)
 * - minDuels: minimum aerial duels (default 5)
 */
router.get('/stats/leaders/aerials', async (req, res) => {
  try {
    const metric = req.query.metric || 'success_rate';
    const limit = Math.min(parseInt(req.query.limit) || 20, 100);
    const minDuels = parseInt(req.query.minDuels) || 5;
    
    let sortField = 'aerial_success_rate';
    if (metric === 'duels_won') sortField = 'aerial_duels_won';
    if (metric === 'total_duels') sortField = 'aerial_duels_total';
    
    const leaders = await mongoDb
      .collection('unified_player_career_stats')
      .find({ aerial_duels_total: { $gte: minDuels } })
      .sort({ [sortField]: -1 })
      .limit(limit)
      .toArray();
    
    const response = {
      metric: metric,
      minDuels: minDuels,
      results: leaders.map(p => ({
        player_id: p._id,
        event_source: p.event_source?.primary_source || 'unknown',
        event_coverage: p.event_source?.event_coverage || 'unknown',
        opta_events: p.opta_events || 0,
        statsbomb_events: p.statsbomb_events || 0,
        aerial_duels_total: p.aerial_duels_total || 0,
        aerial_duels_won: p.aerial_duels_won || 0,
        aerial_success_rate: p.aerial_success_rate || 0
      }))
    };
    
    res.json(response);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/players/stats/leaders/shooting
 * 
 * Ranked list of players by goals or shot efficiency.
 */
router.get('/stats/leaders/shooting', async (req, res) => {
  try {
    const metric = req.query.metric || 'goals';
    const limit = Math.min(parseInt(req.query.limit) || 20, 100);
    const minShots = parseInt(req.query.minShots) || 1;
    
    let sortField = 'goals';
    if (metric === 'shots') sortField = 'total_shots';
    
    const leaders = await mongoDb
      .collection('unified_player_career_stats')
      .find({ total_shots: { $gte: minShots } })
      .sort({ [sortField]: -1 })
      .limit(limit)
      .toArray();
    
    const response = {
      metric: metric,
      minShots: minShots,
      results: leaders.map(p => ({
        player_id: p._id,
        event_source: p.event_source?.primary_source || 'unknown',
        event_coverage: p.event_source?.event_coverage || 'unknown',
        opta_events: p.opta_events || 0,
        statsbomb_events: p.statsbomb_events || 0,
        total_shots: p.total_shots || 0,
        goals: p.goals || 0,
        shot_efficiency: (p.total_shots || 0) > 0 ? Math.round((p.goals / p.total_shots) * 100) : 0
      }))
    };
    
    res.json(response);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/players/stats/re-aggregate
 * 
 * Trigger re-aggregation of player statistics from detailed match data.
 * Internal endpoint for admin/maintenance.
 */
router.post('/stats/re-aggregate', async (req, res) => {
  try {
    // Aggregate detailed_player_statistics into player_detailed_career_stats
    const result = await mongoDb.collection('detailed_player_statistics').aggregate([
      {
        $group: {
          _id: '$player_id',
          matches: { $sum: 1 },
          total_passes: {
            $sum: { $toInt: { $getField: { field: 'total passes', input: '$passes' } } }
          },
          successful_passes: {
            $sum: { $toInt: { $getField: { field: 'passes successful', input: '$passes' } } }
          },
          total_goals: {
            $sum: { $toInt: { $getField: { field: 'goals', input: '$shots' } } }
          },
          total_shots: {
            $sum: { $toInt: { $getField: { field: 'total shots', input: '$shots' } } }
          },
          total_aerial_duels: {
            $sum: { $toInt: { $getField: { field: 'total aerial duels', input: '$aerials' } } }
          },
          aerial_duels_won: {
            $sum: { $toInt: { $getField: { field: 'aerial duels won', input: '$aerials' } } }
          },
          total_tackles: {
            $sum: { $toInt: { $getField: { field: 'total tackles', input: '$tackles' } } }
          },
          last_updated: { $max: '$timestamp' }
        }
      },
      {
        $addFields: {
          pass_accuracy: {
            $cond: [
              { $gt: ['$total_passes', 0] },
              {
                $round: [
                  { $multiply: [{ $divide: ['$successful_passes', '$total_passes'] }, 100] },
                  2
                ]
              },
              0
            ]
          },
          aerial_duel_success: {
            $cond: [
              { $gt: ['$total_aerial_duels', 0] },
              {
                $round: [
                  { $multiply: [{ $divide: ['$aerial_duels_won', '$total_aerial_duels'] }, 100] },
                  2
                ]
              },
              0
            ]
          }
        }
      }
    ]).toArray();
    
    await mongoDb.collection('player_detailed_career_stats').deleteMany({});
    if (result.length > 0) {
      await mongoDb.collection('player_detailed_career_stats').insertMany(result);
    }
    
    res.json({
      message: 'Re-aggregation completed',
      players_aggregated: result.length
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
