import React, { useEffect, useState } from 'react';
import { ArrowLeft, MapPin, Calendar, DollarSign, TrendingUp, Activity, Shield, Target, Zap, Users, Loader2, Download } from 'lucide-react';
import apiService from '../services/api';
import { deriveAge } from '../utils/dataTransformers';

interface Player {
  id: string | number;
  provider_ids?: {
    opta?: string;
  };
  providerIds?: {
    opta?: string;
  };
  opta_uid?: string;
  name: string;
  position: string;
  team?: string;
  team_name?: string;
  club?: string;
  age?: number | null;
  nationality: string;
  marketValue?: string;
  goals?: number;
  assists?: number;
  rating?: number | null;
  overallRating?: number | null;
  matches?: number;
  appearances?: number;
  image?: string;
  photo?: string;
  passAccuracy?: number;
  xG?: number;
  xA?: number;
  height?: string | number;
  weight?: string | number;
  preferred_foot?: string;
  preferredFoot?: string;
  birth_date?: string;
  birthDate?: string;
  detailed_position?: string;
  detailedPosition?: string;
  shirt_number?: number;
  shirtNumber?: number;
}

interface PlayerDetailProps {
  player: Player;
  onBack: () => void;
}

interface CompositeIndexData {
  totalIndex: number;
  attacking: number;
  possession: number;
  defending: number;
}

interface InsightItem {
  title?: string;
  impact?: string;
  description?: string;
}

interface PlayerInsightsData {
  insights: InsightItem[];
}

interface ExpectedMetricsData {
  xg: number;
  xa: number;
  shotsWithXg: number;
  passesWithXa: number;
}

interface HeatmapCell {
  gridX: number;
  gridY: number;
  count: number;
}

interface HeatmapData {
  cells: HeatmapCell[];
  gridCols: number;
  gridRows: number;
  totalEvents: number;
}

interface SequenceSummary {
  matchesAnalyzed?: number;
  totalSequences?: number;
  totalPlayerActions?: number;
  directAttacks?: number;
  shotEndings?: number;
  averageTerritoryGain?: number;
}

interface SequenceItem {
  matchId?: string | number;
  startTimestamp?: string | number;
  endedWithGoal?: boolean;
  endedWithShot?: boolean;
  boxEntry?: boolean;
  matchLabel?: string;
  teamName?: string;
  route?: string;
  playerActions?: number;
  actions?: number;
  durationSeconds?: number;
}

interface SequenceInsightsData {
  summary?: SequenceSummary;
  topSequences?: SequenceItem[];
}

interface FormDataSnapshot {
  matches_played?: number;
  rolling_xg?: number;
  momentum_xg?: number;
  rolling_pass_accuracy?: number;
}

interface TacticalRolePrediction {
  assigned_role_id?: number;
  role_name?: string;
  confidence_score?: number;
}

interface FatigueRiskPrediction {
  is_high_risk?: boolean;
  fatigue_risk_percentage?: number;
  recommendation?: string;
}

interface AnomalyInsightPrediction {
  is_outlier?: boolean;
  insight?: string;
}

interface MlPredictionsData {
  tacticalRole: TacticalRolePrediction | null;
  fatigueRisk: FatigueRiskPrediction | null;
  anomalyInsight: AnomalyInsightPrediction | null;
}

const toFiniteNumber = (value: unknown): number => {
  const normalized = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(normalized) ? normalized : 0;
};

const resolveEventAnalyticsPlayerId = (player: Player): string => {
  const providerId = player.provider_ids?.opta || player.providerIds?.opta || player.opta_uid;
  return String(providerId || player.id);
};

const normalizeCompositeIndex = (value: unknown): CompositeIndexData | null => {
  if (!value || typeof value !== 'object') {
    return null;
  }

  const data = value as {
    total_index?: unknown;
    composite_index?: unknown;
    components?: {
      attacking?: unknown;
      shooting_contribution?: unknown;
      possession?: unknown;
      passing_contribution?: unknown;
      defending?: unknown;
      duel_contribution?: unknown;
    };
  };

  return {
    totalIndex: toFiniteNumber(data.total_index ?? data.composite_index),
    attacking: toFiniteNumber(data.components?.attacking ?? data.components?.shooting_contribution),
    possession: toFiniteNumber(data.components?.possession ?? data.components?.passing_contribution),
    defending: toFiniteNumber(data.components?.defending ?? data.components?.duel_contribution),
  };
};

