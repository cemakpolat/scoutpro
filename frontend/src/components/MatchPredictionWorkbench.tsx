import React, { useEffect, useMemo, useState } from 'react';
import { AlertCircle, Bookmark, Crosshair, History, Loader2, Sparkles, Target, Trash2 } from 'lucide-react';
import { useData } from '../context/DataContext';
import apiService from '../services/api';
import {
  deleteInteractivePredictionRun,
  getInteractivePredictionRuns,
  recordInteractivePredictionRun,
  toggleSavedInteractivePredictionRun,
  type InteractivePredictionRun,
} from '../utils/mlPredictionHistory';

type MatchPredictionFeatures = {
  home_xg: number;
  away_xg: number;
  home_shots: number;
  away_shots: number;
  home_shots_on_target: number;
  away_shots_on_target: number;
  home_possession: number;
  away_possession: number;
  home_pass_accuracy: number;
  away_pass_accuracy: number;
};

interface MatchPredictionWorkbenchProps {
  initialMatchId?: string;
}

const DEFAULT_FEATURES: MatchPredictionFeatures = {
  home_xg: 1.5,
  away_xg: 1.1,
  home_shots: 14,
  away_shots: 10,
  home_shots_on_target: 5,
  away_shots_on_target: 4,
  home_possession: 54,
  away_possession: 46,
  home_pass_accuracy: 84,
  away_pass_accuracy: 80,
};

function normalizeProbabilityValue(value: unknown): number | null {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) {
    return null;
  }

  if (numericValue > 1) {
    return Math.max(0, Math.min(1, numericValue / 100));
  }

  return Math.max(0, Math.min(1, numericValue));
}

function prettifyOutcomeLabel(value: string): string {
  const normalizedValue = String(value || '').trim();
  if (!normalizedValue) {
    return 'Unavailable';
  }

  const knownLabels: Record<string, string> = {
    home_win: 'Home Win',
    away_win: 'Away Win',
    draw: 'Draw',
    both_teams_to_score: 'Both Teams To Score',
    over_2_5_goals: 'Over 2.5 Goals',
  };

  if (knownLabels[normalizedValue]) {
    return knownLabels[normalizedValue];
  }

  return normalizedValue
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (segment) => segment.toUpperCase());
}

function buildPredictedOutcome(probabilities: Record<string, number>): string {
  const preferredKeys = ['home_win', 'draw', 'away_win'];
  const preferredEntries = preferredKeys
    .map((key) => [key, probabilities[key]] as const)
    .filter((entry) => typeof entry[1] === 'number');

  const entries = preferredEntries.length > 0 ? preferredEntries : Object.entries(probabilities);
  if (entries.length === 0) {
    return 'Unavailable';
  }

  const [bestKey] = entries.reduce((bestEntry, nextEntry) => {
    return nextEntry[1] > bestEntry[1] ? nextEntry : bestEntry;
  });

  return prettifyOutcomeLabel(bestKey);
}

function isPendingTrainingPrediction(payload: any): boolean {
  const message = `${payload?.error || ''} ${payload?.status || ''}`.toLowerCase();
  return message.includes('not trained')
    || message.includes('pending_training')
    || message.includes('not fitted');
}

function normalizeMatchPredictionResult(payload: any, source: 'ml' | 'statistics') {
  const rawProbabilities = payload?.probabilities && typeof payload.probabilities === 'object'
    ? payload.probabilities
    : {};
  const normalizedProbabilities = Object.entries(rawProbabilities).reduce<Record<string, number>>((accumulator, [key, value]) => {
    const normalizedValue = normalizeProbabilityValue(value);
    if (normalizedValue !== null) {
      accumulator[key] = normalizedValue;
    }
    return accumulator;
  }, {});

  const predictedOutcome = payload?.predicted_outcome
    ? prettifyOutcomeLabel(String(payload.predicted_outcome))
    : payload?.predicted_outcome_label
      ? prettifyOutcomeLabel(String(payload.predicted_outcome_label))
      : buildPredictedOutcome(normalizedProbabilities);

  return {
    ...payload,
    probabilities: normalizedProbabilities,
    predicted_outcome_label: predictedOutcome,
    prediction_source: source,
    fallback_used: source === 'statistics' || Boolean(payload?._simulated),
  };
}

function toNumericValue(value: unknown, fallback: number): number {
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : fallback;
}

