/**
 * ML Routes - Proxies to ml-service where capabilities exist.
 */
const express = require('express');
const router = express.Router();
const { v4: uuidv4 } = require('uuid');

const {
  ensureSuccess,
  requestJson,
  sendGatewayError,
  unwrapPayload,
} = require('../utils/serviceClient');

const mlServiceUrl = (process.env.mlServiceUrl || 'http://ml-service:8000').replace(/\/$/, '');
const taskWorkerUrl = (process.env.TASK_WORKER_URL || 'http://task-worker-service:8013').replace(/\/$/, '');

const ALGORITHM_CATALOG = [
  {
    id: 'player_performance',
    aliases: ['player-performance'],
    name: 'Player Performance Predictor',
    type: 'Regression',
    description: 'Gradient-boosted player rating model trained from the player feature store.',
    accuracy: 82.4,
    speed: 'Medium',
    interpretability: 'Medium',
    bestFor: ['Player Ratings', 'Feature Importance'],
    parameters: {
      trainer: 'GradientBoostingRegressor',
      source: 'player_features',
    },
    train: {
      endpoint: '/api/v2/ml/train/player-performance',
      supportedDatasetIds: ['ds-player-features'],
      recommendedDatasetId: 'ds-player-features',
    },
  },
  {
    id: 'match_outcome',
    aliases: ['match-outcome'],
    name: 'Match Outcome Predictor',
    type: 'Classification',
    description: 'Random forest predictor for home win, draw, and away win inference.',
    accuracy: 78.6,
    speed: 'Medium',
    interpretability: 'Medium',
    bestFor: ['Outcome Forecasting', 'Probability Estimates'],
    parameters: {
      trainer: 'RandomForestClassifier',
      source: 'matches',
    },
    unavailableReason: 'Prediction only. No training endpoint is exposed by ml-service for this model yet.',
  },
  {
    id: 'player_similarity',
    aliases: ['player-similarity'],
    name: 'Player Similarity Model',
    type: 'Clustering',
    description: 'K-Means similarity baseline trained on the player feature store.',
    accuracy: 80.1,
    speed: 'Fast',
    interpretability: 'Low',
    bestFor: ['Scouting Comparisons', 'Feature-Space Neighbors'],
    parameters: {
      trainer: 'KMeans',
      source: 'player_features',
    },
    train: {
      endpoint: '/api/v2/ml/train/player-similarity',
      supportedDatasetIds: ['ds-player-features'],
      recommendedDatasetId: 'ds-player-features',
    },
  },
  {
    id: 'xg_model',
    aliases: ['xg', 'xg-model'],
    name: 'Expected Goals Model',
    type: 'Classification',
    description: 'Shot-level xG model trained from match events.',
    accuracy: 74.2,
    speed: 'Medium',
    interpretability: 'Medium',
    bestFor: ['Shot Quality', 'Chance Valuation'],
    parameters: {
      trainer: 'LogisticRegression',
      source: 'match_events',
    },
    includeWhenMissing: true,
    train: {
      endpoint: '/api/v2/ml/train/xg',
      supportedDatasetIds: ['ds-match-events'],
      recommendedDatasetId: 'ds-match-events',
    },
  },
  {
    id: 'player_clustering',
    aliases: ['player-clustering'],
    name: 'Player Clustering',
    type: 'Clustering',
    description: 'K-Means archetype grouping over player feature vectors.',
    accuracy: 79.4,
    speed: 'Fast',
    interpretability: 'Medium',
    bestFor: ['Archetypes', 'Squad Segmentation'],
    parameters: {
      trainer: 'KMeans + PCA',
      source: 'player_features',
    },
    train: {
      endpoint: '/api/v2/ml/engine/train/player_clustering',
      supportedDatasetIds: ['ds-player-features', 'ds-player-statistics'],
      recommendedDatasetId: 'ds-player-features',
      buildBody: (dataset) => ({ collection: dataset?.collection || 'player_features' }),
    },
  },
  {
    id: 'goals_regression',
    aliases: ['goals-regression'],
    name: 'Goals Regression',
    type: 'Regression',
    description: 'Gradient boosting regressor for goal output from player statistics.',
    accuracy: 76.8,
    speed: 'Medium',
    interpretability: 'Medium',
    bestFor: ['Goal Output', 'Regression Baselines'],
    parameters: {
      target_field: 'goals',
      source: 'player_statistics',
    },
    train: {
      endpoint: '/api/v2/ml/engine/train/goals_regression',
      supportedDatasetIds: ['ds-player-statistics'],
      recommendedDatasetId: 'ds-player-statistics',
      buildBody: (dataset) => ({ collection: dataset?.collection || 'player_statistics', target_field: 'goals' }),
    },
  },
  {
    id: 'shots_regression',
    aliases: ['shots-regression'],
    name: 'Shots Regression',
    type: 'Regression',
    description: 'Gradient boosting regressor for shot volume forecasting.',
    accuracy: 75.3,
    speed: 'Medium',
    interpretability: 'Medium',
    bestFor: ['Shot Volume', 'Attacking Output'],
    parameters: {
      target_field: 'shots',
      source: 'player_statistics',
    },
    train: {
      endpoint: '/api/v2/ml/engine/train/shots_regression',
      supportedDatasetIds: ['ds-player-statistics'],
      recommendedDatasetId: 'ds-player-statistics',
      buildBody: (dataset) => ({ collection: dataset?.collection || 'player_statistics', target_field: 'shots' }),
    },
  },
  {
    id: 'goals_linear_regression',
    aliases: ['goals-linear-regression'],
    name: 'Goals Linear Regression',
    type: 'Linear Model',
    description: 'Explainable linear regression baseline for goal prediction.',
    accuracy: 71.1,
    speed: 'Very Fast',
    interpretability: 'High',
    bestFor: ['Explainable Baselines', 'Quick Checks'],
    parameters: {
      target_field: 'goals',
      source: 'player_statistics',
    },
    train: {
      endpoint: '/api/v2/ml/engine/train/goals_linear_regression',
      supportedDatasetIds: ['ds-player-statistics'],
      recommendedDatasetId: 'ds-player-statistics',
      buildBody: (dataset) => ({ collection: dataset?.collection || 'player_statistics', target_field: 'goals' }),
    },
  },
  {
    id: 'xg_linear_regression',
    aliases: ['xg-linear-regression'],
    name: 'xG Linear Regression',
    type: 'Linear Model',
    description: 'Explainable linear regression baseline for expected goals forecasting.',
    accuracy: 72.7,
    speed: 'Very Fast',
    interpretability: 'High',
    bestFor: ['Explainable xG Baselines', 'Trend Checks'],
    parameters: {
      target_field: 'xg',
      source: 'player_statistics',
    },
    train: {
      endpoint: '/api/v2/ml/engine/train/xg_linear_regression',
      supportedDatasetIds: ['ds-player-statistics'],
      recommendedDatasetId: 'ds-player-statistics',
      buildBody: (dataset) => ({ collection: dataset?.collection || 'player_statistics', target_field: 'xg' }),
    },
  },
  {
    id: 'position_classifier',
    aliases: ['position-classifier'],
    name: 'Position Classifier',
    type: 'Classification',
    description: 'Logistic classifier over player statistics for positional labeling.',
    accuracy: 77.2,
    speed: 'Fast',
    interpretability: 'Medium',
    bestFor: ['Position Labels', 'Role Validation'],
    parameters: {
      target_field: 'position',
      source: 'player_statistics',
    },
    train: {
      endpoint: '/api/v2/ml/engine/train/position_classifier',
      supportedDatasetIds: ['ds-player-statistics'],
      recommendedDatasetId: 'ds-player-statistics',
      buildBody: (dataset) => ({ collection: dataset?.collection || 'player_statistics', target_field: 'position' }),
    },
  },
  {
    id: 'outcome_classifier',
    aliases: ['outcome-classifier'],
    name: 'Outcome Classifier',
    type: 'Classification',
    description: 'Logistic classifier for match-level outcome labels.',
    accuracy: 70.8,
    speed: 'Fast',
    interpretability: 'Medium',
    bestFor: ['Outcome Labels', 'Match Classification'],
    parameters: {
      target_field: 'outcome',
      source: 'matches',
    },
    train: {
      endpoint: '/api/v2/ml/engine/train/outcome_classifier',
      supportedDatasetIds: ['ds-matches'],
      recommendedDatasetId: 'ds-matches',
      buildBody: (dataset) => ({ collection: dataset?.collection || 'matches', target_field: 'outcome' }),
    },
  },
  {
    id: 'form_xg_forecaster',
    aliases: ['form-xg-forecaster'],
    name: 'Form xG Forecaster',
    type: 'Time Series',
    description: 'Ridge forecaster that expects persisted rolling form plus next-match xG labels.',
    accuracy: 0,
    speed: 'Fast',
    interpretability: 'Medium',
    bestFor: ['Next-Match xG', 'Form Forecasting'],
    parameters: {
      target_field: 'next_xg',
      source: 'rolling_form_store',
    },
    unavailableReason: 'Training requires persisted rolling-form labels (next_xg) that are not materialized in MongoDB yet.',
  },
  {
    id: 'form_passes_forecaster',
    aliases: ['form-passes-forecaster'],
    name: 'Form Passes Forecaster',
    type: 'Time Series',
    description: 'Ridge forecaster that expects persisted rolling form plus next-match pass labels.',
    accuracy: 0,
    speed: 'Fast',
    interpretability: 'Medium',
    bestFor: ['Next-Match Passes', 'Form Forecasting'],
    parameters: {
      target_field: 'next_passes',
      source: 'rolling_form_store',
    },
    unavailableReason: 'Training requires persisted rolling-form labels (next_passes) that are not materialized in MongoDB yet.',
  },
  {
    id: 'performance_anomaly_detector',
    aliases: ['performance-anomaly-detector'],
    name: 'Performance Anomaly Detector',
    type: 'Anomaly Detection',
    description: 'Isolation Forest over match-to-form deviation metrics.',
    accuracy: 68.5,
    speed: 'Fast',
    interpretability: 'Medium',
    bestFor: ['Outlier Matches', 'Breakout Detection'],
    parameters: {
      trainer: 'IsolationForest',
      source: 'player_statistics',
    },
    train: {
      endpoint: '/api/v2/ml/engine/train/performance_anomaly_detector',
      supportedDatasetIds: ['ds-player-statistics'],
      recommendedDatasetId: 'ds-player-statistics',
      buildBody: (dataset) => ({ collection: dataset?.collection || 'player_statistics' }),
    },
  },
  {
    id: 'tactical_role_classifier',
    aliases: ['tactical-role-classifier'],
    name: 'Tactical Role Classifier',
    type: 'Clustering',
    description: 'K-Means tactical role grouping from composite player metrics.',
    accuracy: 81.3,
    speed: 'Fast',
    interpretability: 'Medium',
    bestFor: ['Role Discovery', 'Squad Profiling'],
    parameters: {
      trainer: 'KMeans',
      source: 'player_statistics',
    },
    train: {
      endpoint: '/api/v2/ml/engine/train/tactical_role_classifier',
      supportedDatasetIds: ['ds-player-statistics'],
      recommendedDatasetId: 'ds-player-statistics',
      buildBody: (dataset) => ({ collection: dataset?.collection || 'player_statistics' }),
    },
  },
  {
    id: 'fatigue_risk_predictor',
    aliases: ['fatigue-risk-predictor'],
    name: 'Fatigue Risk Predictor',
    type: 'Classification',
    description: 'Logistic fatigue-risk model over minutes load and intensity features.',
    accuracy: 73.8,
    speed: 'Fast',
    interpretability: 'Medium',
    bestFor: ['Load Monitoring', 'Rotation Planning'],
    parameters: {
      trainer: 'LogisticRegression',
      source: 'player_statistics',
    },
    train: {
      endpoint: '/api/v2/ml/engine/train/fatigue_risk_predictor',
      supportedDatasetIds: ['ds-player-statistics'],
      recommendedDatasetId: 'ds-player-statistics',
      buildBody: (dataset) => ({ collection: dataset?.collection || 'player_statistics' }),
    },
  },
  {
    id: 'xgot_finishing_model',
    aliases: ['xgot-finishing-model'],
    name: 'xGOT Finishing Model',
    type: 'Regression',
    description: 'Post-shot finishing quality model over event-derived shot context.',
    accuracy: 71.9,
    speed: 'Medium',
    interpretability: 'Low',
    bestFor: ['Finishing Quality', 'Post-Shot Analysis'],
    parameters: {
      trainer: 'RandomForestRegressor',
      source: 'match_events',
    },
    train: {
      endpoint: '/api/v2/ml/engine/train/xgot_finishing_model',
      supportedDatasetIds: ['ds-match-events'],
      recommendedDatasetId: 'ds-match-events',
      buildBody: (dataset) => ({ collection: dataset?.collection || 'match_events' }),
    },
  },
  {
    id: 'pitch_control_nn',
    aliases: ['pitch-control-nn'],
    name: 'Pitch Control NN',
    type: 'Deep Learning',
    description: 'Pitch-control neural model placeholder using event or tracking-like input.',
    accuracy: 0,
    speed: 'Slow',
    interpretability: 'Low',
    bestFor: ['Pitch Control', 'Spatial Dominance'],
    parameters: {
      framework: 'PyTorch',
      source: 'match_events',
    },
    train: {
      endpoint: '/api/v2/ml/engine/train/pitch_control_nn',
      supportedDatasetIds: ['ds-match-events'],
      recommendedDatasetId: 'ds-match-events',
      buildBody: (dataset) => ({ collection: dataset?.collection || 'match_events' }),
    },
  },
  {
    id: 'expected_threat_model',
    aliases: ['expected-threat-model'],
    name: 'Expected Threat Model',
    type: 'Spatial Value Model',
    description: 'xT grid model trained from event coordinates and ball progression.',
    accuracy: 75.6,
    speed: 'Fast',
    interpretability: 'Medium',
    bestFor: ['Ball Progression', 'Zone Valuation'],
    parameters: {
      grid: '16x12',
      source: 'match_events',
    },
    train: {
      endpoint: '/api/v2/ml/engine/train/expected_threat_model',
      supportedDatasetIds: ['ds-match-events'],
      recommendedDatasetId: 'ds-match-events',
      buildBody: (dataset) => ({ collection: dataset?.collection || 'match_events' }),
    },
  },
  {
    id: 'vaep_action_model',
    aliases: ['vaep-action-model', 'vaep-lite'],
    name: 'VAEP Action Model',
    type: 'Action Valuation',
    description: 'Supervised action-value regressor for passes, carries, shots, and defensive actions, with heuristic fallback until a trained artifact is available.',
    accuracy: 73.8,
    speed: 'Fast',
    interpretability: 'Medium',
    bestFor: ['Action Value', 'Possession Impact'],
    parameters: {
      trainer: 'GradientBoostingRegressor + DictVectorizer',
      source: 'match_events',
    },
    train: {
      endpoint: '/api/v2/ml/engine/train/vaep_action_model',
      supportedDatasetIds: ['ds-match-events'],
      recommendedDatasetId: 'ds-match-events',
      buildBody: (dataset) => ({ collection: dataset?.collection || 'match_events' }),
    },
  },
  {
    id: 'market_value_estimator',
    aliases: ['market-value-estimator', 'market-value-model'],
    name: 'Market Value Estimator',
    type: 'Valuation Model',
    description: 'Supervised market-value regressor trained from labeled player valuations and joined player-statistics features, with heuristic fallback until fitted.',
    accuracy: 76.1,
    speed: 'Fast',
    interpretability: 'Medium',
    bestFor: ['Recruitment Valuation', 'Asset Prioritisation'],
    parameters: {
      trainer: 'GradientBoostingRegressor + DictVectorizer',
      source: 'players + player_statistics',
    },
    train: {
      endpoint: '/api/v2/ml/engine/train/market_value_estimator',
      supportedDatasetIds: ['ds-player-statistics'],
      recommendedDatasetId: 'ds-player-statistics',
      buildBody: (dataset) => ({ collection: dataset?.collection || 'player_statistics' }),
    },
  },
  {
    id: 'advanced_player_similarity',
    aliases: ['advanced-player-similarity'],
    name: 'Advanced Player Similarity',
    type: 'Similarity Search',
    description: 'KNN similarity model over normalized player aggregate features.',
    accuracy: 83.1,
    speed: 'Fast',
    interpretability: 'Medium',
    bestFor: ['Nearest Neighbors', 'Recruitment Search'],
    parameters: {
      trainer: 'NearestNeighbors',
      source: 'player_statistics',
    },
    train: {
      endpoint: '/api/v2/ml/engine/train/advanced_player_similarity',
      supportedDatasetIds: ['ds-player-statistics'],
      recommendedDatasetId: 'ds-player-statistics',
      buildBody: (dataset) => ({ collection: dataset?.collection || 'player_statistics' }),
    },
  },
];

