import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertCircle, Brain, Loader2, Orbit, Sparkles, Users } from 'lucide-react';
import { useData } from '../context/DataContext';
import { useApi } from '../hooks/useApi';
import apiService from '../services/api';
import type { Player } from '../types';

interface ClusteringExplorerProps {
  initialPlayerId?: string;
}

function toNumber(value: unknown, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function buildClusterFeaturePayload(player: Player, statsPayload: any) {
  const stats = statsPayload?.stats || statsPayload || {};
  const matchesPlayed = Math.max(
    1,
    toNumber(stats.matches_played, toNumber(player.appearances, 0)),
  );

  return {
    aerial_win_rate: toNumber(stats.aerial_duel_success_rate, 0),
    assists_per_90: toNumber(stats.assists_per_90, toNumber(player.assists, 0) / matchesPlayed),
    duel_win_rate: toNumber(stats.duel_success_rate, 0),
    foul_rate: toNumber(stats.foul_rate, 0),
    goals_per_90: toNumber(stats.goals_per_90, toNumber(player.goals, 0) / matchesPlayed),
    interception_rate: toNumber(stats.interception_rate, 0),
    key_passes_per_90: toNumber(stats.key_passes_per_90, 0),
    matches_played: matchesPlayed,
    pass_accuracy: toNumber(stats.pass_accuracy, toNumber(player.passAccuracy, 0)),
    pressures_applied: toNumber(stats.pressures_applied, 0),
    save_rate: toNumber(stats.save_rate, 0),
    shot_accuracy: toNumber(stats.shot_accuracy, 0),
    shot_conversion: toNumber(stats.shot_conversion || stats.conversion_rate, 0),
    tackle_success_rate: toNumber(stats.tackle_success_rate, 0),
    take_on_success_rate: toNumber(stats.take_on_success_rate, toNumber(player.dribbleSuccess, 0)),
  };
}

function prettifyFeatureName(value: string): string {
  return value
    .split('_')
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ');
}

function formatClusterFeatureValue(key: string, value: number): string {
  const isRate = key.includes('rate') || key.includes('accuracy') || key.includes('win_rate') || key.includes('conversion');
  if (isRate) {
    return `${value.toFixed(1)}%`;
  }

  return value.toFixed(2);
}

const ClusteringExplorer: React.FC<ClusteringExplorerProps> = ({ initialPlayerId }) => {
  const { players } = useData();
  const {
    data: tasks,
    loading: tasksLoading,
    error: tasksError,
  } = useApi(() => apiService.listTasks(50), []);

  const [selectedPlayerId, setSelectedPlayerId] = useState('');
  const [predictionLoading, setPredictionLoading] = useState(false);
  const [predictionError, setPredictionError] = useState<string | null>(null);
  const [clusterPrediction, setClusterPrediction] = useState<any>(null);
  const [derivedFeatures, setDerivedFeatures] = useState<Record<string, number> | null>(null);
  const [autoRequested, setAutoRequested] = useState(false);

  const availablePlayers = players || [];
  const latestClusteringTask = useMemo(() => {
    return (tasks || []).find((task: any) => task.status === 'completed' && task.result?.algorithm === 'player_clustering') || null;
  }, [tasks]);
  const clusterDistribution = latestClusteringTask?.result?.cluster_distribution || {};
  const clusterArchetypes = latestClusteringTask?.result?.cluster_archetypes || {};
  const maxClusterCount = Math.max(...Object.values(clusterDistribution).map((value) => Number(value) || 0), 1);
  const featureHighlights = useMemo(() => {
    if (!derivedFeatures) {
      return [];
    }

    return Object.entries(derivedFeatures)
      .filter(([, value]) => Number.isFinite(value) && value !== 0)
      .sort((left, right) => Math.abs(right[1]) - Math.abs(left[1]))
      .slice(0, 6);
  }, [derivedFeatures]);

  useEffect(() => {
    if (availablePlayers.length === 0) {
      return;
    }

    if (initialPlayerId && availablePlayers.some((player) => String(player.id) === String(initialPlayerId))) {
      setSelectedPlayerId(String(initialPlayerId));
      return;
    }

    if (!selectedPlayerId) {
      setSelectedPlayerId(String(availablePlayers[0].id));
    }
  }, [availablePlayers, initialPlayerId, selectedPlayerId]);

  const selectedPlayer = availablePlayers.find((player) => String(player.id) === String(selectedPlayerId)) || null;

  const handleAssignCluster = useCallback(async (playerId: string) => {
    const player = availablePlayers.find((entry) => String(entry.id) === String(playerId));
    if (!player) {
      return;
    }

    setPredictionLoading(true);
    setPredictionError(null);
    setClusterPrediction(null);

    try {
      const statsResponse = await apiService.getPlayerStatistics(playerId);
      if (!statsResponse.success) {
        throw new Error(statsResponse.error.message);
      }

      const nextFeatures = buildClusterFeaturePayload(player, statsResponse.data);
      setDerivedFeatures(nextFeatures);

      const predictionResponse = await apiService.predictPlayerCluster(nextFeatures);
      if (!predictionResponse.success) {
        throw new Error(predictionResponse.error.message);
      }

      const payload = predictionResponse.data?.prediction ?? predictionResponse.data;
      if (payload?.error) {
        throw new Error(payload.error);
      }

      setClusterPrediction(payload);
    } catch (clusterError) {
      setPredictionError(clusterError instanceof Error ? clusterError.message : 'Cluster assignment failed');
    } finally {
      setPredictionLoading(false);
    }
  }, [availablePlayers]);

  useEffect(() => {
    if (!initialPlayerId || autoRequested || String(selectedPlayerId) !== String(initialPlayerId)) {
      return;
    }

    setAutoRequested(true);
    void handleAssignCluster(String(initialPlayerId));
  }, [autoRequested, handleAssignCluster, initialPlayerId, selectedPlayerId]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 rounded-xl border border-slate-700 bg-slate-800 p-5 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Clustering Explorer</h2>
          <p className="mt-1 text-sm text-slate-400">
            Inspect the latest trained player clustering output, then assign an individual player to a live archetype using the current cluster model.
          </p>
        </div>
        <div className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs text-slate-400">
          {latestClusteringTask ? 'Latest clustering run loaded' : 'Waiting for a clustering training result'}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.1fr,0.9fr]">
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-700 bg-slate-800 p-6">
            <div className="flex items-center gap-2 text-lg font-semibold text-white">
              <Orbit className="h-5 w-5 text-cyan-400" />
              Latest Cluster Training Snapshot
            </div>

            {tasksLoading && !latestClusteringTask ? (
              <div className="mt-4 flex items-center text-sm text-slate-400">
                <Loader2 className="mr-2 h-4 w-4 animate-spin text-cyan-400" />
                Loading clustering metadata...
              </div>
            ) : latestClusteringTask?.result ? (
              <div className="mt-4 space-y-5">
                <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
                  <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
                    <div className="text-xs uppercase tracking-wide text-slate-500">Clusters</div>
                    <div className="mt-2 text-2xl font-bold text-white">{latestClusteringTask.result.n_clusters ?? '—'}</div>
                  </div>
                  <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
                    <div className="text-xs uppercase tracking-wide text-slate-500">Samples</div>
                    <div className="mt-2 text-2xl font-bold text-white">{latestClusteringTask.result.n_samples ?? '—'}</div>
                  </div>
                  <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
                    <div className="text-xs uppercase tracking-wide text-slate-500">Inertia</div>
                    <div className="mt-2 text-2xl font-bold text-white">{latestClusteringTask.result.inertia ?? '—'}</div>
                  </div>
                  <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
                    <div className="text-xs uppercase tracking-wide text-slate-500">Silhouette</div>
                    <div className="mt-2 text-2xl font-bold text-white">{latestClusteringTask.result.silhouette_score ?? '—'}</div>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  {Object.entries(clusterArchetypes).map(([clusterId, label]) => {
                    const count = Number((clusterDistribution as Record<string, unknown>)[clusterId] || 0);
                    const widthPercent = Math.max(8, Math.min(100, (count / maxClusterCount) * 100));
                    return (
                      <div key={clusterId} className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <div className="text-xs uppercase tracking-wide text-slate-500">Cluster {clusterId}</div>
                            <div className="mt-1 text-lg font-semibold text-white">{String(label)}</div>
                          </div>
                          <div className="text-right">
                            <div className="text-lg font-bold text-cyan-300">{count}</div>
                            <div className="text-xs text-slate-500">players</div>
                          </div>
                        </div>
                        <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-700">
                          <div className="h-full rounded-full bg-cyan-400" style={{ width: `${widthPercent}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="mt-4 rounded-lg border border-slate-700 bg-slate-900/70 px-4 py-6 text-sm text-slate-400">
                {tasksError || 'No completed player clustering task is available yet. Train Player Clustering in ML Laboratory or Batch Tasks first.'}
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-xl border border-slate-700 bg-slate-800 p-6">
            <div className="flex items-center gap-2 text-lg font-semibold text-white">
              <Users className="h-5 w-5 text-yellow-400" />
              Assign A Player To A Cluster
            </div>
            <div className="mt-2 text-sm text-slate-400">
              Select a player, derive their cluster feature payload from live player statistics, then request a live cluster assignment.
            </div>

            <div className="mt-4 space-y-4">
              <select
                value={selectedPlayerId}
                onChange={(event) => {
                  setSelectedPlayerId(event.target.value);
                  setPredictionError(null);
                  setClusterPrediction(null);
                }}
                className="w-full rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-white focus:border-cyan-400 focus:outline-none"
              >
                {availablePlayers.map((player) => (
                  <option key={player.id} value={player.id}>{player.name}</option>
                ))}
              </select>

              <button
                onClick={() => selectedPlayerId && void handleAssignCluster(selectedPlayerId)}
                disabled={!selectedPlayerId || predictionLoading}
                className="inline-flex items-center gap-2 rounded-lg bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 transition-colors hover:bg-cyan-400 disabled:bg-slate-600 disabled:text-slate-300"
              >
                {predictionLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                {predictionLoading ? 'Assigning...' : 'Assign Cluster'}
              </button>
            </div>

            {selectedPlayer && (
              <div className="mt-5 rounded-lg border border-slate-700 bg-slate-900/70 p-4 text-sm text-slate-300">
                <div className="text-lg font-semibold text-white">{selectedPlayer.name}</div>
                <div className="mt-1 text-slate-400">{selectedPlayer.position} • {selectedPlayer.club}</div>
              </div>
            )}

            {predictionError && (
              <div className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                <div className="flex items-start gap-2">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>{predictionError}</span>
                </div>
              </div>
            )}

            {clusterPrediction && (
              <div className="mt-4 space-y-3">
                <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
                  <div className="text-xs uppercase tracking-wide text-slate-500">Assigned Cluster</div>
                  <div className="mt-2 text-2xl font-bold text-white">{clusterPrediction.archetype || `Cluster ${clusterPrediction.cluster_id}`}</div>
                  <div className="mt-1 text-sm text-slate-400">Cluster ID: {clusterPrediction.cluster_id ?? '—'}</div>
                </div>

                <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4 text-sm text-slate-300">
                  This assignment is currently an archetype label only. The live model does not return confidence or nearest-neighbour explanations yet, so the best explanation available in the UI is the feature mix used for the assignment below.
                </div>

                {featureHighlights.length > 0 && (
                  <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
                    <div className="flex items-center gap-2 text-sm font-semibold text-white">
                      <Sparkles className="h-4 w-4 text-cyan-400" />
                      Main Signals Used In This Assignment
                    </div>
                    <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
                      {featureHighlights.map(([key, value]) => (
                        <div key={key} className="rounded-lg border border-slate-700 bg-slate-800/70 p-3">
                          <div className="text-xs uppercase tracking-wide text-slate-500">{prettifyFeatureName(key)}</div>
                          <div className="mt-1 text-lg font-semibold text-white">{formatClusterFeatureValue(key, value)}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {derivedFeatures && (
                  <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
                    <div className="flex items-center gap-2 text-sm font-semibold text-white">
                      <Brain className="h-4 w-4 text-cyan-400" />
                      Derived Feature Payload
                    </div>
                    <div className="mt-2 text-xs text-slate-500">
                      These are the exact numeric inputs sent to the current clustering model for this player.
                    </div>
                    <pre className="mt-3 overflow-x-auto text-xs text-slate-300">{JSON.stringify(derivedFeatures, null, 2)}</pre>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClusteringExplorer;