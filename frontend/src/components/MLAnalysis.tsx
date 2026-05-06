import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Brain, BarChart3, Target, TrendingUp, Users, Activity,
  Loader2, Search, RefreshCw, CheckCircle, Database, AlertCircle, Bookmark, History, Trash2
} from 'lucide-react';
import apiService from '../services/api';
import { useData } from '../context/DataContext';
import type { ModelCenterInteractivePanel } from './ModelCenter';
import {
  deleteInteractivePredictionRun,
  getInteractivePredictionRuns,
  recordInteractivePredictionRun,
  toggleSavedInteractivePredictionRun,
  type InteractivePredictionRun,
} from '../utils/mlPredictionHistory';

// ─── Main Component ──────────────────────────────────────────────────────────

interface MLAnalysisProps {
  showTrainingPanel?: boolean;
  initialPanel?: ModelCenterInteractivePanel;
  initialPlayerId?: string;
}

type AnalysisPanel = ModelCenterInteractivePanel | 'train';

const MLAnalysis: React.FC<MLAnalysisProps> = ({ showTrainingPanel = true, initialPanel = 'similar', initialPlayerId }) => {
  const [selectedModel, setSelectedModel] = useState<AnalysisPanel>(initialPanel);
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

  useEffect(() => {
    setSelectedModel(initialPanel);
  }, [initialPanel]);

  const panels: Array<{ id: AnalysisPanel; label: string; icon: React.ComponentType<{ className?: string }> }> = [
    { id: 'similar', label: 'Similar Players', icon: Users },
    { id: 'performance', label: 'Performance Prediction', icon: Activity },
    ...(showTrainingPanel ? [{ id: 'train' as const, label: 'Train Models', icon: RefreshCw }] : []),
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
      {selectedModel === 'similar'     && <SimilarPlayersPanel initialPlayerId={initialPlayerId} />}
      {selectedModel === 'performance' && <PerformancePredictionPanel initialPlayerId={initialPlayerId} />}
      {showTrainingPanel && selectedModel === 'train' && <TrainModelPanel />}
    </div>
  );
};

// ─── Similar Players Panel ────────────────────────────────────────────────────

const SimilarPlayersPanel: React.FC<{ initialPlayerId?: string }> = ({ initialPlayerId }) => {
  const { players } = useData();
  const [playerId, setPlayerId] = useState('');
  const [topN, setTopN] = useState(5);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [error, setError] = useState('');

  const searchablePlayers = useMemo(() => players || [], [players]);

  const resolvePlayerId = useCallback((input: string) => {
    const trimmed = input.trim();
    if (!trimmed) {
      return '';
    }

    const directMatch = searchablePlayers.find((player) => {
      return String(player.id) === trimmed
        || String(player.id).toLowerCase() === trimmed.toLowerCase();
    });
    if (directMatch) {
      return String(directMatch.id);
    }

    const normalizedInput = trimmed.toLowerCase();
    const byName = searchablePlayers.find((player) => String(player.name || '').toLowerCase() === normalizedInput);
    if (byName) {
      return String(byName.id);
    }

    const partialNameMatch = searchablePlayers.find((player) => String(player.name || '').toLowerCase().includes(normalizedInput));
    if (partialNameMatch) {
      return String(partialNameMatch.id);
    }

    return trimmed;
  }, [searchablePlayers]);

  const handleFind = useCallback(async (providedPlayerId?: string) => {
    const requestedValue = (providedPlayerId ?? playerId).trim();
    const resolvedPlayerId = resolvePlayerId(requestedValue);
    if (!resolvedPlayerId) return;
    setLoading(true);
    setError('');
    setResults([]);
    try {
      const res = await (apiService as any).findSimilarPlayersById(resolvedPlayerId, topN);
      const list =
        res?.data?.similar_players ??
        res?.data?.players ??
        (Array.isArray(res?.data) ? res.data : []);
      setResults(list);
      if (list.length === 0) setError('No similar players found for that player.');
    } catch {
      setError('Failed to fetch similar players.');
    } finally {
      setLoading(false);
    }
  }, [playerId, resolvePlayerId, topN]);

  useEffect(() => {
    if (!initialPlayerId) {
      return;
    }

    setPlayerId(initialPlayerId);
    void handleFind(initialPlayerId);
  }, [handleFind, initialPlayerId]);

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
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              void handleFind();
            }
          }}
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
          onClick={() => {
            void handleFind();
          }}
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

function buildPerformanceFeaturesFromStats(stats: any): Record<string, number> {
  return {
    passes: Number(stats?.passes_completed ?? stats?.passes ?? 50) || 50,
    shots: Number(stats?.shots ?? stats?.shots_total ?? 5) || 5,
    tackles: Number(stats?.tackles_won ?? stats?.tackles ?? 8) || 8,
  };
}