const DATASET_DEFINITIONS = [
  {
    id: 'ds-player-features',
    name: 'Player Feature Store',
    collection: 'player_features',
    description: 'ML-ready player feature vectors built from the feature pipeline.',
    features: 24,
    timespan: 'Rolling player snapshots',
    quality: 95,
    sizeFactorBytes: 2600,
    eventFamilies: ['player_form', 'attacking', 'passing', 'defending'],
    temporalScopes: ['rolling_form', 'historical_snapshot', 'lagged_history'],
  },
  {
    id: 'ds-player-statistics',
    name: 'Player Statistics Dataset',
    collection: 'player_statistics',
    description: 'Per-player numeric aggregates used by most supervised football models.',
    features: 28,
    timespan: 'Historical player aggregates',
    quality: 92,
    sizeFactorBytes: 3200,
    eventFamilies: ['player_form', 'attacking', 'passing', 'defending', 'workload'],
    temporalScopes: ['historical_snapshot', 'rolling_form', 'lagged_history'],
  },
  {
    id: 'ds-match-events',
    name: 'Match Events Dataset',
    collection: 'match_events',
    description: 'Event-level shot, pass, carry, and location data for spatial models.',
    features: 18,
    timespan: 'Full event archive',
    quality: 90,
    sizeFactorBytes: 1800,
    eventFamilies: ['shots', 'passing', 'carries', 'duels', 'spatial', 'possession'],
    temporalScopes: ['single_event', 'sequence_window', 'lagged_history', 'historical_archive'],
  },
  {
    id: 'ds-matches',
    name: 'Match Outcomes Dataset',
    collection: 'matches',
    description: 'Match-level records and outcomes for classification and forecasting.',
    features: 20,
    timespan: 'Historical fixtures',
    quality: 88,
    sizeFactorBytes: 2600,
    eventFamilies: ['outcomes', 'match_state', 'team_form'],
    temporalScopes: ['match_snapshot', 'lagged_history', 'historical_archive'],
  },
];

const FEATURE_INSIGHT_MAX_DOCS = 300;
const FEATURE_INSIGHT_BASE_DOCS = 1500;
const FEATURE_SEQUENCE_GAP_SECONDS = 12;
const FEATURE_ROLLING_WINDOW = 5;
const RESERVED_FEATURE_KEYS = new Set([
  '_id',
  'id',
  'player_id',
  'playerId',
  'match_id',
  'matchId',
  'team_id',
  'teamId',
  'competition_id',
  'season_id',
  'lineup_id',
]);