const normalizeExpectedMetrics = (value: unknown): ExpectedMetricsData | null => {
  if (!value || typeof value !== 'object') {
    return null;
  }

  const data = value as {
    analytical_xg?: unknown;
    total_xg?: unknown;
    analytical_xa?: unknown;
    total_xa?: unknown;
    shots_with_xg?: unknown;
    passes_with_xa?: unknown;
  };

  return {
    xg: toFiniteNumber(data.analytical_xg ?? data.total_xg),
    xa: toFiniteNumber(data.analytical_xa ?? data.total_xa),
    shotsWithXg: toFiniteNumber(data.shots_with_xg),
    passesWithXa: toFiniteNumber(data.passes_with_xa),
  };
};

const normalizeHeatmap = (value: unknown): HeatmapData | null => {
  if (!value || typeof value !== 'object') {
    return null;
  }

  if (Array.isArray(value)) {
    const cells = value.map((cell) => {
      const data = (cell && typeof cell === 'object' ? cell : {}) as {
        grid_x?: unknown;
        grid_y?: unknown;
        count?: unknown;
      };

      return {
        gridX: toFiniteNumber(data.grid_x),
        gridY: toFiniteNumber(data.grid_y),
        count: toFiniteNumber(data.count),
      };
    });

    return {
      cells,
      gridCols: 10,
      gridRows: 10,
      totalEvents: cells.reduce((sum, cell) => sum + cell.count, 0),
    };
  }

  const data = value as {
    matrix?: unknown;
    grid_cols?: unknown;
    grid_rows?: unknown;
    total_events?: unknown;
  };

  if (!Array.isArray(data.matrix)) {
    return null;
  }

  const cells: HeatmapCell[] = [];
  data.matrix.forEach((column: unknown, gridX: number) => {
    if (!Array.isArray(column)) {
      return;
    }

    column.forEach((count: unknown, gridY: number) => {
      const normalizedCount = toFiniteNumber(count);
      if (normalizedCount <= 0) {
        return;
      }

      cells.push({
        gridX,
        gridY,
        count: normalizedCount,
      });
    });
  });

  return {
    cells,
    gridCols: toFiniteNumber(data.grid_cols) || 10,
    gridRows: toFiniteNumber(data.grid_rows) || 10,
    totalEvents: toFiniteNumber(data.total_events),
  };
};