function buildFeaturesFromMatch(match: any): MatchPredictionFeatures {
  return {
    home_xg: toNumericValue(match?.homeXG ?? match?.home_xg, DEFAULT_FEATURES.home_xg),
    away_xg: toNumericValue(match?.awayXG ?? match?.away_xg, DEFAULT_FEATURES.away_xg),
    home_shots: toNumericValue(match?.homeShots ?? match?.home_shots, DEFAULT_FEATURES.home_shots),
    away_shots: toNumericValue(match?.awayShots ?? match?.away_shots, DEFAULT_FEATURES.away_shots),
    home_shots_on_target: toNumericValue(match?.homeShotsOnTarget ?? match?.home_shots_on_target, DEFAULT_FEATURES.home_shots_on_target),
    away_shots_on_target: toNumericValue(match?.awayShotsOnTarget ?? match?.away_shots_on_target, DEFAULT_FEATURES.away_shots_on_target),
    home_possession: toNumericValue(match?.homePossession ?? match?.home_possession, DEFAULT_FEATURES.home_possession),
    away_possession: toNumericValue(match?.awayPossession ?? match?.away_possession, DEFAULT_FEATURES.away_possession),
    home_pass_accuracy: toNumericValue(match?.homePassAccuracy ?? match?.home_pass_accuracy, DEFAULT_FEATURES.home_pass_accuracy),
    away_pass_accuracy: toNumericValue(match?.awayPassAccuracy ?? match?.away_pass_accuracy, DEFAULT_FEATURES.away_pass_accuracy),
  };
}

const FEATURE_FIELDS: Array<{ key: keyof MatchPredictionFeatures; label: string; step?: number }> = [
  { key: 'home_xg', label: 'Home xG', step: 0.01 },
  { key: 'away_xg', label: 'Away xG', step: 0.01 },
  { key: 'home_shots', label: 'Home Shots', step: 1 },
  { key: 'away_shots', label: 'Away Shots', step: 1 },
  { key: 'home_shots_on_target', label: 'Home Shots On Target', step: 1 },
  { key: 'away_shots_on_target', label: 'Away Shots On Target', step: 1 },
  { key: 'home_possession', label: 'Home Possession %', step: 1 },
  { key: 'away_possession', label: 'Away Possession %', step: 1 },
  { key: 'home_pass_accuracy', label: 'Home Pass Accuracy %', step: 0.1 },
  { key: 'away_pass_accuracy', label: 'Away Pass Accuracy %', step: 0.1 },
];