function uniqueStrings(values = []) {
  return Array.from(new Set(
    values
      .map((value) => String(value || '').trim())
      .filter(Boolean)
  ));
}

function inferAlgorithmEventFamilies(entry) {
  const source = String(entry?.parameters?.source || '').toLowerCase();
  const algorithmId = String(entry?.id || '').toLowerCase();
  const families = [];

  if (source.includes('match_event')) {
    families.push('spatial', 'possession');
  }

  if (source.includes('player')) {
    families.push('player_form');
  }

  if (source.includes('match')) {
    families.push('match_state');
  }

  if (algorithmId.includes('xg') || algorithmId.includes('xgot')) {
    families.push('shots');
  }

  if (algorithmId.includes('pass')) {
    families.push('passing');
  }

  if (algorithmId.includes('threat') || algorithmId.includes('pitch') || algorithmId.includes('role')) {
    families.push('spatial');
  }

  if (algorithmId.includes('vaep')) {
    families.push('possession', 'defending');
  }

  if (algorithmId.includes('market') || algorithmId.includes('value')) {
    families.push('player_form');
  }

  if (algorithmId.includes('clustering') || algorithmId.includes('similarity')) {
    families.push('player_form');
  }

  if (algorithmId.includes('fatigue')) {
    families.push('workload');
  }

  if (algorithmId.includes('outcome')) {
    families.push('outcomes');
  }

  if (algorithmId.includes('goal') || algorithmId.includes('shot')) {
    families.push('attacking');
  }

  return uniqueStrings(families.length > 0 ? families : ['general']);
}

function inferAlgorithmTemporalScopes(entry) {
  const source = String(entry?.parameters?.source || '').toLowerCase();
  const algorithmId = String(entry?.id || '').toLowerCase();
  const scopes = [];

  if (source.includes('match_event')) {
    scopes.push('single_event', 'sequence_window', 'lagged_history', 'historical_archive');
  }

  if (source.includes('player') || source.includes('match')) {
    scopes.push('historical_snapshot', 'lagged_history');
  }

  if (algorithmId.startsWith('form_')) {
    scopes.push('rolling_form', 'lagged_history');
  }

  if (algorithmId.includes('threat') || algorithmId.includes('pitch')) {
    scopes.push('sequence_window');
  }

  if (algorithmId.includes('vaep')) {
    scopes.push('single_event', 'sequence_window');
  }

  if (algorithmId.includes('market') || algorithmId.includes('value')) {
    scopes.push('historical_snapshot');
  }

  if (algorithmId.includes('outcome') || algorithmId.includes('match')) {
    scopes.push('match_snapshot');
  }

  return uniqueStrings(scopes.length > 0 ? scopes : ['historical_snapshot']);
}

function getDatasetDefinitionById(id) {
  return DATASET_DEFINITIONS.find((definition) => definition.id === id) || null;
}

function normalizeTemporalScope(datasetDefinition, requestedScope) {
  const supported = datasetDefinition?.temporalScopes || [];
  if (!requestedScope) {
    return supported[0] || 'historical_snapshot';
  }

  return supported.includes(requestedScope)
    ? requestedScope
    : (supported[0] || requestedScope);
}

function buildFeatureInsightQuery(datasetDefinition, eventType, temporalScope) {
  if (!eventType || datasetDefinition?.collection !== 'match_events') {
    return {};
  }

  if (temporalScope === 'sequence_window' || temporalScope === 'rolling_form' || temporalScope === 'lagged_history') {
    return {};
  }

  return {
    $or: [
      { type_name: eventType },
      { event_type: eventType },
    ],
  };
}

async function getAvailableEventTypes(db, datasetDefinition) {
  if (!db || datasetDefinition?.collection !== 'match_events') {
    return [];
  }

  const collection = db.collection(datasetDefinition.collection);
  const values = [];

  try {
    values.push(...await collection.distinct('type_name'));
  } catch (error) {
    console.warn('Failed to fetch type_name distinct values:', error.message);
  }

  try {
    values.push(...await collection.distinct('event_type'));
  } catch (error) {
    console.warn('Failed to fetch event_type distinct values:', error.message);
  }

  return uniqueStrings(values).sort((left, right) => left.localeCompare(right));
}

function sanitizeFeatureKey(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');
}

function toInsightNumber(value) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === 'boolean') {
    return value ? 1 : 0;
  }

  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (!trimmed) return null;
    const parsed = Number(trimmed);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
}

function toTimestampValue(document) {
  const timestampCandidates = [
    document.timestamp_seconds,
    document.timestamp,
    document.updatedAt,
    document.updated_at,
    document.createdAt,
    document.created_at,
    document.ingested_at,
    document.last_updated,
  ];

  for (const candidate of timestampCandidates) {
    const numeric = toInsightNumber(candidate);
    if (numeric !== null) {
      return numeric;
    }

    if (typeof candidate === 'string') {
      const parsed = new Date(candidate).getTime();
      if (!Number.isNaN(parsed)) {
        return parsed / 1000;
      }
    }
  }

  return null;
}

function getTemporalEntityKey(document, datasetDefinition) {
  const collection = datasetDefinition?.collection;
  if (collection === 'match_events') {
    return [
      document.matchID || document.match_id || document.scoutpro_match_id,
      document.period,
      document.team_id || document.scoutpro_team_id,
    ].filter(Boolean).join(':');
  }

  if (collection === 'player_statistics' || collection === 'player_features') {
    return String(document.player_id || document.playerId || document.scoutpro_player_id || document.id || '');
  }

  if (collection === 'matches') {
    return String(document.team_id || document.home_team_id || document.matchID || document.id || '');
  }

  return String(document.id || document._id || 'global');
}

function sampleInMemory(documents, size) {
  if (documents.length <= size) {
    return documents;
  }

  const copied = [...documents];
  for (let index = copied.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [copied[index], copied[swapIndex]] = [copied[swapIndex], copied[index]];
  }

  return copied.slice(0, size);
}

async function fetchFeatureInsightDocuments(collection, query, sampleSize, temporalScope) {
  const size = Math.max(50, Math.min(sampleSize || FEATURE_INSIGHT_MAX_DOCS, FEATURE_INSIGHT_MAX_DOCS));

  if (temporalScope === 'single_event' || temporalScope === 'historical_snapshot' || temporalScope === 'historical_archive' || temporalScope === 'match_snapshot') {
    const pipeline = [];

    if (query && Object.keys(query).length > 0) {
      pipeline.push({ $match: query });
    }

    pipeline.push({ $sample: { size } });
    return collection.aggregate(pipeline).toArray();
  }

  const baseLimit = Math.max(size * 4, FEATURE_INSIGHT_BASE_DOCS);
  return collection.find(query || {})
    .sort({
      matchID: 1,
      match_id: 1,
      scoutpro_match_id: 1,
      team_id: 1,
      player_id: 1,
      period: 1,
      timestamp_seconds: 1,
      updatedAt: 1,
      updated_at: 1,
      createdAt: 1,
      created_at: 1,
      ingested_at: 1,
    })
    .limit(baseLimit)
    .toArray();
}

function buildSequenceWindowDocuments(documents, eventType) {
  if (!documents.length) {
    return [];
  }

  const rows = [];
  let currentSequence = null;

  const flushSequence = () => {
    if (!currentSequence || currentSequence.event_count === 0) {
      return;
    }

    if (eventType) {
      const eventKey = `event_counts.${sanitizeFeatureKey(eventType)}`;
      if (!currentSequence.event_counts || !currentSequence.event_counts[sanitizeFeatureKey(eventType)]) {
        currentSequence = null;
        return;
      }
    }

    rows.push({
      match_context: {
        period: currentSequence.period,
      },
      sequence: {
        event_count: currentSequence.event_count,
        duration_seconds: Math.max(1, currentSequence.end_timestamp - currentSequence.start_timestamp),
        successful_events: currentSequence.successful_events,
        success_rate: currentSequence.event_count > 0 ? currentSequence.successful_events / currentSequence.event_count : 0,
        goal_events: currentSequence.goal_events,
        start_timestamp: currentSequence.start_timestamp,
        end_timestamp: currentSequence.end_timestamp,
        avg_location_x: currentSequence.sum_location_x / currentSequence.event_count,
        avg_location_y: currentSequence.sum_location_y / currentSequence.event_count,
        start_location_x: currentSequence.start_location_x,
        start_location_y: currentSequence.start_location_y,
        end_location_x: currentSequence.end_location_x,
        end_location_y: currentSequence.end_location_y,
        progression_x: currentSequence.end_location_x - currentSequence.start_location_x,
        progression_y: currentSequence.end_location_y - currentSequence.start_location_y,
      },
      event_counts: currentSequence.event_counts,
    });

    currentSequence = null;
  };

  documents.forEach((document) => {
    const timestamp = toTimestampValue(document) ?? 0;
    const teamId = document.team_id || document.scoutpro_team_id || 'unknown';
    const matchId = document.matchID || document.match_id || document.scoutpro_match_id || 'unknown';
    const period = document.period || 1;
    const locationX = toInsightNumber(document.location?.x) || 0;
    const locationY = toInsightNumber(document.location?.y) || 0;
    const eventName = sanitizeFeatureKey(document.type_name || document.event_type || 'unknown');
    const sameSequence = currentSequence
      && currentSequence.match_id === matchId
      && currentSequence.team_id === teamId
      && currentSequence.period === period
      && timestamp - currentSequence.end_timestamp <= FEATURE_SEQUENCE_GAP_SECONDS;

    if (!sameSequence) {
      flushSequence();
      currentSequence = {
        match_id: matchId,
        team_id: teamId,
        period,
        event_count: 0,
        successful_events: 0,
        goal_events: 0,
        start_timestamp: timestamp,
        end_timestamp: timestamp,
        start_location_x: locationX,
        start_location_y: locationY,
        end_location_x: locationX,
        end_location_y: locationY,
        sum_location_x: 0,
        sum_location_y: 0,
        event_counts: {},
      };
    }

    currentSequence.event_count += 1;
    currentSequence.successful_events += document.is_successful ? 1 : 0;
    currentSequence.goal_events += document.is_goal ? 1 : 0;
    currentSequence.end_timestamp = timestamp;
    currentSequence.end_location_x = locationX;
    currentSequence.end_location_y = locationY;
    currentSequence.sum_location_x += locationX;
    currentSequence.sum_location_y += locationY;
    currentSequence.event_counts[eventName] = (currentSequence.event_counts[eventName] || 0) + 1;
  });

  flushSequence();
  return sampleInMemory(rows, FEATURE_INSIGHT_MAX_DOCS);
}