const PlayerDetail: React.FC<PlayerDetailProps> = ({ player: initialPlayer, onBack }) => {
  const [player, setPlayer] = useState(initialPlayer);
  const [insights, setInsights] = useState<PlayerInsightsData | null>(null);
  const [, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [, setEnhancedStats] = useState<unknown>(null);
  const [heatmap, setHeatmap] = useState<HeatmapData | null>(null);
  const [compositeIndex, setCompositeIndex] = useState<CompositeIndexData | null>(null);
  const [expectedMetrics, setExpectedMetrics] = useState<ExpectedMetricsData | null>(null);
  const [sequenceInsights, setSequenceInsights] = useState<SequenceInsightsData | null>(null);
  const [formData, setFormData] = useState<FormDataSnapshot | null>(null);
  const [mlPredictions, setMlPredictions] = useState<MlPredictionsData | null>(null);

  useEffect(() => {
    const fetchDetails = async () => {
      setLoading(true);
      try {
        const internalPlayerId = String(initialPlayer.id);

        // Fetch advanced player insights from API
        const insightsRes = await apiService.getPlayerInsightsAdvanced(internalPlayerId);
        if (insightsRes.success && insightsRes.data) {
          setInsights(insightsRes.data as PlayerInsightsData);
        }

        // Fetch full player data first so event analytics can use the provider ID namespace.
        const playerRes = await apiService.getPlayer(internalPlayerId);
        const detailedPlayer = playerRes.success && playerRes.data
          ? { ...initialPlayer, ...playerRes.data }
          : initialPlayer;

        if (playerRes.success && playerRes.data) {
          setPlayer((currentPlayer) => ({ ...currentPlayer, ...playerRes.data }));
        }

        const eventAnalyticsPlayerId = resolveEventAnalyticsPlayerId(detailedPlayer);

        // Single bundle call: replaces 5 separate analytics requests.
        // First call computes and persists to MongoDB; subsequent calls return instantly.
        const [bundleRes, formRes, sequenceRes] = await Promise.allSettled([
          apiService.getPlayerAnalyticsBundle(eventAnalyticsPlayerId),
          fetch(`/api/ml/form/${internalPlayerId}`).then(r => r.json()).catch(() => null),
          apiService.getPlayerSequenceInsights(internalPlayerId),
        ]);

        if (bundleRes.status === 'fulfilled' && bundleRes.value.data) {
          const b = bundleRes.value.data;
          if (b.pass_stats && !b.pass_stats.error) setEnhancedStats(b.pass_stats);
          if (b.heatmap && !b.heatmap.error) setHeatmap(normalizeHeatmap(b.heatmap));
          if (b.composite_index && !b.composite_index.error) setCompositeIndex(normalizeCompositeIndex(b.composite_index));
          if (b.expected_metrics && !b.expected_metrics.error) setExpectedMetrics(normalizeExpectedMetrics(b.expected_metrics));
        }

        if (formRes.status === 'fulfilled') {
          const formJson = formRes.value;
          if (formJson?.success && formJson.data) setFormData(formJson.data as FormDataSnapshot);
        }

        if (sequenceRes.status === 'fulfilled' && sequenceRes.value.data) {
          setSequenceInsights(sequenceRes.value.data as SequenceInsightsData);
        }

        // ML Predictions — use real computed values from bundle
        try {
          const bundleData = bundleRes.status === 'fulfilled' ? bundleRes.value.data : null;
          const compData = bundleData?.composite_index ? normalizeCompositeIndex(bundleData.composite_index) : null;
          const passStats = bundleData?.pass_stats ?? {};
          const matchCount = bundleData?.match_count ?? {};
          const passAccuracy = Number(passStats.open_play_completion ?? 0);
          const totalEvents = Number(matchCount.total_events ?? 0);
          const matchesPlayed = Number(matchCount.match_count ?? 0);
          const estimatedMinsPerMatch = 80;

          const predictionsRes = await Promise.allSettled([
            apiService.predictTacticalRole({
              composite_defending: compData?.defending ?? 0,
              composite_possession: compData?.possession ?? 0,
              composite_attacking: compData?.attacking ?? 0,
              pass_accuracy: passAccuracy || 75.0,
              touches_in_box_per_90: totalEvents > 0 ? Math.min((totalEvents / Math.max(matchesPlayed, 1)) * 0.05, 10) : 2.5,
            }),
            apiService.predictFatigueRisk({
              minutes_last_14d: matchesPlayed * estimatedMinsPerMatch,
              days_since_last: 3,
              age: detailedPlayer.age || 25,
              intensity_index: totalEvents > 0 ? Math.min(totalEvents / Math.max(matchesPlayed * 60, 1), 3.0) : 1.1,
            }),
            apiService.predictPerformanceAnomaly({
              xg_differential: (bundleData?.expected_metrics?.total_xg ?? 0) - (compData?.attacking ?? 0) * 0.1,
              pass_volume_diff: (passStats.total_passes ?? 0) - 30,
              defensive_actions_diff: (bundleData?.duel_stats?.total_duels ?? 0) - 10,
              composite_index_deviation: (compData?.totalIndex ?? 0) - 50,
            }),
          ]);

          const [roleRes, fatigueRes, anomalyRes] = predictionsRes;

          // Gateway wraps predictions as { algorithm, prediction: { ... } } — unwrap.
          const unwrapPrediction = (data: unknown): unknown => {
            if (data && typeof data === 'object' && 'prediction' in data) {
              return (data as { prediction: unknown }).prediction;
            }
            return data;
          };

          setMlPredictions({
            tacticalRole: roleRes.status === 'fulfilled' ? unwrapPrediction(roleRes.value.data) as TacticalRolePrediction : null,
            fatigueRisk: fatigueRes.status === 'fulfilled' ? unwrapPrediction(fatigueRes.value.data) as FatigueRiskPrediction : null,
            anomalyInsight: anomalyRes.status === 'fulfilled' ? unwrapPrediction(anomalyRes.value.data) as AnomalyInsightPrediction : null,
          });
        } catch (mlErr) {
          console.error("Failed to fetch ML predictions", mlErr);
        }
      } catch {
        // Silently fall back to initial player data
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [initialPlayer]);

  const handleDownloadReport = async () => {
    setDownloading(true);
    try {
      const blob = await apiService.generatePlayerReport(String(player.id));
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `player-report-${player.name.replace(/\s+/g, '-')}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Failed to download report', e);
    } finally {
      setDownloading(false);
    }
  };

  const resolvedAge = deriveAge(player.age, player.birth_date || player.birthDate);
  const resolvedPosition = player.position || player.detailed_position || player.detailedPosition || 'Unknown position';
  const resolvedClub = player.team || player.club || player.team_name || 'Unknown club';
  const resolvedRating = typeof player.rating === 'number' && Number.isFinite(player.rating)
    ? player.rating
    : typeof player.overallRating === 'number' && Number.isFinite(player.overallRating)
      ? player.overallRating
      : null;
  const matchesPlayed = typeof player.matches === 'number'
    ? player.matches
    : typeof player.appearances === 'number'
      ? player.appearances
      : 0;
  const goals = Number(player.goals ?? 0);
  const assists = Number(player.assists ?? 0);
  const passAccuracy = typeof player.passAccuracy === 'number' ? player.passAccuracy : null;
  const xG = typeof player.xG === 'number' ? player.xG : null;
  const xA = typeof player.xA === 'number' ? player.xA : null;
  const hasTrackedEventData = matchesPlayed > 0 || goals > 0 || assists > 0 || (passAccuracy ?? 0) > 0 || (xG ?? 0) > 0 || (xA ?? 0) > 0 || resolvedRating != null;
  const heatmapCells = heatmap?.cells || [];
  const heatmapGridCols = heatmap?.gridCols || 10;
  const heatmapGridRows = heatmap?.gridRows || 10;
  const heatmapMaxCount = heatmapCells.reduce((max, cell) => Math.max(max, cell.count), 0);
  const heatmapMinCount = heatmapCells.reduce((min, cell) => Math.min(min, cell.count), heatmapCells[0]?.count ?? 0);

  const formatMeasurement = (value?: string | number, suffix?: string) => {
    if (value === undefined || value === null || value === '') {
      return '—';
    }

    const normalized = String(value);
    if (suffix && !normalized.toLowerCase().includes(suffix)) {
      return `${normalized} ${suffix}`;
    }

    return normalized;
  };

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={onBack}
              className="flex items-center text-slate-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Players
            </button>
            <button
              onClick={handleDownloadReport}
              disabled={downloading}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 rounded-lg text-sm transition-colors"
            >
              {downloading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
              <span>{downloading ? 'Generating...' : 'Download PDF'}</span>
            </button>
          </div>

          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <div className="flex items-center space-x-6">
              <img
                src={player.image || player.photo || `https://ui-avatars.com/api/?name=${encodeURIComponent(player.name)}&size=96&background=334155&color=fff`}
                alt={player.name}
                className="w-24 h-24 rounded-full object-cover"
              />
              <div>
                <h1 className="text-3xl font-bold text-white">{player.name}</h1>
                <div className="flex items-center space-x-4 mt-2 text-slate-400">
                  <span className="flex items-center">
                    <Shield className="w-4 h-4 mr-1" />
                    {resolvedPosition}
                  </span>
                  <span className="flex items-center">
                    <Users className="w-4 h-4 mr-1" />
                    {resolvedClub}
                  </span>
                  <span className="flex items-center">
                    <MapPin className="w-4 h-4 mr-1" />
                    {player.nationality}
                  </span>
                  <span className="flex items-center">
                    <Calendar className="w-4 h-4 mr-1" />
                    {resolvedAge != null ? `${resolvedAge} years` : 'Age unavailable'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-400">Market Value</p>
                <p className="text-2xl font-bold text-white">{player.marketValue || '—'}</p>
              </div>
              <DollarSign className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-400">Goals</p>
                <p className="text-2xl font-bold text-white">{hasTrackedEventData ? goals : '—'}</p>
              </div>
              <Target className="w-8 h-8 text-red-500" />
            </div>
          </div>

          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-400">Assists</p>
                <p className="text-2xl font-bold text-white">{hasTrackedEventData ? assists : '—'}</p>
              </div>
              <Zap className="w-8 h-8 text-yellow-500" />
            </div>
          </div>

          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-400">Rating</p>
                <p className="text-2xl font-bold text-white">{resolvedRating != null ? resolvedRating.toFixed(1) : '—'}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-500" />
            </div>
          </div>
        </div>

        {/* Performance Analysis */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              Performance Metrics
            </h3>
            {hasTrackedEventData ? (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Matches Played</span>
                  <span className="font-semibold text-white">{matchesPlayed}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Goals per Match</span>
                  <span className="font-semibold text-white">{matchesPlayed > 0 ? (goals / matchesPlayed).toFixed(2) : '—'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Assists per Match</span>
                  <span className="font-semibold text-white">{matchesPlayed > 0 ? (assists / matchesPlayed).toFixed(2) : '—'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Goal Contributions</span>
                  <span className="font-semibold text-white">{goals + assists}</span>
                </div>
                {passAccuracy != null && (
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Pass Accuracy</span>
                    <span className="font-semibold text-white">{passAccuracy}%</span>
                  </div>
                )}
                {xG != null && (
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">xG</span>
                    <span className="font-semibold text-white">{xG}</span>
                  </div>
                )}
                {xA != null && (
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">xA</span>
                    <span className="font-semibold text-white">{xA}</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="rounded-lg border border-slate-700 bg-slate-700/40 px-4 py-5 text-sm text-slate-300">
                No evaluated event statistics are available for this player yet. Biographical data is shown from the canonical player profile.
              </div>
            )}
          </div>

          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Player Context & Insights</h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
              <div className="rounded-lg bg-slate-700/60 px-3 py-3">
                <div className="text-xs uppercase tracking-wide text-slate-400">Birth Date</div>
                <div className="mt-1 text-sm text-white">{player.birth_date || player.birthDate || '—'}</div>
              </div>
              <div className="rounded-lg bg-slate-700/60 px-3 py-3">
                <div className="text-xs uppercase tracking-wide text-slate-400">Preferred Foot</div>
                <div className="mt-1 text-sm text-white">{player.preferred_foot || player.preferredFoot || '—'}</div>
              </div>
              <div className="rounded-lg bg-slate-700/60 px-3 py-3">
                <div className="text-xs uppercase tracking-wide text-slate-400">Height</div>
                <div className="mt-1 text-sm text-white">{formatMeasurement(player.height, 'cm')}</div>
              </div>
              <div className="rounded-lg bg-slate-700/60 px-3 py-3">
                <div className="text-xs uppercase tracking-wide text-slate-400">Weight</div>
                <div className="mt-1 text-sm text-white">{formatMeasurement(player.weight, 'kg')}</div>
              </div>
              <div className="rounded-lg bg-slate-700/60 px-3 py-3">
                <div className="text-xs uppercase tracking-wide text-slate-400">Shirt Number</div>
                <div className="mt-1 text-sm text-white">{player.shirt_number ?? player.shirtNumber ?? '—'}</div>
              </div>
              <div className="rounded-lg bg-slate-700/60 px-3 py-3">
                <div className="text-xs uppercase tracking-wide text-slate-400">Data Coverage</div>
                <div className="mt-1 text-sm text-white">{hasTrackedEventData ? 'Event metrics available' : 'Profile only'}</div>
              </div>
            </div>

            {/* API-driven insights */}
            {insights && insights.insights && insights.insights.length > 0 && (
              <div className="mt-4 space-y-2">
                <h4 className="text-sm font-medium text-slate-400 mb-2">AI Insights</h4>
                {insights.insights.map((ins: InsightItem, i: number) => (
                  <div key={i} className="p-3 bg-slate-700 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-white">{ins.title}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        ins.impact === 'high' ? 'bg-red-600/30 text-red-300' : 'bg-yellow-600/30 text-yellow-300'
                      }`}>{ins.impact}</span>
                    </div>
                    <p className="text-xs text-slate-400">{ins.description}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Scout ML Service Insights Block */}
            {mlPredictions && (
              <div className="mt-4 space-y-3">
                <h4 className="text-sm font-medium text-slate-400 mb-2 flex items-center">
                  <Activity className="w-4 h-4 mr-2" /> Actionable ML Models
                </h4>
                
                {mlPredictions.tacticalRole && mlPredictions.tacticalRole.assigned_role_id !== undefined && (
                  <div className="p-3 bg-indigo-900/30 border border-indigo-700/50 rounded-lg">
                    <div className="text-xs text-indigo-300 font-semibold uppercase tracking-wide mb-1">Clustered Tactical Role</div>
                    <div className="text-white text-sm font-medium">{mlPredictions.tacticalRole.role_name} <span className="text-xs text-indigo-400 font-normal">({((mlPredictions.tacticalRole.confidence_score ?? 0) * 100).toFixed(0)}% Match)</span></div>
                  </div>
                )}

                {mlPredictions.fatigueRisk && (
                  <div className={`p-3 border rounded-lg ${mlPredictions.fatigueRisk.is_high_risk ? 'bg-red-900/30 border-red-700/50' : 'bg-green-900/30 border-green-700/50'}`}>
                    <div className={`text-xs font-semibold uppercase tracking-wide mb-1 ${mlPredictions.fatigueRisk.is_high_risk ? 'text-red-400' : 'text-green-400'}`}>Physical Fatigue Risk</div>
                    <div className="text-white text-sm">{(mlPredictions.fatigueRisk.fatigue_risk_percentage ?? 0).toFixed(1)}% <span className="text-xs text-slate-400 ml-1">- {mlPredictions.fatigueRisk.recommendation}</span></div>
                  </div>
                )}

                {mlPredictions.anomalyInsight && mlPredictions.anomalyInsight.is_outlier && (
                  <div className="p-3 bg-yellow-900/30 border border-yellow-700/50 rounded-lg">
                    <div className="text-xs text-yellow-400 font-semibold uppercase tracking-wide mb-1">Performance Anomaly</div>
                    <div className="text-white text-sm text-balance leading-tight">{mlPredictions.anomalyInsight.insight}</div>
                  </div>
                )}
              </div>
            )}

          </div>
        </div>        

        <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6 mt-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <Activity className="w-5 h-5 mr-2 text-cyan-400" />
            Sequence Involvement
          </h3>

          {sequenceInsights?.summary?.matchesAnalyzed > 0 ? (
            <>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                <div className="rounded-lg bg-slate-700/40 px-3 py-3">
                  <div className="text-xs uppercase tracking-wide text-slate-400">Matches</div>
                  <div className="mt-1 text-lg font-semibold text-white">{sequenceInsights.summary.matchesAnalyzed}</div>
                </div>
                <div className="rounded-lg bg-slate-700/40 px-3 py-3">
                  <div className="text-xs uppercase tracking-wide text-slate-400">Sequences</div>
                  <div className="mt-1 text-lg font-semibold text-white">{sequenceInsights.summary.totalSequences}</div>
                </div>
                <div className="rounded-lg bg-slate-700/40 px-3 py-3">
                  <div className="text-xs uppercase tracking-wide text-slate-400">Player Actions</div>
                  <div className="mt-1 text-lg font-semibold text-white">{sequenceInsights.summary.totalPlayerActions}</div>
                </div>
                <div className="rounded-lg bg-slate-700/40 px-3 py-3">
                  <div className="text-xs uppercase tracking-wide text-slate-400">Direct Attacks</div>
                  <div className="mt-1 text-lg font-semibold text-white">{sequenceInsights.summary.directAttacks}</div>
                </div>
                <div className="rounded-lg bg-slate-700/40 px-3 py-3">
                  <div className="text-xs uppercase tracking-wide text-slate-400">Shot Endings</div>
                  <div className="mt-1 text-lg font-semibold text-white">{sequenceInsights.summary.shotEndings}</div>
                </div>
                <div className="rounded-lg bg-slate-700/40 px-3 py-3">
                  <div className="text-xs uppercase tracking-wide text-slate-400">Avg Territory Gain</div>
                  <div className="mt-1 text-lg font-semibold text-white">{sequenceInsights.summary.averageTerritoryGain}</div>
                </div>
              </div>

              {Array.isArray(sequenceInsights.topSequences) && sequenceInsights.topSequences.length > 0 && (
                <div className="mt-5 space-y-3">
                  <h4 className="text-sm font-medium text-slate-400">Top Sequences</h4>
                  {sequenceInsights.topSequences.slice(0, 3).map((sequence: SequenceItem, index: number) => {
                    const outcome = sequence.endedWithGoal
                      ? 'Ended with goal'
                      : sequence.endedWithShot
                        ? 'Ended with shot'
                        : sequence.boxEntry
                          ? 'Reached the box'
                          : 'Advanced possession';

                    return (
                      <div key={`${sequence.matchId}-${sequence.startTimestamp}-${index}`} className="rounded-lg border border-slate-700 bg-slate-700/30 px-4 py-3">
                        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                          <div>
                            <div className="text-sm font-semibold text-white">{sequence.matchLabel}</div>
                            <div className="text-xs text-slate-400">
                              {sequence.teamName} • {sequence.route} • {sequence.playerActions} player actions
                            </div>
                          </div>
                          <div className="text-xs text-slate-300 md:text-right">
                            <div>{sequence.actions} actions over {sequence.durationSeconds}s</div>
                            <div>{outcome}</div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </>
          ) : (
            <div className="rounded-lg border border-slate-700 bg-slate-700/40 px-4 py-5 text-sm text-slate-300">
              No sequence-level involvement is available for this player yet.
            </div>
          )}
        </div>

        {/* Phase 4 Form Widget */}
        {formData && (
          <div className="bg-slate-800 rounded-lg shadow-sm border-t-2 border-indigo-500 p-6 mt-6 mb-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center">
              <TrendingUp className="h-5 w-5 text-indigo-400 mr-2" />
              Live Form Momentum (ML)
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-700/50 rounded-lg p-4 text-center">
                <p className="text-sm text-slate-400 font-medium">Matches</p>
                <p className="text-2xl font-bold text-white mt-1">{formData.matches_played || 0}</p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4 text-center">
                <p className="text-sm text-slate-400 font-medium">Rolling xG</p>
                <p className="text-2xl font-bold text-indigo-400 mt-1">{(formData.rolling_xg || 0).toFixed(2)}</p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4 text-center">
                <p className="text-sm text-slate-400 font-medium">xG Momentum</p>
                <p className={`text-2xl font-bold mt-1 ${(formData.momentum_xg || 0) > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {(formData.momentum_xg || 0) > 0 ? '+' : ''}{(formData.momentum_xg || 0).toFixed(2)}
                </p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4 text-center">
                <p className="text-sm text-slate-400 font-medium">Rolling Pass Acc</p>
                <p className="text-2xl font-bold text-sky-400 mt-1">{((formData.rolling_pass_accuracy || 0) * 100).toFixed(1)}%</p>
              </div>
            </div>
          </div>
        )}
        
        {/* Phase 3 Advanced Analytics Block */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
              <Zap className="w-5 h-5 mr-2 text-yellow-400" />
              Composite Index & Expected
            </h3>
            <div className="space-y-4">
              {compositeIndex ? (
                <>
                  <div className="flex justify-between items-center bg-slate-700/30 p-2 rounded">
                    <span className="text-slate-400">Total Index</span>
                    <span className="font-bold text-green-400">{compositeIndex.totalIndex.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center p-2">
                    <span className="text-slate-400">Attacking</span>
                    <span className="font-semibold text-white">{compositeIndex.attacking.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center p-2">
                    <span className="text-slate-400">Possession</span>
                    <span className="font-semibold text-white">{compositeIndex.possession.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center p-2">
                    <span className="text-slate-400">Defending</span>
                    <span className="font-semibold text-white">{compositeIndex.defending.toFixed(2)}</span>
                  </div>
                </>
              ) : (
                <div className="text-slate-400 text-sm border border-slate-700/50 p-3 rounded-lg text-center">
                  Computing composite elements...
                </div>
              )}
              {expectedMetrics && (
                <div className="mt-4 pt-4 border-t border-slate-700">
                  <div className="flex justify-between items-center p-2">
                    <span className="text-slate-400">Analytical xG</span>
                    <span className="font-semibold text-white">{expectedMetrics.xg.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center p-2">
                    <span className="text-slate-400">Analytical xA</span>
                    <span className="font-semibold text-white">{expectedMetrics.xa.toFixed(2)}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-3 px-2 pt-2 text-xs text-slate-400">
                    <span>Shots With xG: {expectedMetrics.shotsWithXg}</span>
                    <span>Passes With xA: {expectedMetrics.passesWithXa}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
              <Target className="w-5 h-5 mr-2 text-red-400" />
              Spatial Density Heatmap
            </h3>
            {heatmap && heatmapCells.length > 0 ? (
              <div className="relative w-full h-56 bg-emerald-900/20 border border-emerald-600/30 rounded flex items-center justify-center overflow-hidden">
                {/* Scaled Pitch Background lines */}
                <div className="absolute inset-0 border border-white/10" />
                <div className="absolute top-0 bottom-0 left-1/2 w-px bg-white/10" />
                <div className="absolute top-1/2 left-1/2 w-12 h-12 border border-white/10 rounded-full -translate-x-1/2 -translate-y-1/2" />
                
                {/* Simplified Heatmap Render */}
                {heatmapCells.map((cell, i: number) => {
                   // normalize count to 0-1 scale
                   const normalized = heatmapMaxCount > heatmapMinCount
                     ? (cell.count - heatmapMinCount) / (heatmapMaxCount - heatmapMinCount)
                     : 1;
                   const opacity = Math.max(0.2, normalized);
                   const left = `${((cell.gridX + 0.5) / heatmapGridCols) * 100}%`;
                   const bottom = `${((cell.gridY + 0.5) / heatmapGridRows) * 100}%`;
                   
                   // heat intensity color (yellow -> red)
                   const color = opacity > 0.7 ? 'bg-red-500' : opacity > 0.4 ? 'bg-orange-500' : 'bg-yellow-500';
                   const scale = 1 + (opacity * 0.5);

                   return (
                     <div key={i} className={`absolute w-8 h-8 ${color} rounded-full blur-md opacity-70 transition-transform`} 
                          style={{ 
                            left, 
                            bottom, 
                            transform: `translate(-50%, 50%) scale(${scale})`,
                            zIndex: Math.floor(opacity * 10)
                          }}
                          title={`Zone (${cell.gridX},${cell.gridY}): ${cell.count} events`} />
                   );
                })}
              </div>
            ) : (
              <div className="text-slate-400 text-sm border border-slate-700/50 p-6 rounded-lg text-center h-56 flex items-center justify-center">
                {heatmap ? 'No spatial event data available for this player.' : 'Waiting for spatial telemetry...'}
              </div>
            )}
          </div>
        </div>      </div>
    </div>
  );
};

export default PlayerDetail;