const MatchPredictionWorkbench: React.FC<MatchPredictionWorkbenchProps> = ({ initialMatchId }) => {
  const { matches } = useData();
  const [selectedMatchId, setSelectedMatchId] = useState('');
  const [features, setFeatures] = useState<MatchPredictionFeatures>(DEFAULT_FEATURES);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [predictionHistory, setPredictionHistory] = useState<InteractivePredictionRun[]>(() => getInteractivePredictionRuns('match-outcome'));
  const [activeHistoryId, setActiveHistoryId] = useState<string | null>(null);

  const availableMatches = useMemo(
    () => (matches || []).filter((match: any) => Boolean(match?.id)).slice(0, 200),
    [matches],
  );

  useEffect(() => {
    if (availableMatches.length === 0) {
      return;
    }

    if (initialMatchId && availableMatches.some((match: any) => String(match.id) === String(initialMatchId))) {
      setSelectedMatchId(String(initialMatchId));
      return;
    }

    if (!selectedMatchId) {
      setSelectedMatchId(String(availableMatches[0].id));
    }
  }, [availableMatches, initialMatchId, selectedMatchId]);

  useEffect(() => {
    const selectedMatch = availableMatches.find((match: any) => String(match.id) === String(selectedMatchId));
    if (selectedMatch) {
      setFeatures(buildFeaturesFromMatch(selectedMatch));
      setResult(null);
      setError(null);
    }
  }, [availableMatches, selectedMatchId]);

  const selectedMatch = availableMatches.find((match: any) => String(match.id) === String(selectedMatchId));
  const matchLabel = selectedMatch
    ? `${selectedMatch.homeTeam || selectedMatch.home_team || 'Home'} vs ${selectedMatch.awayTeam || selectedMatch.away_team || 'Away'}`
    : 'Custom scenario';

  const probabilityEntries = useMemo(() => {
    const probabilities = result?.probabilities;
    if (!probabilities || typeof probabilities !== 'object') {
      return [];
    }

    return Object.entries(probabilities)
      .map(([key, value]) => ({
        label: key,
        value: Number(value),
      }))
      .filter((entry) => Number.isFinite(entry.value))
      .sort((left, right) => right.value - left.value);
  }, [result]);

  const activeHistoryRun = useMemo(
    () => predictionHistory.find((entry) => entry.id === activeHistoryId) || null,
    [activeHistoryId, predictionHistory],
  );

  const formatHistoryTimestamp = (value: string) => new Date(value).toLocaleString();

  const handlePredict = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await apiService.predictMatchOutcome(features);
      if (!response.success) {
        throw new Error(response.error.message);
      }

      let nextResult = response.data;
      if (isPendingTrainingPrediction(nextResult)) {
        if (!selectedMatchId) {
          throw new Error('The match model is not trained yet and no match is selected for a statistics fallback.');
        }

        const fallbackResponse = await apiService.getMatchPrediction(selectedMatchId);
        if (!fallbackResponse.success) {
          throw new Error(nextResult?.error || fallbackResponse.error.message);
        }

        nextResult = normalizeMatchPredictionResult(fallbackResponse.data, 'statistics');
      } else {
        if (nextResult?.error) {
          throw new Error(nextResult.error);
        }

        nextResult = normalizeMatchPredictionResult(nextResult, 'ml');
      }

      setResult(nextResult);
      const recordedRun = recordInteractivePredictionRun({
        type: 'match-outcome',
        title: matchLabel,
        summary: `${nextResult.predicted_outcome || nextResult.predicted_outcome_label || 'Outcome unavailable'}`,
        input: features,
        result: nextResult,
        context: selectedMatchId ? { matchId: selectedMatchId } : undefined,
      });
      setActiveHistoryId(recordedRun.id);
      setPredictionHistory(getInteractivePredictionRuns('match-outcome'));
    } catch (predictionError) {
      setError(predictionError instanceof Error ? predictionError.message : 'Prediction failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRestoreRun = (run: InteractivePredictionRun) => {
    setActiveHistoryId(run.id);
    setError(null);
    setResult(normalizeMatchPredictionResult(
      run.result,
      run.result?.prediction_source === 'statistics' || run.result?.fallback_used ? 'statistics' : 'ml',
    ));
    setFeatures(run.input as MatchPredictionFeatures);
    if (run.context?.matchId) {
      setSelectedMatchId(run.context.matchId);
    }
  };

  const handleToggleSavedRun = (runId: string) => {
    setPredictionHistory(toggleSavedInteractivePredictionRun(runId).filter((entry) => entry.type === 'match-outcome'));
  };

  const handleDeleteRun = (runId: string) => {
    setPredictionHistory(deleteInteractivePredictionRun(runId).filter((entry) => entry.type === 'match-outcome'));
    if (activeHistoryId === runId) {
      setActiveHistoryId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 rounded-xl border border-slate-700 bg-slate-800 p-5 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Match Prediction</h2>
          <p className="mt-1 text-sm text-slate-400">
            Build a scenario from a real match baseline or edit the numbers manually, then send that feature set to the live match outcome predictor.
          </p>
        </div>
        <div className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs text-slate-400">
          Scenario: {matchLabel}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.25fr,0.75fr]">
        <div className="rounded-xl border border-slate-700 bg-slate-800 p-6">
          <div className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="text-sm font-medium text-slate-300">Load baseline from tracked match</div>
              <div className="mt-1 text-xs text-slate-500">Selecting a match populates the form from the current match read model.</div>
            </div>
            <select
              value={selectedMatchId}
              onChange={(event) => setSelectedMatchId(event.target.value)}
              className="rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-white focus:border-cyan-400 focus:outline-none"
            >
              {availableMatches.map((match: any) => (
                <option key={String(match.id)} value={String(match.id)}>
                  {(match.homeTeam || match.home_team || 'Home')} vs {(match.awayTeam || match.away_team || 'Away')}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {FEATURE_FIELDS.map((field) => (
              <label key={field.key} className="block rounded-lg border border-slate-700 bg-slate-900/70 p-4">
                <div className="text-xs uppercase tracking-wide text-slate-500">{field.label}</div>
                <input
                  type="number"
                  step={field.step ?? 1}
                  value={features[field.key]}
                  onChange={(event) => setFeatures((current) => ({
                    ...current,
                    [field.key]: Number(event.target.value),
                  }))}
                  className="mt-2 w-full bg-transparent text-xl font-semibold text-white outline-none"
                />
              </label>
            ))}
          </div>

          <button
            onClick={handlePredict}
            disabled={loading}
            className="mt-5 inline-flex items-center gap-2 rounded-lg bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 transition-colors hover:bg-cyan-400 disabled:bg-slate-600 disabled:text-slate-300"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {loading ? 'Predicting...' : 'Predict Match Outcome'}
          </button>
        </div>

        <div className="space-y-6">
          <div className="rounded-xl border border-slate-700 bg-slate-800 p-6">
            <div className="flex items-center gap-2 text-lg font-semibold text-white">
              <Target className="h-5 w-5 text-green-400" />
              Prediction Result
            </div>

            {error && (
              <div className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                <div className="flex items-start gap-2">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>{error}</span>
                </div>
              </div>
            )}

            {!error && result && (
              <div className="mt-4 space-y-4">
                <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
                  <div className="text-xs uppercase tracking-wide text-slate-500">Predicted Outcome</div>
                  <div className="mt-2 text-2xl font-bold text-white">{result.predicted_outcome_label || result.predicted_outcome || 'Unavailable'}</div>
                  <div className="mt-1 text-xs text-slate-400">
                    {result.prediction_source === 'statistics'
                      ? 'Statistics projection fallback'
                      : result._simulated
                        ? 'Scenario fallback estimate'
                        : 'Direct ML model prediction'}
                  </div>
                  {result._simulated && (
                    <div className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-100">
                      The trained match model is not available yet, so this scenario is using a fallback estimate derived from the form values above.
                    </div>
                  )}
                  {activeHistoryRun && (
                    <button
                      onClick={() => handleToggleSavedRun(activeHistoryRun.id)}
                      className={`mt-3 inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-medium transition-colors ${
                        activeHistoryRun.saved
                          ? 'border-amber-500/40 bg-amber-500/10 text-amber-200'
                          : 'border-slate-600 bg-slate-800 text-slate-300 hover:border-cyan-400 hover:text-white'
                      }`}
                    >
                      <Bookmark className="h-3.5 w-3.5" />
                      {activeHistoryRun.saved ? 'Saved Run' : 'Save This Run'}
                    </button>
                  )}
                </div>

                {probabilityEntries.length > 0 && (
                  <div className="space-y-3">
                    {probabilityEntries.map((entry) => (
                      <div key={entry.label} className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-300">{prettifyOutcomeLabel(entry.label)}</span>
                          <span className="font-semibold text-white">{(entry.value * 100).toFixed(1)}%</span>
                        </div>
                        <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-700">
                          <div className="h-full rounded-full bg-cyan-400" style={{ width: `${Math.max(0, Math.min(100, entry.value * 100))}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {result.expected_goals && (
                  <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
                    <div className="text-xs uppercase tracking-wide text-slate-500">Expected Goals Snapshot</div>
                    <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <div className="text-slate-400">Home</div>
                        <div className="mt-1 text-lg font-semibold text-white">{toNumericValue(result.expected_goals.home, 0).toFixed(2)}</div>
                      </div>
                      <div>
                        <div className="text-slate-400">Away</div>
                        <div className="mt-1 text-lg font-semibold text-white">{toNumericValue(result.expected_goals.away, 0).toFixed(2)}</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {!error && !result && (
              <div className="mt-4 rounded-lg border border-slate-700 bg-slate-900/70 px-4 py-6 text-sm text-slate-400">
                Run the scenario to view the current model outcome probabilities.
              </div>
            )}
          </div>

          <div className="rounded-xl border border-slate-700 bg-slate-800 p-6">
            <div className="flex items-center gap-2 text-lg font-semibold text-white">
              <Crosshair className="h-5 w-5 text-yellow-400" />
              Scenario Notes
            </div>
            <div className="mt-4 space-y-3 text-sm text-slate-400">
              <p>This first version uses tracked match metrics as a baseline and lets you edit them manually for scenario planning.</p>
              <p>If the backend model is not trained yet, this panel will surface the live error rather than hiding it.</p>
            </div>
          </div>

          <div className="rounded-xl border border-slate-700 bg-slate-800 p-6">
            <div className="flex items-center gap-2 text-lg font-semibold text-white">
              <History className="h-5 w-5 text-cyan-400" />
              Prediction History
            </div>
            <div className="mt-2 text-sm text-slate-400">
              Recent interactive runs are stored locally so you can reopen or pin useful scenarios.
            </div>

            <div className="mt-4 space-y-3">
              {predictionHistory.length === 0 && (
                <div className="rounded-lg border border-slate-700 bg-slate-900/70 px-4 py-5 text-sm text-slate-400">
                  No prediction runs have been saved yet from this browser.
                </div>
              )}

              {predictionHistory.slice(0, 6).map((run) => (
                <div key={run.id} className={`rounded-lg border p-4 ${activeHistoryId === run.id ? 'border-cyan-500/40 bg-cyan-500/10' : 'border-slate-700 bg-slate-900/70'}`}>
                  <div className="flex items-start justify-between gap-3">
                    <button onClick={() => handleRestoreRun(run)} className="text-left">
                      <div className="font-medium text-white">{run.title}</div>
                      <div className="mt-1 text-xs text-slate-400">{run.summary}</div>
                      <div className="mt-2 text-[11px] text-slate-500">{formatHistoryTimestamp(run.createdAt)}</div>
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
      </div>
    </div>
  );
};

export default MatchPredictionWorkbench;