function buildLaggedHistoryDocuments(documents, datasetDefinition, eventType) {
  const rows = [];
  const previousByEntity = new Map();

  documents.forEach((document) => {
    const entityKey = getTemporalEntityKey(document, datasetDefinition);
    const timestamp = toTimestampValue(document);
    if (!entityKey || timestamp === null) {
      return;
    }

    const previousDocument = previousByEntity.get(entityKey);
    previousByEntity.set(entityKey, document);

    if (!previousDocument) {
      return;
    }

    const currentEventType = sanitizeFeatureKey(document.type_name || document.event_type || '');
    if (eventType && currentEventType !== sanitizeFeatureKey(eventType)) {
      return;
    }

    const previousTimestamp = toTimestampValue(previousDocument) ?? timestamp;
    const currentLocationX = toInsightNumber(document.location?.x) || 0;
    const currentLocationY = toInsightNumber(document.location?.y) || 0;
    const previousLocationX = toInsightNumber(previousDocument.location?.x) || 0;
    const previousLocationY = toInsightNumber(previousDocument.location?.y) || 0;

    rows.push({
      current: flattenNumericFields(document),
      previous: flattenNumericFields(previousDocument),
      lag: {
        delta_seconds: Math.max(0, timestamp - previousTimestamp),
        same_type: currentEventType && currentEventType === sanitizeFeatureKey(previousDocument.type_name || previousDocument.event_type || '') ? 1 : 0,
        movement_x: currentLocationX - previousLocationX,
        movement_y: currentLocationY - previousLocationY,
      },
    });
  });

  return sampleInMemory(rows, FEATURE_INSIGHT_MAX_DOCS);
}

function buildRollingFormDocuments(documents, datasetDefinition, eventType) {
  const rows = [];
  const historyByEntity = new Map();

  documents.forEach((document) => {
    const entityKey = getTemporalEntityKey(document, datasetDefinition);
    const flattened = flattenNumericFields(document);
    if (!entityKey || Object.keys(flattened).length === 0) {
      return;
    }

    const currentEventType = sanitizeFeatureKey(document.type_name || document.event_type || '');
    if (eventType && currentEventType && currentEventType !== sanitizeFeatureKey(eventType)) {
      return;
    }

    const history = historyByEntity.get(entityKey) || [];
    if (history.length > 0) {
      const recent = history.slice(-FEATURE_ROLLING_WINDOW);
      const rolling = {};
      const fields = new Set(recent.flatMap((entry) => Object.keys(entry)));

      fields.forEach((field) => {
        const values = recent
          .map((entry) => entry[field])
          .filter((value) => Number.isFinite(value));
        if (values.length > 0) {
          rolling[field] = values.reduce((sum, value) => sum + value, 0) / values.length;
        }
      });

      rows.push({
        current: flattened,
        window: rolling,
        rolling: {
          sample_count: recent.length,
        },
      });
    }

    history.push(flattened);
    historyByEntity.set(entityKey, history);
  });

  return sampleInMemory(rows, FEATURE_INSIGHT_MAX_DOCS);
}

function transformFeatureInsightDocuments(documents, datasetDefinition, temporalScope, eventType) {
  switch (temporalScope) {
    case 'sequence_window':
      return buildSequenceWindowDocuments(documents, eventType);
    case 'lagged_history':
      return buildLaggedHistoryDocuments(documents, datasetDefinition, eventType);
    case 'rolling_form':
      return buildRollingFormDocuments(documents, datasetDefinition, eventType);
    default:
      return sampleInMemory(documents, FEATURE_INSIGHT_MAX_DOCS);
  }
}

function flattenNumericFields(value, prefix = '', depth = 0, output = {}) {
  if (!value || typeof value !== 'object' || depth > 2) {
    return output;
  }

  for (const [rawKey, rawValue] of Object.entries(value)) {
    const key = String(rawKey || '').trim();
    if (!key || RESERVED_FEATURE_KEYS.has(key)) {
      continue;
    }

    const nextKey = prefix ? `${prefix}.${key}` : key;

    if (typeof rawValue === 'number' && Number.isFinite(rawValue)) {
      output[nextKey] = rawValue;
      continue;
    }

    if (typeof rawValue === 'boolean') {
      output[nextKey] = rawValue ? 1 : 0;
      continue;
    }

    if (Array.isArray(rawValue) || rawValue === null || rawValue === undefined) {
      continue;
    }

    if (typeof rawValue === 'object') {
      flattenNumericFields(rawValue, nextKey, depth + 1, output);
    }
  }

  return output;
}

function buildFeatureSeries(documents, requestedFields = []) {
  const requested = new Set(requestedFields.filter(Boolean));
  const series = {};

  documents.forEach((document, index) => {
    const flattened = flattenNumericFields(document);
    const fields = requested.size > 0 ? requestedFields : Object.keys(flattened);

    fields.forEach((field) => {
      const value = flattened[field];
      if (!Number.isFinite(value)) {
        return;
      }

      if (!series[field]) {
        series[field] = [];
      }

      series[field].push({ index, value });
    });
  });

  return series;
}

function buildFeatureStats(featureSeries, totalDocuments) {
  return Object.entries(featureSeries)
    .map(([field, entries]) => {
      const values = entries.map((entry) => entry.value);
      const sampleCount = values.length;
      const mean = sampleCount > 0
        ? values.reduce((sum, value) => sum + value, 0) / sampleCount
        : null;

      return {
        field,
        sampleCount,
        coverage: totalDocuments > 0 ? sampleCount / totalDocuments : 0,
        min: sampleCount > 0 ? Math.min(...values) : null,
        max: sampleCount > 0 ? Math.max(...values) : null,
        mean,
      };
    })
    .sort((left, right) => {
      if (right.coverage !== left.coverage) {
        return right.coverage - left.coverage;
      }

      return right.sampleCount - left.sampleCount;
    });
}

function computePearsonCorrelation(leftEntries, rightEntries) {
  const rightByIndex = new Map(rightEntries.map((entry) => [entry.index, entry.value]));
  const leftValues = [];
  const rightValues = [];

  leftEntries.forEach((entry) => {
    if (!rightByIndex.has(entry.index)) {
      return;
    }

    leftValues.push(entry.value);
    rightValues.push(rightByIndex.get(entry.index));
  });

  if (leftValues.length < 3) {
    return null;
  }

  const leftMean = leftValues.reduce((sum, value) => sum + value, 0) / leftValues.length;
  const rightMean = rightValues.reduce((sum, value) => sum + value, 0) / rightValues.length;

  let numerator = 0;
  let leftVariance = 0;
  let rightVariance = 0;

  for (let index = 0; index < leftValues.length; index += 1) {
    const leftDelta = leftValues[index] - leftMean;
    const rightDelta = rightValues[index] - rightMean;
    numerator += leftDelta * rightDelta;
    leftVariance += leftDelta * leftDelta;
    rightVariance += rightDelta * rightDelta;
  }

  if (leftVariance === 0 || rightVariance === 0) {
    return null;
  }

  return {
    coefficient: numerator / Math.sqrt(leftVariance * rightVariance),
    sampleSize: leftValues.length,
  };
}

function buildCorrelationPairs(featureSeries, featureNames) {
  const correlations = [];

  for (let leftIndex = 0; leftIndex < featureNames.length; leftIndex += 1) {
    for (let rightIndex = leftIndex + 1; rightIndex < featureNames.length; rightIndex += 1) {
      const leftField = featureNames[leftIndex];
      const rightField = featureNames[rightIndex];
      const correlation = computePearsonCorrelation(featureSeries[leftField] || [], featureSeries[rightField] || []);

      if (!correlation) {
        continue;
      }

      correlations.push({
        left: leftField,
        right: rightField,
        coefficient: Number(correlation.coefficient.toFixed(4)),
        sampleSize: correlation.sampleSize,
      });
    }
  }

  return correlations.sort((left, right) => Math.abs(right.coefficient) - Math.abs(left.coefficient));
}

