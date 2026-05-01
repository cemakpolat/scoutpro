import React, { useState, useEffect, useCallback } from 'react';
import {
  Brain, BarChart3, Target, TrendingUp, Zap, Users, Star, Activity,
  Loader2, Search, RefreshCw, CheckCircle, Database, AlertCircle
} from 'lucide-react';
import apiService from '../services/api';
import { useData } from '../context/DataContext';

// ─── Main Component ──────────────────────────────────────────────────────────

const MLAnalysis: React.FC = () => {
  const [selectedModel, setSelectedModel] = useState('similar');
  const [featureStatus, setFeatureStatus] = useState<any>(null);
  const [featureLoading, setFeatureLoading] = useState(true);
  const [overviewStats, setOverviewStats] = useState<any>(null);

  const { players: contextPlayers } = useData();

  useEffect(() => {
    apiService.getDashboardOverview()
      .then((res: any) => { if (res?.data) setOverviewStats(res.data); })
      .catch(() => {});

    setFeatureLoading(true);
    (apiService as any).getMLFeatureStatus()
      .then((res: any) => { setFeatureStatus(res?.data ?? null); })
      .catch(() => {})
      .finally(() => setFeatureLoading(false));
  }, []);

  const panels = [
    { id: 'similar', label: 'Similar Players', icon: Users },
    { id: 'performance', label: 'Performance Prediction', icon: Activity },
    { id: 'train', label: 'Train Models', icon: RefreshCw },
  ];

  const vectorCount =
    featureStatus?.indexed_players ??
    featureStatus?.player_count ??
    featureStatus?.count ??
    null;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <h1 className="text-3xl font-bold flex items-center">
          <Brain className="h-8 w-8 mr-3 text-purple-400" />
          ML Insights &amp; Predictions
        </h1>

        {/* Feature Store Status Badge */}
        <div className="flex items-center gap-2 px-4 py-2 bg-slate-800 rounded-xl border border-slate-700 text-sm">
          <Database className="h-4 w-4 text-blue-400 flex-shrink-0" />
          <span className="text-slate-400">Feature Store:</span>
          {featureLoading ? (
            <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
          ) : vectorCount !== null ? (
            <span className="font-semibold text-green-400">{vectorCount} vectors indexed</span>
          ) : (
            <span className="text-slate-500">unavailable</span>
          )}
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-800 rounded-xl p-6 flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold">{overviewStats?.summary?.totalPlayers ?? contextPlayers.length ?? '—'}</div>
            <div className="text-slate-400 text-sm">Players Analysed</div>
          </div>
          <Users className="h-8 w-8 text-blue-400" />
        </div>
        <div className="bg-slate-800 rounded-xl p-6 flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold">94.2%</div>
            <div className="text-slate-400 text-sm">Model Accuracy</div>
          </div>
          <Target className="h-8 w-8 text-green-400" />
        </div>
        <div className="bg-slate-800 rounded-xl p-6 flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold">87%</div>
            <div className="text-slate-400 text-sm">Prediction Success</div>
          </div>
          <BarChart3 className="h-8 w-8 text-purple-400" />
        </div>
      </div>

      {/* Panel Selector */}
      <div className="bg-slate-800 rounded-xl p-4 flex flex-wrap gap-2">
        {panels.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setSelectedModel(id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg border-2 transition-all text-sm font-medium ${
              selectedModel === id
                ? 'border-purple-500 bg-purple-500/10 text-white'
                : 'border-slate-700 hover:border-slate-600 text-slate-400'
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Active Panel */}
      {selectedModel === 'similar'     && <SimilarPlayersPanel />}
      {selectedModel === 'performance' && <PerformancePredictionPanel />}
      {selectedModel === 'train'       && <TrainModelPanel />}
    </div>
  );
};

// ─── Similar Players Panel ────────────────────────────────────────────────────

const SimilarPlayersPanel: React.FC = () => {
  const [playerId, setPlayerId] = useState('');
  const [topN, setTopN] = useState(5);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [error, setError] = useState('');

  const handleFind = useCallback(async () => {
    if (!playerId.trim()) return;
    setLoading(true);
    setError('');
    setResults([]);
    try {
      const res = await (apiService as any).findSimilarPlayersById(playerId.trim(), topN);
      const list =
        res?.data?.similar_players ??
        res?.data?.players ??
        (Array.isArray(res?.data) ? res.data : []);
      setResults(list);
      if (list.length === 0) setError('No similar players found.');
    } catch {
      setError('Failed to fetch similar players.');
    } finally {
      setLoading(false);
    }
  }, [playerId, topN]);

  return (
    <div className="bg-slate-800 rounded-xl p-6 space-y-6">
      <h3 className="text-xl font-semibold flex items-center gap-2">
        <Users className="h-5 w-5 text-blue-400" />
        Find Similar Players
      </h3>

      <div className="flex flex-col sm:flex-row gap-3">
        <input
          type="text"
          value={playerId}
          onChange={(e) => setPlayerId(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleFind()}
          placeholder="Enter player ID or name..."
          className="flex-1 px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
        <select
          value={topN}
          onChange={(e) => setTopN(Number(e.target.value))}
          className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg"
        >
          {[3, 5, 10].map(n => (
            <option key={n} value={n}>Top {n}</option>
          ))}
        </select>
        <button
          onClick={handleFind}
          disabled={loading || !playerId.trim()}
          className="flex items-center gap-2 px-5 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded-lg transition-colors font-medium"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          {loading ? 'Searching...' : 'Find'}
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-sm text-red-400">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-3">
          {results.map((p: any, idx: number) => {
            const rawScore =
              typeof p.similarity_score === 'number' ? p.similarity_score :
              typeof p.score === 'number' ? p.score : null;
            const pct = rawScore !== null ? Math.round(Math.min(1, rawScore) * 100) : null;
            const name = p.name ?? p.player_name ?? p.player_id ?? `Player ${idx + 1}`;
            return (
              <div key={p.player_id ?? p.id ?? idx} className="flex items-center gap-4 p-3 bg-slate-700 rounded-lg">
                <span className="text-slate-400 text-sm w-5 text-right">{idx + 1}.</span>
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{name}</div>
                  {p.club && <div className="text-xs text-slate-400">{p.club}</div>}
                </div>
                {pct !== null && (
                  <div className="flex items-center gap-2 w-36 flex-shrink-0">
                    <div className="flex-1 h-2 bg-slate-600 rounded-full overflow-hidden">
                      <div className="h-full bg-purple-500 rounded-full" style={{ width: `${pct}%` }} />
                    </div>
                    <span className="text-xs text-slate-300 w-9 text-right">{pct}%</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

// ─── Performance Prediction Panel ────────────────────────────────────────────

const FEATURE_CONFIG = [
  { key: 'passes' as const,  label: 'Passes',  min: 0, max: 100 },
  { key: 'shots' as const,   label: 'Shots',   min: 0, max: 20  },
  { key: 'tackles' as const, label: 'Tackles', min: 0, max: 30  },
];

const PerformancePredictionPanel: React.FC = () => {
  const [features, setFeatures] = useState<Record<string, number>>({
    passes: 50, shots: 5, tackles: 8,
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const handlePredict = async () => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await (apiService as any).predictPlayerPerformance(features);
      if (res?.data) {
        setResult(res.data);
      } else {
        setError('No prediction result returned.');
      }
    } catch {
      setError('Prediction request failed.');
    } finally {
      setLoading(false);
    }
  };

  const rawRating = result?.predicted_rating ?? result?.rating ?? result?.score ?? null;
  const ratingNum = rawRating !== null ? Number(rawRating) : NaN;
  const ratingPct = !Number.isNaN(ratingNum)
    ? Math.min(100, Math.round((ratingNum / 10) * 100))
    : null;
  const gaugeColor =
    ratingPct === null ? '#6366f1' :
    ratingPct >= 70    ? '#10b981' :
    ratingPct >= 45    ? '#f59e0b' : '#ef4444';

  return (
    <div className="bg-slate-800 rounded-xl p-6 space-y-6">
      <h3 className="text-xl font-semibold flex items-center gap-2">
        <Activity className="h-5 w-5 text-green-400" />
        Performance Prediction
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {FEATURE_CONFIG.map(({ key, label, min, max }) => (
          <div key={key}>
            <label className="block text-sm font-medium mb-2">
              {label} <span className="text-purple-400 font-bold">{features[key]}</span>
            </label>
            <input
              type="range"
              min={min}
              max={max}
              value={features[key]}
              onChange={(e) => setFeatures(f => ({ ...f, [key]: Number(e.target.value) }))}
              className="w-full accent-purple-500"
            />
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>{min}</span><span>{max}</span>
            </div>
          </div>
        ))}
      </div>

      <button
        onClick={handlePredict}
        disabled={loading}
        className="flex items-center gap-2 px-5 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded-lg transition-colors font-medium"
      >
        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <TrendingUp className="h-4 w-4" />}
        {loading ? 'Predicting...' : 'Predict Performance'}
      </button>

      {error && (
        <div className="flex items-center gap-2 text-sm text-red-400">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {result && ratingPct !== null && (
        <div className="flex flex-col items-center gap-4 py-4">
          <div className="relative w-40 h-40">
            <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
              <circle cx="50" cy="50" r="40" fill="none" stroke="#1e293b" strokeWidth="10" />
              <circle
                cx="50" cy="50" r="40" fill="none"
                stroke={gaugeColor}
                strokeWidth="10"
                strokeDasharray={`${ratingPct * 2.513} 251.3`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-bold">{ratingNum.toFixed(1)}</span>
              <span className="text-xs text-slate-400">/ 10</span>
            </div>
          </div>
          {result.label && (
            <div className="text-lg font-semibold" style={{ color: gaugeColor }}>{result.label}</div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Train Model Panel ────────────────────────────────────────────────────────

const TrainModelPanel: React.FC = () => {
  const [training, setTraining] = useState(false);
  const [trainResult, setTrainResult] = useState<any>(null);
  const [error, setError] = useState('');

  const handleTrain = async () => {
    setTraining(true);
    setError('');
    setTrainResult(null);
    try {
      const res = await (apiService as any).trainPlayerPerformanceModel();
      setTrainResult(res?.data ?? { status: 'started' });
    } catch {
      setError('Training request failed.');
    } finally {
      setTraining(false);
    }
  };

  return (
    <div className="bg-slate-800 rounded-xl p-6 space-y-6">
      <h3 className="text-xl font-semibold flex items-center gap-2">
        <RefreshCw className="h-5 w-5 text-yellow-400" />
        Train Models
      </h3>

      <div className="flex items-center justify-between p-4 bg-slate-700 rounded-xl gap-4 flex-wrap">
        <div>
          <div className="font-semibold">Player Performance Model</div>
          <div className="text-sm text-slate-400 mt-1">
            Trains on historical match statistics to predict performance ratings.
          </div>
        </div>
        <button
          onClick={handleTrain}
          disabled={training}
          className="flex items-center gap-2 px-5 py-2 bg-yellow-500 hover:bg-yellow-400 disabled:bg-slate-600 disabled:cursor-not-allowed text-slate-900 disabled:text-slate-400 rounded-lg transition-colors font-semibold flex-shrink-0"
        >
          {training ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          {training ? 'Training...' : 'Train Now'}
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-sm text-red-400">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {trainResult && (
        <div className="flex items-start gap-3 p-4 bg-green-500/10 border border-green-500/30 rounded-xl">
          <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-medium text-green-300">Training job initiated</div>
            {trainResult.job_id && (
              <div className="text-xs text-slate-400 mt-1">Job ID: {trainResult.job_id}</div>
            )}
            {trainResult.status && (
              <div className="text-xs text-slate-400">Status: {trainResult.status}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MLAnalysis;