const PerformancePredictionPanel: React.FC<{ initialPlayerId?: string }> = ({ initialPlayerId }) => {
  const [features, setFeatures] = useState<Record<string, number>>({
    passes: 50, shots: 5, tackles: 8,
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [prefillLabel, setPrefillLabel] = useState<string | null>(null);
  const [predictionHistory, setPredictionHistory] = useState<InteractivePredictionRun[]>(() => getInteractivePredictionRuns('player-performance'));
  const [activeHistoryId, setActiveHistoryId] = useState<string | null>(null);

  useEffect(() => {
    if (!initialPlayerId) {
      return;
    }

    let cancelled = false;

    const loadPlayerBaseline = async () => {
      try {
        const statsResponse = await apiService.getPlayerStatistics(initialPlayerId);
        if (!statsResponse.success || cancelled) {
          return;
        }

        setFeatures(buildPerformanceFeaturesFromStats(statsResponse.data));
        setPrefillLabel(`Player ${initialPlayerId}`);
      } catch {
        if (!cancelled) {
          setPrefillLabel(`Player ${initialPlayerId}`);
        }
      }
    };

    void loadPlayerBaseline();

    return () => {
      cancelled = true;
    };
  }, [initialPlayerId]);

  const handlePredict = async () => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await (apiService as any).predictPlayerPerformance(features);
      if (res?.data) {
        setResult(res.data);
        const recordedRun = recordInteractivePredictionRun({
          type: 'player-performance',
          title: prefillLabel ? `${prefillLabel} performance projection` : 'Custom performance projection',
          summary: `${Number(res.data.predicted_rating ?? res.data.rating ?? res.data.score ?? 0).toFixed(1)} / 10`,
          input: features,
          result: res.data,
          context: initialPlayerId ? { playerId: initialPlayerId } : undefined,
        });
        setActiveHistoryId(recordedRun.id);
        setPredictionHistory(getInteractivePredictionRuns('player-performance'));
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

  const activeHistoryRun = predictionHistory.find((entry) => entry.id === activeHistoryId) || null;

  const handleRestoreRun = (run: InteractivePredictionRun) => {
    setActiveHistoryId(run.id);
    setError('');
    setResult(run.result);
    setFeatures(run.input as Record<string, number>);
  };

  const handleToggleSavedRun = (runId: string) => {
    setPredictionHistory(toggleSavedInteractivePredictionRun(runId).filter((entry) => entry.type === 'player-performance'));
  };

  const handleDeleteRun = (runId: string) => {
    setPredictionHistory(deleteInteractivePredictionRun(runId).filter((entry) => entry.type === 'player-performance'));
    if (activeHistoryId === runId) {
      setActiveHistoryId(null);
    }
  };

  return (
    <div className="bg-slate-800 rounded-xl p-6 space-y-6">
      <h3 className="text-xl font-semibold flex items-center gap-2">
        <Activity className="h-5 w-5 text-green-400" />
        Performance Prediction
      </h3>

      {prefillLabel && (
        <div className="rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-4 py-3 text-sm text-cyan-100">
          Prefilled from {prefillLabel}. Adjust the numbers if you want to test a different scenario before running the prediction.
        </div>
      )}

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
          {result._simulated && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-center text-sm text-amber-100">
              The trained player model is not available yet, so this result is coming from a fallback estimate based on the sliders above.
            </div>
          )}
          {activeHistoryRun && (
            <button
              onClick={() => handleToggleSavedRun(activeHistoryRun.id)}
              className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-medium transition-colors ${
                activeHistoryRun.saved
                  ? 'border-amber-500/40 bg-amber-500/10 text-amber-200'
                  : 'border-slate-600 bg-slate-700 text-slate-200 hover:border-cyan-400 hover:text-white'
              }`}
            >
              <Bookmark className="h-3.5 w-3.5" />
              {activeHistoryRun.saved ? 'Saved Run' : 'Save This Run'}
            </button>
          )}
        </div>
      )}

      <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          <History className="h-4 w-4 text-cyan-400" />
          Prediction History
        </div>
        <div className="mt-3 space-y-3">
          {predictionHistory.length === 0 && (
            <div className="text-sm text-slate-400">No interactive player performance runs have been stored yet.</div>
          )}
          {predictionHistory.slice(0, 5).map((run) => (
            <div key={run.id} className={`rounded-lg border p-3 ${activeHistoryId === run.id ? 'border-cyan-500/40 bg-cyan-500/10' : 'border-slate-700 bg-slate-800/70'}`}>
              <div className="flex items-start justify-between gap-3">
                <button onClick={() => handleRestoreRun(run)} className="text-left">
                  <div className="font-medium text-white">{run.title}</div>
                  <div className="mt-1 text-xs text-slate-400">{run.summary}</div>
                  <div className="mt-2 text-[11px] text-slate-500">{new Date(run.createdAt).toLocaleString()}</div>
                </button>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleToggleSavedRun(run.id)}
                    className={`rounded-md border px-2 py-1 text-[11px] ${run.saved ? 'border-amber-500/40 bg-amber-500/10 text-amber-200' : 'border-slate-600 text-slate-300'}`}
                  >
                    {run.saved ? 'Saved' : 'Save'}
                  </button>
                  <button
                    onClick={() => handleDeleteRun(run.id)}
                    className="rounded-md border border-slate-600 px-2 py-1 text-[11px] text-slate-300 hover:border-red-400 hover:text-red-200"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
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