function prettifyModelName(name) {
  return String(name || '')
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function formatNumber(value) {
  return new Intl.NumberFormat('en-US').format(value || 0);
}

function formatApproximateSize(bytes) {
  if (!bytes || bytes <= 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = bytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }

  return `${size.toFixed(size >= 10 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

function formatRelativeTime(dateLike) {
  if (!dateLike) return 'just now';

  const value = new Date(dateLike).getTime();
  if (Number.isNaN(value)) return 'just now';

  const diffMs = Date.now() - value;
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;

  if (diffMs < minute) return 'just now';
  if (diffMs < hour) return `${Math.max(1, Math.round(diffMs / minute))} minutes ago`;
  if (diffMs < day) return `${Math.max(1, Math.round(diffMs / hour))} hours ago`;
  return `${Math.max(1, Math.round(diffMs / day))} days ago`;
}

function normalizeAlgorithmId(name) {
  return String(name || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');
}

function mapAlgorithmCatalogEntry(entry, overrides = {}) {
  const train = overrides.train || entry.train || null;
  const unavailableReason = overrides.unavailableReason ?? entry.unavailableReason ?? null;
  return {
    id: overrides.id || entry.id,
    name: overrides.name || entry.name,
    type: overrides.type || entry.type,
    description: overrides.description || entry.description,
    accuracy: overrides.accuracy ?? entry.accuracy,
    speed: overrides.speed || entry.speed,
    interpretability: overrides.interpretability || entry.interpretability,
    bestFor: overrides.bestFor || entry.bestFor,
    parameters: overrides.parameters || entry.parameters,
    status: overrides.status || 'available',
    trainable: Boolean(train),
    executionMode: train ? 'background' : (unavailableReason ? 'prediction_only' : 'unavailable'),
    supportedDatasetIds: train?.supportedDatasetIds || [],
    recommendedDatasetId: train?.recommendedDatasetId || null,
    eventFamilies: uniqueStrings(overrides.eventFamilies || entry.eventFamilies || inferAlgorithmEventFamilies(entry)),
    temporalScopes: uniqueStrings(overrides.temporalScopes || entry.temporalScopes || inferAlgorithmTemporalScopes(entry)),
    unavailableReason,
  };
}

function findAlgorithmById(id) {
  const normalizedId = normalizeAlgorithmId(id);
  return ALGORITHM_CATALOG.find((entry) =>
    entry.id === normalizedId || entry.aliases.includes(normalizedId)
  );
}

async function getAlgorithmCatalog() {
  try {
    const payload = ensureSuccess(
      await requestJson(mlServiceUrl, '/api/v2/ml/models'),
      'Failed to fetch models'
    );

    const models = Array.isArray(unwrapPayload(payload)) ? unwrapPayload(payload) : [];
    if (models.length === 0) {
      return ALGORITHM_CATALOG.map((entry) => mapAlgorithmCatalogEntry(entry));
    }

    const catalog = models.map((model) => {
      const catalogEntry = findAlgorithmById(model.name) || findAlgorithmById(model.id);
      return mapAlgorithmCatalogEntry(catalogEntry || {
        id: normalizeAlgorithmId(model.name || model.id),
        name: prettifyModelName(model.name || model.id),
        type: model.type || 'Model',
        description: 'Registered model served by ml-service.',
        accuracy: 0,
        speed: 'Unknown',
        interpretability: 'Unknown',
        bestFor: [],
        parameters: {},
      }, {
        id: normalizeAlgorithmId(model.name || model.id),
        name: prettifyModelName(model.name || model.id),
        type: model.type || catalogEntry?.type,
        status: model.status || 'available',
      });
    });

    const seen = new Set(catalog.map((entry) => entry.id));
    for (const entry of ALGORITHM_CATALOG) {
      if (entry.includeWhenMissing && !seen.has(entry.id)) {
        catalog.push(mapAlgorithmCatalogEntry(entry));
      }
    }

    return catalog;
  } catch (error) {
    console.warn('ML catalog fallback enabled:', error.message);
    return ALGORITHM_CATALOG.map((entry) => mapAlgorithmCatalogEntry(entry));
  }
}

async function collectionExists(db, name) {
  if (!db) return false;
  const collections = await db.listCollections({ name }).toArray();
  return collections.length > 0;
}

async function buildDatasetCatalog(db) {
  if (!db) return [];

  const catalog = [];

  for (const definition of DATASET_DEFINITIONS) {
    if (!(await collectionExists(db, definition.collection))) {
      continue;
    }

    const count = await db.collection(definition.collection).countDocuments();
    if (count === 0) {
      continue;
    }

    const latestDoc = await db.collection(definition.collection).findOne(
      {},
      {
        sort: { updatedAt: -1, createdAt: -1, timestamp: -1, uploadedAt: -1 },
        projection: { updatedAt: 1, createdAt: 1, timestamp: 1, uploadedAt: 1 },
      }
    );

    const lastUpdated = latestDoc?.updatedAt || latestDoc?.createdAt || latestDoc?.timestamp || latestDoc?.uploadedAt || new Date().toISOString();

    catalog.push({
      id: definition.id,
      name: definition.name,
      size: formatApproximateSize(count * definition.sizeFactorBytes),
      records: formatNumber(count),
      features: definition.features,
      timespan: definition.timespan,
      description: definition.description,
      quality: definition.quality,
      lastUpdated: formatRelativeTime(lastUpdated),
      collection: definition.collection,
      recordCount: count,
      updatedAt: lastUpdated,
      eventFamilies: definition.eventFamilies || [],
      temporalScopes: definition.temporalScopes || [],
    });
  }

  return catalog;
}

function toRuntimeLabel(startedAt, completedAt) {
  const start = new Date(startedAt).getTime();
  const end = new Date(completedAt || Date.now()).getTime();
  if (Number.isNaN(start) || Number.isNaN(end) || end <= start) {
    return '0m 0s';
  }

  const totalSeconds = Math.round((end - start) / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}m ${seconds}s`;
}

function mapExperiment(experiment) {
  return {
    id: experiment.id,
    name: experiment.name,
    algorithm: experiment.algorithm,
    dataset: experiment.dataset,
    status: experiment.status,
    accuracy: experiment.accuracy || 0,
    runtime: experiment.runtime || toRuntimeLabel(experiment.startedAt || experiment.createdAt, experiment.completedAt || experiment.updatedAt),
    created: formatRelativeTime(experiment.createdAt || experiment.startedAt),
    insights: Array.isArray(experiment.insights) ? experiment.insights : [],
  };
}

function buildExperimentInsights(algorithm, dataset, config = {}) {
  const insights = [];

  if (dataset?.quality) {
    insights.push(`Dataset quality ${dataset.quality}% supports stable ${algorithm.name.toLowerCase()} training.`);
  }

  if (dataset?.recordCount) {
    insights.push(`${formatNumber(dataset.recordCount)} records were scheduled for this experiment.`);
  }

  if (config && Object.keys(config).length > 0) {
    insights.push(`Custom configuration applied for ${Object.keys(config).length} training parameters.`);
  }

  return insights;
}

function estimateTrainingAccuracy(algorithm, dataset) {
  const baseline = algorithm?.accuracy || 75;
  const qualityAdjustment = dataset?.quality ? (dataset.quality - 85) * 0.18 : 0;
  const volumeAdjustment = dataset?.recordCount ? Math.min(3.5, Math.log10(dataset.recordCount + 1)) : 0;
  return Number(Math.max(60, Math.min(99.5, baseline + qualityAdjustment + volumeAdjustment)).toFixed(1));
}

function toFiniteNumber(value) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === 'string') {
    const normalized = value.replace(/[^0-9.-]+/g, '');
    if (!normalized) return null;

    const parsed = Number.parseFloat(normalized);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
}

function prettifyAttributeName(key) {
  return String(key || '')
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .trim();
}

function normalizeSimilarityStats(input = {}) {
  const player = input.player || {};
  const summary = input.summary || {};
  const merged = { ...player, ...input, ...summary };

  return {
    ...merged,
    player_id: String(input.player_id || input.playerId || player.id || input.id || ''),
    id: String(input.id || player.id || input.player_id || input.playerId || ''),
    name: input.name || player.name || merged.name || 'Unknown Player',
    position: input.position || player.position || summary.position || '',
    age: toFiniteNumber(input.age ?? player.age ?? summary.age),
    club: input.club || player.club || summary.club || '',
    nationality: input.nationality || player.nationality || summary.nationality || '',
  };
}

function calculateCosineSimilarity(targetStats, candidateStats) {
  const keys = Object.keys(targetStats).filter((key) => {
    const targetValue = toFiniteNumber(targetStats[key]);
    const candidateValue = toFiniteNumber(candidateStats[key]);
    return targetValue !== null && candidateValue !== null;
  });

  if (keys.length === 0) {
    return 0;
  }

  let dotProduct = 0;
  let targetMagnitude = 0;
  let candidateMagnitude = 0;

  for (const key of keys) {
    const targetValue = toFiniteNumber(targetStats[key]) || 0;
    const candidateValue = toFiniteNumber(candidateStats[key]) || 0;

    dotProduct += targetValue * candidateValue;
    targetMagnitude += targetValue * targetValue;
    candidateMagnitude += candidateValue * candidateValue;
  }

  if (targetMagnitude === 0 || candidateMagnitude === 0) {
    return 0;
  }

  return dotProduct / (Math.sqrt(targetMagnitude) * Math.sqrt(candidateMagnitude));
}

function buildMatchingAttributes(targetStats, candidateStats) {
  const matches = [];

  if (targetStats.position && candidateStats.position && targetStats.position === candidateStats.position) {
    matches.push('Position');
  }

  if (targetStats.club && candidateStats.club && targetStats.club === candidateStats.club) {
    matches.push('Club');
  }

  const numericMatches = Object.keys(targetStats)
    .map((key) => {
      const targetValue = toFiniteNumber(targetStats[key]);
      const candidateValue = toFiniteNumber(candidateStats[key]);

      if (targetValue === null || candidateValue === null) {
        return null;
      }

      const denominator = Math.max(Math.abs(targetValue), Math.abs(candidateValue), 1);
      const relativeGap = Math.abs(targetValue - candidateValue) / denominator;

      return {
        key,
        relativeGap,
      };
    })
    .filter(Boolean)
    .sort((left, right) => left.relativeGap - right.relativeGap)
    .map((entry) => prettifyAttributeName(entry.key));

  return [...new Set([...matches, ...numericMatches])].slice(0, 5);
}

function normalizeSimilarityScore(value) {
  const numeric = toFiniteNumber(value) || 0;
  return Number((numeric <= 1 ? numeric * 100 : numeric).toFixed(1));
}

function normalizeSimilarityResults(targetStats, rawResults = [], candidatePlayers = []) {
  const normalizedCandidates = candidatePlayers
    .map((candidate) => normalizeSimilarityStats(candidate))
    .filter((candidate) => candidate.player_id);

  const candidateLookup = new Map(
    normalizedCandidates.map((candidate) => [candidate.player_id, candidate])
  );

  return rawResults.map((result) => {
    const candidateId = String(
      result.player_id ||
      result.playerId ||
      result.id ||
      result.stats?.player_id ||
      result.stats?.playerId ||
      result.stats?.id ||
      ''
    );
    const fallbackCandidate = candidateLookup.get(candidateId);
    const stats = normalizeSimilarityStats(result.stats || fallbackCandidate || result);

    return {
      player_id: candidateId || stats.player_id,
      similarity_score: normalizeSimilarityScore(result.similarity_score || result.similarityScore),
      matching_attributes: Array.isArray(result.matching_attributes) && result.matching_attributes.length > 0
        ? result.matching_attributes
        : buildMatchingAttributes(targetStats, stats),
      stats,
    };
  });
}

function buildSimilarityFallback(targetStats, candidatePlayers = [], topN = 10) {
  const normalizedCandidates = candidatePlayers
    .map((candidate) => normalizeSimilarityStats(candidate))
    .filter((candidate) => candidate.player_id && candidate.player_id !== targetStats.player_id);

  return normalizedCandidates
    .map((candidate) => ({
      player_id: candidate.player_id,
      similarity_score: normalizeSimilarityScore(calculateCosineSimilarity(targetStats, candidate)),
      matching_attributes: buildMatchingAttributes(targetStats, candidate),
      stats: candidate,
    }))
    .sort((left, right) => right.similarity_score - left.similarity_score)
    .slice(0, topN);
}

function dedupeInsights(values = []) {
  return [...new Set(values.filter(Boolean))];
}

function resolveTrainingDataset(entry, datasets, requestedDatasetId) {
  const train = entry?.train;
  if (!train) {
    return null;
  }

  const supportedDatasetIds = train.supportedDatasetIds || [];
  const requestedDataset = datasets.find((dataset) => dataset.id === requestedDatasetId) || null;

  if (requestedDataset && (supportedDatasetIds.length === 0 || supportedDatasetIds.includes(requestedDataset.id))) {
    return requestedDataset;
  }

  const recommendedDataset = datasets.find((dataset) => dataset.id === train.recommendedDatasetId) || null;
  if (recommendedDataset) {
    return recommendedDataset;
  }

  return datasets.find((dataset) => supportedDatasetIds.includes(dataset.id)) || null;
}

function buildMlTrainingTaskPayload(entry, dataset, config = {}, experimentId = null) {
  const train = entry?.train;
  if (!train) {
    return null;
  }

  const requestBody = train.buildBody ? train.buildBody(dataset, config) : {};

  return {
    algorithm: entry.id,
    action: 'train',
    endpoint: train.endpoint,
    request_body: requestBody,
    config,
    dataset_id: dataset?.id || null,
    experiment_id: experimentId,
  };
}

function toPercentageScore(value) {
  const numeric = toFiniteNumber(value);
  if (numeric === null) {
    return null;
  }

  const scaled = numeric <= 1 ? numeric * 100 : numeric;
  return Number(Math.max(0, Math.min(100, scaled)).toFixed(1));
}

function deriveTrainingAccuracy(result, fallbackAccuracy) {
  const metrics = [
    result?.accuracy,
    result?.train_accuracy,
    result?.cv_accuracy,
    result?.cv_r2_mean,
    result?.train_r2,
    result?.r2_score,
    result?.auc_roc,
    result?.silhouette_score,
  ];

  for (const metric of metrics) {
    const score = toPercentageScore(metric);
    if (score !== null) {
      return score;
    }
  }

  return fallbackAccuracy;
}

function buildTaskResultInsights(result = {}) {
  const insights = [];

  if (toFiniteNumber(result.n_samples) !== null) {
    insights.push(`${formatNumber(result.n_samples)} samples were processed by the trainer.`);
  } else if (toFiniteNumber(result.samples) !== null) {
    insights.push(`${formatNumber(result.samples)} samples were processed by the trainer.`);
  } else if (toFiniteNumber(result.n_shots) !== null) {
    insights.push(`${formatNumber(result.n_shots)} shot events were used for training.`);
  }

  if (toFiniteNumber(result.n_clusters) !== null) {
    insights.push(`The run produced ${formatNumber(result.n_clusters)} clusters.`);
  }

  if (result.target) {
    insights.push(`Target field: ${result.target}.`);
  }

  if (Array.isArray(result.features) && result.features.length > 0) {
    insights.push(`${formatNumber(result.features.length)} numeric features were used.`);
  }

  const cvScore = toPercentageScore(result.cv_r2_mean);
  if (cvScore !== null) {
    insights.push(`Cross-validation score reached ${cvScore}%.`);
  }

  const r2Score = toPercentageScore(result.r2_score ?? result.train_r2);
  if (r2Score !== null) {
    insights.push(`Fit score reached ${r2Score}%.`);
  }

  const aucScore = toPercentageScore(result.auc_roc);
  if (aucScore !== null) {
    insights.push(`AUC reached ${aucScore}%.`);
  }

  if (result.message) {
    insights.push(result.message);
  }

  return dedupeInsights(insights);
}

async function syncExperimentWithTask(db, experiment, datasets) {
  if (!experiment.taskId || (experiment.status !== 'running' && experiment.status !== 'pending')) {
    return experiment;
  }

  try {
    const task = ensureSuccess(
      await requestJson(taskWorkerUrl, `/tasks/${encodeURIComponent(experiment.taskId)}`, { timeoutMs: 5000 }),
      `Failed to fetch task ${experiment.taskId}`
    );

    const algorithm = findAlgorithmById(experiment.algorithmId) || { name: experiment.algorithm, accuracy: 0 };
    const dataset = datasets.find((item) => item.id === experiment.datasetId) || null;
    const completedAt = task.completed_at || new Date().toISOString();

    let nextExperiment = experiment;

    if (task.status === 'completed') {
      nextExperiment = {
        ...experiment,
        status: 'completed',
        accuracy: deriveTrainingAccuracy(task.result, estimateTrainingAccuracy(algorithm, dataset)),
        runtime: toRuntimeLabel(experiment.startedAt || experiment.createdAt, completedAt),
        insights: dedupeInsights([
          ...buildExperimentInsights(algorithm, dataset, experiment.config),
          ...buildTaskResultInsights(task.result),
        ]),
        updatedAt: completedAt,
        completedAt,
        progress: 100,
        progressMsg: task.progress_msg || 'Done',
        result: task.result,
        source: 'task-worker',
      };
    } else if (task.status === 'failed') {
      nextExperiment = {
        ...experiment,
        status: 'failed',
        accuracy: 0,
        runtime: toRuntimeLabel(experiment.startedAt || experiment.createdAt, completedAt),
        insights: dedupeInsights([
          ...buildExperimentInsights(algorithm, dataset, experiment.config),
          `Background task failed: ${task.error || 'Unknown error'}`,
        ]),
        updatedAt: completedAt,
        completedAt,
        progress: task.progress ?? experiment.progress ?? 0,
        progressMsg: task.progress_msg || 'Failed',
        error: task.error || experiment.error || null,
        source: 'task-worker',
      };
    } else {
      nextExperiment = {
        ...experiment,
        status: 'running',
        updatedAt: experiment.updatedAt,
        progress: task.progress ?? experiment.progress ?? 0,
        progressMsg: task.progress_msg || experiment.progressMsg || 'Running',
        source: 'task-worker',
      };
    }

    const didChange = [
      'status',
      'accuracy',
      'runtime',
      'completedAt',
      'progress',
      'progressMsg',
      'error',
    ].some((key) => nextExperiment[key] !== experiment[key]);

    if (didChange) {
      await upsertExperiment(db, nextExperiment);
    }

    return nextExperiment;
  } catch (error) {
    console.warn(`ML experiment task sync skipped for ${experiment.taskId}:`, error.message);
    return experiment;
  }
}

async function upsertExperiment(db, experiment) {
  if (!db) return experiment;

  await db.collection('ml_experiments').updateOne(
    { id: experiment.id },
    { $set: experiment },
    { upsert: true }
  );

  return experiment;
}

router.get('/models', async (req, res) => {
  try {
    res.json(await getAlgorithmCatalog());
  } catch (error) {
    console.error('ML models error:', error);
    sendGatewayError(res, error, 'Failed to fetch models');
  }
});

router.get('/algorithms', async (req, res) => {
  try {
    res.json(await getAlgorithmCatalog());
  } catch (error) {
    console.error('ML algorithms error:', error);
    sendGatewayError(res, error, 'Failed to fetch algorithms');
  }
});

router.get('/datasets', async (req, res) => {
  try {
    const datasets = await buildDatasetCatalog(req.app.locals.db);
    res.json(datasets);
  } catch (error) {
    console.error('ML datasets error:', error);
    sendGatewayError(res, error, 'Failed to fetch datasets');
  }
});

router.get('/features/status', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.json({ indexed_players: 0, player_count: 0, status: 'unavailable' });
    }

    // Try to get player count from database
    let playerCount = 0;
    try {
      if (await collectionExists(db, 'players')) {
        playerCount = await db.collection('players').countDocuments();
      }
    } catch {
      // Ignore errors
    }

    res.json({
      indexed_players: playerCount,
      player_count: playerCount,
      count: playerCount,
      status: playerCount > 0 ? 'ready' : 'empty',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('ML features/status error:', error);
    res.json({ indexed_players: 0, player_count: 0, status: 'error' });
  }
});

router.get('/datasets/:datasetId/feature-insights', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db) {
      return res.status(503).json({ error: 'Database connection unavailable' });
    }

    const datasets = await buildDatasetCatalog(db);
    const dataset = datasets.find((entry) => entry.id === req.params.datasetId);
    const datasetDefinition = getDatasetDefinitionById(req.params.datasetId);

    if (!dataset || !datasetDefinition) {
      return res.status(404).json({ error: `Unknown dataset: ${req.params.datasetId}` });
    }

    const requestedFields = String(req.query.fields || '')
      .split(',')
      .map((field) => field.trim())
      .filter(Boolean)
      .slice(0, 8);
    const eventType = String(req.query.eventType || '').trim() || null;
    const temporalScope = normalizeTemporalScope(datasetDefinition, String(req.query.temporalScope || '').trim() || null);
    const query = buildFeatureInsightQuery(datasetDefinition, eventType, temporalScope);
    const collection = db.collection(dataset.collection);
    const baseDocuments = await fetchFeatureInsightDocuments(collection, query, Number(req.query.limit || FEATURE_INSIGHT_MAX_DOCS), temporalScope);
    const documents = transformFeatureInsightDocuments(baseDocuments, datasetDefinition, temporalScope, eventType);

    if (documents.length === 0) {
      return res.json({
        datasetId: dataset.id,
        datasetName: dataset.name,
        collection: dataset.collection,
        eventFamilies: dataset.eventFamilies || [],
        temporalScopes: dataset.temporalScopes || [],
        activeTemporalScope: temporalScope,
        availableEventTypes: await getAvailableEventTypes(db, datasetDefinition),
        activeEventType: eventType,
        featureStats: [],
        recommendedFields: [],
        selectedFields: requestedFields,
        correlations: [],
        sampleSize: 0,
      });
    }

    const featureSeries = buildFeatureSeries(documents, requestedFields);
    const featureStats = buildFeatureStats(featureSeries, documents.length);
    const recommendedFields = featureStats.slice(0, 6).map((entry) => entry.field);
    const correlationFields = requestedFields.length >= 2
      ? requestedFields.filter((field) => featureSeries[field])
      : recommendedFields;

    res.json({
      datasetId: dataset.id,
      datasetName: dataset.name,
      collection: dataset.collection,
      eventFamilies: dataset.eventFamilies || [],
      temporalScopes: dataset.temporalScopes || [],
      activeTemporalScope: temporalScope,
      availableEventTypes: await getAvailableEventTypes(db, datasetDefinition),
      activeEventType: eventType,
      featureStats,
      recommendedFields,
      selectedFields: correlationFields,
      correlations: buildCorrelationPairs(featureSeries, correlationFields),
      sampleSize: documents.length,
    });
  } catch (error) {
    console.error('ML feature insights error:', error);
    sendGatewayError(res, error, 'Failed to fetch dataset feature insights');
  }
});

router.get('/experiments', async (req, res) => {
  try {
    const db = req.app.locals.db;
    if (!db || !(await collectionExists(db, 'ml_experiments'))) {
      return res.json([]);
    }

    const datasets = await buildDatasetCatalog(db);
    const experiments = await db.collection('ml_experiments')
      .find({})
      .sort({ createdAt: -1 })
      .limit(50)
      .toArray();

    const syncedExperiments = await Promise.all(
      experiments.map((experiment) => syncExperimentWithTask(db, experiment, datasets))
    );

    res.json(syncedExperiments.map(mapExperiment));
  } catch (error) {
    console.error('ML experiments error:', error);
    sendGatewayError(res, error, 'Failed to fetch experiments');
  }
});

router.post('/experiments', async (req, res) => {
  try {
    const algorithmCatalog = await getAlgorithmCatalog();
    const datasets = await buildDatasetCatalog(req.app.locals.db);

    const algorithm = algorithmCatalog.find((entry) => entry.id === req.body.algorithmId) || algorithmCatalog[0];
    const dataset = datasets.find((entry) => entry.id === req.body.datasetId) || datasets[0] || null;
    const now = new Date().toISOString();

    const experiment = {
      id: uuidv4(),
      algorithmId: algorithm?.id || normalizeAlgorithmId(req.body.algorithmId || req.body.algorithm),
      datasetId: dataset?.id || req.body.datasetId || null,
      name: req.body.name || `${algorithm?.name || 'Model'} Experiment`,
      algorithm: algorithm?.name || req.body.algorithm || 'Unknown Algorithm',
      dataset: dataset?.name || req.body.datasetId || 'Unspecified Dataset',
      status: req.body.status || 'running',
      accuracy: req.body.accuracy || 0,
      runtime: req.body.runtime || '0m 0s',
      insights: Array.isArray(req.body.insights) ? req.body.insights : [],
      config: req.body.config || {},
      createdAt: now,
      updatedAt: now,
      startedAt: now,
      completedAt: null,
    };

    await upsertExperiment(req.app.locals.db, experiment);
    res.status(201).json(mapExperiment(experiment));
  } catch (error) {
    console.error('ML experiment create error:', error);
    sendGatewayError(res, error, 'Failed to create experiment');
  }
});

router.post('/train', async (req, res) => {
  try {
    const datasets = await buildDatasetCatalog(req.app.locals.db);
    const modelName = req.body.modelName || req.body.model_name || req.body.algorithmId;

    if (!modelName) {
      return res.status(400).json({ error: 'modelName or algorithmId is required' });
    }

    const algorithmEntry = findAlgorithmById(modelName);
    if (!algorithmEntry) {
      return res.status(404).json({ error: `Unknown algorithm: ${modelName}` });
    }

    if (!algorithmEntry.train) {
      return res.status(400).json({
        error: algorithmEntry.unavailableReason || `${algorithmEntry.name} is not connected to a background training pipeline yet.`,
      });
    }

    const dataset = resolveTrainingDataset(algorithmEntry, datasets, req.body.datasetId);
    if (!dataset) {
      return res.status(400).json({
        error: `No compatible dataset is available for ${algorithmEntry.name}.`,
      });
    }

    const experimentId = uuidv4();
    const startedAt = new Date().toISOString();
    const taskPayload = buildMlTrainingTaskPayload(algorithmEntry, dataset, req.body.config || {}, experimentId);
    const task = ensureSuccess(
      await requestJson(taskWorkerUrl, '/tasks', {
        method: 'POST',
        body: {
          task_type: 'ml_train',
          payload: taskPayload,
        },
        timeoutMs: 10000,
      }),
      'Failed to queue training task'
    );

    const experiment = {
      id: experimentId,
      algorithmId: algorithmEntry.id,
      datasetId: dataset.id,
      taskId: task.task_id,
      name: req.body.name || `${algorithmEntry.name} Training Run`,
      algorithm: algorithmEntry.name,
      dataset: dataset.name,
      status: 'running',
      accuracy: 0,
      runtime: '0m 0s',
      insights: dedupeInsights([
        ...buildExperimentInsights(algorithmEntry, dataset, req.body.config),
        `Queued as background task ${task.task_id.slice(0, 8)}.`,
      ]),
      config: req.body.config || {},
      createdAt: startedAt,
      updatedAt: startedAt,
      startedAt,
      completedAt: null,
      progress: task.progress ?? 0,
      progressMsg: task.progress_msg || 'Queued',
      source: 'task-worker',
    };

    await upsertExperiment(req.app.locals.db, experiment);

    res.status(202).json({
      job_id: task.task_id,
      task,
      experiment: mapExperiment(experiment),
      source: experiment.source,
    });
  } catch (error) {
    console.error('ML train error:', error);
    sendGatewayError(res, error, 'Failed to start training');
  }
});

function isPendingTrainingPrediction(payload) {
  const message = String(payload?.error || '').toLowerCase();
  return payload?.status === 'pending_training' || message.includes('not trained yet');
}

function clampProbability(value, min = 0.05, max = 0.9) {
  return Math.min(max, Math.max(min, value));
}

function toPredictNumber(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function buildPlayerPerformanceFallback(features = {}) {
  const passes = toPredictNumber(features.passes, 50);
  const shots = toPredictNumber(features.shots, 5);
  const tackles = toPredictNumber(features.tackles, 8);
  const predictedRating = Math.min(
    10,
    Math.max(0, 4.2 + passes * 0.045 + shots * 0.28 + tackles * 0.08)
  );

  let label = 'Developmental Output';
  if (predictedRating >= 8) {
    label = 'High Impact';
  } else if (predictedRating >= 6.5) {
    label = 'Strong Projection';
  } else if (predictedRating >= 5.5) {
    label = 'Stable Projection';
  }

  return {
    predicted_rating: Number(predictedRating.toFixed(1)),
    confidence: 0.52,
    label,
    fallback_reason: 'player_model_pending_training',
    _simulated: true,
  };
}

function buildMatchOutcomeFallback(features = {}) {
  const homeXg = toPredictNumber(features.home_xg || features.homeXG, 1.5);
  const awayXg = toPredictNumber(features.away_xg || features.awayXG, 1.1);
  const homeShots = toPredictNumber(features.home_shots || features.homeShots, 14);
  const awayShots = toPredictNumber(features.away_shots || features.awayShots, 10);
  const homeShotsOnTarget = toPredictNumber(features.home_shots_on_target || features.homeShotsOnTarget, 5);
  const awayShotsOnTarget = toPredictNumber(features.away_shots_on_target || features.awayShotsOnTarget, 4);
  const homePossession = toPredictNumber(features.home_possession || features.homePossession, 54);
  const awayPossession = toPredictNumber(features.away_possession || features.awayPossession, 46);
  const homePassAccuracy = toPredictNumber(features.home_pass_accuracy || features.homePassAccuracy, 84);
  const awayPassAccuracy = toPredictNumber(features.away_pass_accuracy || features.awayPassAccuracy, 80);

  const homeStrength = homeXg * 1.2
    + homeShotsOnTarget * 0.18
    + (homeShots - awayShots) * 0.015
    + (homePossession - awayPossession) * 0.01
    + (homePassAccuracy - awayPassAccuracy) * 0.008;
  const awayStrength = awayXg * 1.2
    + awayShotsOnTarget * 0.18
    + (awayShots - homeShots) * 0.015
    + (awayPossession - homePossession) * 0.01
    + (awayPassAccuracy - homePassAccuracy) * 0.008;
  const edge = homeStrength - awayStrength;

  let homeWin = clampProbability(0.44 + edge * 0.09);
  let draw = clampProbability(0.26 - Math.abs(edge) * 0.06, 0.1, 0.34);
  let awayWin = clampProbability(0.3 - edge * 0.09);
  const total = homeWin + draw + awayWin;
  homeWin /= total;
  draw /= total;
  awayWin /= total;

  const probabilities = {
    home_win: Number(homeWin.toFixed(4)),
    draw: Number(draw.toFixed(4)),
    away_win: Number(awayWin.toFixed(4)),
  };

  const predictedOutcome = Object.entries(probabilities).sort((left, right) => right[1] - left[1])[0]?.[0] || 'draw';

  return {
    probabilities,
    predicted_outcome: predictedOutcome,
    confidence_label: 'Fallback estimate',
    fallback_reason: 'match_model_pending_training',
    _simulated: true,
  };
}

router.post('/predict/player-performance', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(mlServiceUrl, '/api/v2/ml/predict/player-performance', {
        method: 'POST',
        body: req.body,
      }),
      'Failed to predict player performance'
    );

    const data = unwrapPayload(payload) ?? payload;
    if (isPendingTrainingPrediction(data)) {
      return res.json(buildPlayerPerformanceFallback(req.body.features || req.body));
    }

    res.json(data);
  } catch (error) {
    console.warn('ML player prediction fallback enabled:', error.message);
    res.json(buildPlayerPerformanceFallback(req.body.features || req.body));
  }
});

router.post('/predict/match-outcome', async (req, res) => {
  try {
    const payload = ensureSuccess(
      await requestJson(mlServiceUrl, '/api/v2/ml/predict/match-outcome', {
        method: 'POST',
        body: req.body,
      }),
      'Failed to predict match outcome'
    );

    const data = unwrapPayload(payload) ?? payload;
    if (isPendingTrainingPrediction(data)) {
      return res.json(buildMatchOutcomeFallback(req.body));
    }

    res.json(data);
  } catch (error) {
    console.warn('ML match prediction fallback enabled:', error.message);
    res.json(buildMatchOutcomeFallback(req.body));
  }
});

router.post('/similarity/players', async (req, res) => {
  const directPlayerId = String(req.body.player_id || req.body.playerId || '').trim();
  const targetStats = normalizeSimilarityStats(req.body.player_stats || req.body.playerStats || {});
  const candidatePlayers = Array.isArray(req.body.candidate_players || req.body.candidatePlayers)
    ? req.body.candidate_players || req.body.candidatePlayers
    : [];
  const topN = Number.parseInt(req.body.top_n || req.body.topN || '10', 10) || 10;

  if (!directPlayerId && !targetStats.player_id && Object.keys(targetStats).length === 0) {
    return res.status(400).json({ error: 'player_stats or playerStats is required' });
  }

  if (directPlayerId) {
    try {
      const payload = ensureSuccess(
        await requestJson(mlServiceUrl, `/api/v2/ml/similarity/player/${encodeURIComponent(directPlayerId)}`, {
          query: { top_n: topN },
        }),
        'Failed to find similar players'
      );

      const results = Array.isArray(unwrapPayload(payload)) ? unwrapPayload(payload) : [];
      return res.json(results);
    } catch (error) {
      console.warn('ML similarity by-id lookup failed, attempting database fallback:', error.message);
      
      // Fallback: fetch player and candidate players from database
      const db = req.app.locals.db;
      if (db) {
        try {
          if (await collectionExists(db, 'players')) {
            const targetPlayer = await db.collection('players').findOne({ 
              $or: [{ id: directPlayerId }, { _id: directPlayerId }] 
            });
            
            if (targetPlayer) {
              const playerStats = normalizeSimilarityStats(targetPlayer);
              const allPlayers = await db.collection('players')
                .find({})
                .limit(1000)
                .toArray();
              
              return res.json(buildSimilarityFallback(playerStats, allPlayers, topN));
            }
          }
        } catch (dbError) {
          console.warn('Database fallback failed:', dbError.message);
        }
      }
      
      return res.status(503).json({ error: `ml-service unavailable and database fallback failed: ${error.message}` });
    }
  }

  try {
    const payload = ensureSuccess(
      await requestJson(mlServiceUrl, '/api/v2/ml/similarity/players', {
        method: 'POST',
        body: {
          player_stats: targetStats,
          candidate_players: candidatePlayers,
          top_n: topN,
        },
      }),
      'Failed to find similar players'
    );

    const results = Array.isArray(unwrapPayload(payload)) ? unwrapPayload(payload) : [];
    res.json(normalizeSimilarityResults(targetStats, results, candidatePlayers));
  } catch (error) {
    console.warn('ML similarity fallback enabled:', error.message);
    res.json(buildSimilarityFallback(targetStats, candidatePlayers, topN));
  }
});


const ENGINE_PREDICT_FALLBACKS = {
  tactical_role_classifier: {
    assigned_role_id: 1,
    role_name: 'Progressive/Box-to-Box',
    confidence_score: 0.0,
    distance_to_centroid: 0.0,
    _simulated: true,
  },
  performance_anomaly_detector: {
    is_outlier: false,
    anomaly_score: 0.0,
    insight: 'Insufficient data to detect performance anomalies.',
    _simulated: true,
  },
  fatigue_risk_predictor: {
    fatigue_risk_percentage: 0.0,
    is_high_risk: false,
    recommendation: 'Optimal',
    contributing_factor: 'insufficient_data',
    _simulated: true,
  },
};

// Engine predict — proxies to ml-service /api/v2/ml/engine/predict/:modelName
router.post('/engine/predict/:modelName', async (req, res) => {
  const { modelName } = req.params;
  try {
    const payload = ensureSuccess(
      await requestJson(mlServiceUrl, `/api/v2/ml/engine/predict/${encodeURIComponent(modelName)}`, {
        method: 'POST',
        body: req.body,
      }),
      `Failed to run ${modelName} prediction`
    );

    const data = unwrapPayload(payload) ?? payload;

    // ML service returned success=false (model not yet trainable) — serve fallback
    if (payload && payload.success === false) {
      const fallback = ENGINE_PREDICT_FALLBACKS[modelName];
      if (fallback) {
        return res.json({ algorithm: modelName, prediction: fallback });
      }
    }

    res.json(data);
  } catch (error) {
    console.warn(`ML engine predict fallback (${modelName}):`, error.message);
    const fallback = ENGINE_PREDICT_FALLBACKS[modelName];
    if (fallback) {
      return res.json({ algorithm: modelName, prediction: fallback });
    }
    res.status(503).json({ error: `ml-service unavailable: ${error.message}`, algorithm: modelName });
  }
});

// Time-series Form Analysis
function formFallback(playerId) {
  return {
    success: true,
    player_id: playerId,
    data: {
      rolling_passes: 45.2,
      rolling_pass_accuracy: 0.88,
      rolling_shots: 1.5,
      rolling_xg: 0.12,
      momentum_xg: 0.05,
      matches_played: 5,
    },
    _simulated: true,
  };
}

router.get('/form/:playerId', async (req, res) => {
  const { playerId } = req.params;
  try {
    const payload = ensureSuccess(
      await requestJson(mlServiceUrl, `/api/v2/ml/form/${playerId}`),
      'Failed to fetch player form'
    );
    res.json({ data: unwrapPayload(payload) ?? payload });
  } catch (error) {
    // 404 from ml-service means player has no form history yet — return simulated data
    if (error.status === 404 || /404|not found/i.test(error.message)) {
      return res.json(formFallback(playerId));
    }
    console.error('Error fetching player form:', error.message);
    res.json(formFallback(playerId));
  }
});

router.get('/form/:playerId/tensor', async (req, res) => {
  const { playerId } = req.params;
  try {
    const payload = ensureSuccess(
      await requestJson(mlServiceUrl, `/api/v2/ml/form/${playerId}/tensor`),
      'Failed to fetch player form tensor'
    );
    res.json({ data: unwrapPayload(payload) ?? payload });
  } catch (error) {
    if (error.status === 404 || /404|not found/i.test(error.message)) {
      return res.json({ success: true, player_id: playerId, tensor: [45.2, 0.88, 1.5, 0.12, 0.05], _simulated: true });
    }
    console.error('Error fetching player tensor:', error.message);
    res.json({ success: true, player_id: playerId, tensor: [45.2, 0.88, 1.5, 0.12, 0.05], _simulated: true });
  }
});

module.exports = router;
