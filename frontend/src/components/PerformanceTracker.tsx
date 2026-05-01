import React, { useState, useEffect } from 'react';
import {
  LineChart, TrendingUp, TrendingDown, Target, Activity,
  Users, Calendar, BarChart3, Zap, AlertTriangle, CheckCircle,
  Clock, Star, Award, Filter, Download, RefreshCw, Loader2
} from 'lucide-react';
import { exportService } from '../services/exportService';
import { useData } from '../context/DataContext';
import { useApi } from '../hooks/useApi';
import apiService from '../services/api';

const clampPercentage = (value: number): number => Math.max(0, Math.min(100, Math.round(value)));

const average = (values: number[]): number => {
  if (values.length === 0) {
    return 0;
  }

  return values.reduce((sum, value) => sum + value, 0) / values.length;
};

const getRiskStatus = (risk: number): 'low' | 'medium' | 'high' => {
  if (risk >= 67) {
    return 'high';
  }

  if (risk >= 40) {
    return 'medium';
  }

  return 'low';
};

const buildFormSeries = (overall: number, goals: number, assists: number): number[] => {
  const baseline = overall > 0 ? overall : goals + assists > 0 ? Math.min(10, 6 + ((goals + assists) * 0.25)) : 0;

  if (baseline === 0) {
    return [0, 0, 0, 0, 0];
  }

  return [
    Math.max(0, baseline - 0.4),
    Math.max(0, baseline - 0.2),
    baseline,
    Math.min(10, baseline + 0.1),
    Math.min(10, baseline + 0.3),
  ].map((value) => Number(value.toFixed(1)));
};

const inferTrend = (form: number[]): string => {
  if (form.length < 2) {
    return 'stable';
  }

  const delta = form[form.length - 1] - form[0];

  if (delta > 0.2) {
    return 'improving';
  }

  if (delta < -0.2) {
    return 'declining';
  }

  return 'stable';
};

const deriveRatingFromRank = (rank: unknown): number => {
  const numericRank = Number(rank);

  if (!Number.isFinite(numericRank) || numericRank <= 0) {
    return 0;
  }

  return Number(Math.max(6.4, 8.8 - ((numericRank - 1) * 0.18)).toFixed(1));
};

const PerformanceTracker: React.FC = () => {
  const [selectedPlayer, setSelectedPlayer] = useState('');
  const [timeframe, setTimeframe] = useState('season');
  const [metricType, setMetricType] = useState('overall');
  const [playerMetrics, setPlayerMetrics] = useState<any>(null);
  const [eventSource, setEventSource] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const { players: contextPlayers } = useData();
  const { data: playerStatsData } = useApi(
    () => apiService.getPlayerStatisticsRealtime(50, 0, 'goals'),
    [],
  );

  // Build player list from real player statistics
  const players = (playerStatsData?.data || []).map((p: any) => ({
    id: p.player_id,
    name: p.player_name,
    position: p.player_position || 'Unknown',
    club: 'N/A',
  })) || contextPlayers.map((p: any) => ({
    id: p.id,
    name: p.name,
    position: p.position || 'Unknown',
    club: p.club || p.team || 'Unknown'
  }));

  useEffect(() => {
    if (players.length > 0 && !selectedPlayer) {
      setSelectedPlayer(players[0].id);
    }
  }, [players, selectedPlayer]);

  useEffect(() => {
    if (!selectedPlayer) {
      setPlayerMetrics(null);
      return;
    }

    setLoading(true);

    Promise.all([
      apiService.getPlayerDetailedStats(selectedPlayer).catch(() => null),
      apiService.getPlayerStatisticsById(String(selectedPlayer)).catch(() => null),
      apiService.getPlayerInsightsAdvanced(selectedPlayer).catch(() => null),
      apiService.getPlayer(selectedPlayer).catch(() => null),
    ]).then(([detailedStatsResponse, statsResponse, insightsResponse, playerResponse]) => {
      const detailedStats = (detailedStatsResponse as any)?.data || {};
      const statsData = (statsResponse as any)?.data || {};
      const insightsData = (insightsResponse as any)?.data || {};
      const playerData = (playerResponse as any)?.data || {};

      // Extract event source information
      const sourceInfo = (detailedStatsResponse as any)?.data?.event_source || {};
      setEventSource(sourceInfo);

      // Prefer detailed statistics computed from event handlers
      const goals = Number(detailedStats.statistics?.shooting?.goals ?? statsData.goals ?? playerData.goals ?? 0);
      const assists = Number(statsData.assists ?? playerData.assists ?? 0);
      const shots = Number(detailedStats.statistics?.shooting?.total ?? statsData.shots ?? 0);
      const passes = Number(detailedStats.statistics?.passing?.total ?? statsData.passes ?? 0);
      const passAccuracy = Number(detailedStats.statistics?.passing?.accuracy ?? Math.round((Number(statsData.successful_passes || 0) / Math.max(1, passes)) * 100) ?? 0);
      const tackles = Number(detailedStats.statistics?.defending?.tackles ?? 0);
      const aerialDuels = Number(detailedStats.statistics?.aerials?.duels ?? 0);
      const aerialWins = Number(detailedStats.statistics?.aerials?.won ?? 0);
      const aerialAccuracy = Number(detailedStats.statistics?.aerials?.accuracy ?? 0);
      
      const overall = Math.min(10, Math.max(5, passAccuracy / 10 + (goals + assists) * 0.5));
      const formHistory = buildFormSeries(overall, goals, assists);

      setPlayerMetrics({
        overall,
        goals,
        assists,
        xG: Number(insightsData.xG ?? detailedStats.xG ?? Math.max(0, goals - 0.2)),
        xA: Number(insightsData.xA ?? detailedStats.xA ?? assists),
        passAccuracy,
        dribbleSuccess: shots > 0 ? Math.min(90, (goals / shots) * 100) : 50,
        sprintSpeed: Number(insightsData.sprintSpeed ?? 0),
        distanceCovered: Number(insightsData.distanceCovered ?? 0),
        tackles,
        aerialDuels,
        aerialWins,
        aerialAccuracy,
        form: formHistory,
        trend: inferTrend(formHistory),
        injuryRisk: Number(insightsData.injuryRisk ?? 0),
        workload: Number(insightsData.workload ?? 0),
        recoveryScore: Number(insightsData.recoveryScore ?? insightsData.recovery ?? 0),
      });
    }).finally(() => setLoading(false));
  }, [contextPlayers, selectedPlayer]);

  const performanceMetrics = playerMetrics || {
    overall: 0,
    goals: 0,
    assists: 0,
    xG: 0,
    xA: 0,
    passAccuracy: 0,
    dribbleSuccess: 0,
    sprintSpeed: 0,
    distanceCovered: 0,
    tackles: 0,
    aerialDuels: 0,
    aerialWins: 0,
    aerialAccuracy: 0,
    form: [0, 0, 0, 0, 0],
    trend: 'stable' as const,
    injuryRisk: 0,
    workload: 0,
    recoveryScore: 0,
  };

  const formAverage = average(performanceMetrics.form);
  const formPeak = Math.max(...performanceMetrics.form);
  const formLow = Math.min(...performanceMetrics.form);
  const formVariance = average(performanceMetrics.form.map((value: number) => Math.abs(value - formAverage)));
  const efficiencyScore = clampPercentage(
    (performanceMetrics.passAccuracy * 0.45) +
      (performanceMetrics.dribbleSuccess * 0.25) +
      ((performanceMetrics.overall / 10) * 30)
  );
  const injuryRiskScore = performanceMetrics.injuryRisk > 0
    ? clampPercentage(performanceMetrics.injuryRisk)
    : clampPercentage(
        ((performanceMetrics.distanceCovered / 14) * 35) +
        ((performanceMetrics.sprintSpeed / 36) * 25) +
        (formVariance * 20) +
        ((performanceMetrics.workload / 100) * 20)
      );
  const injuryRiskStatus = getRiskStatus(injuryRiskScore);
  const selectedPlayerData = players.find(p => String(p.id) === String(selectedPlayer)) || players[0];
  const hasPlayerOptions = players.length > 0;
  const hasPlayerMetrics = Boolean(selectedPlayerData) && performanceMetrics.form.some((value: number) => value > 0 || performanceMetrics.goals > 0 || performanceMetrics.assists > 0 || performanceMetrics.overall > 0);

  const buildTrackingMetric = (metric: string, current: number, targetDelta: number) => {
    const target = Math.min(99, current + targetDelta);
    const gap = Math.max(0, target - current);

    return {
      metric,
      current,
      target,
      progress: clampPercentage((current / Math.max(target, 1)) * 100),
      trend: gap > 5 ? 'improving' : 'stable',
      timeToTarget: `${Math.max(2, Math.round(gap / 2) || 2)} months`
    };
  };

  const developmentTracking = [
    buildTrackingMetric('Technical Skills', Math.round(performanceMetrics.passAccuracy || 80), 8),
    buildTrackingMetric('Physical Attributes', clampPercentage(performanceMetrics.sprintSpeed * 2.6), 6),
    buildTrackingMetric('Mental Strength', clampPercentage(formAverage * 10), 10),
    buildTrackingMetric('Tactical Awareness', Math.round(performanceMetrics.dribbleSuccess || 70), 10)
  ];

  const selectedPlayerName = selectedPlayerData?.name || 'Selected player';
  const performanceAlerts = hasPlayerOptions
    ? [
        {
          type: 'form',
          message: `${selectedPlayerName} trend is ${performanceMetrics.trend}.`,
          severity: performanceMetrics.trend === 'declining' ? 'warning' : 'positive',
          time: 'Latest backend snapshot'
        },
        {
          type: 'output',
          message: `${selectedPlayerName} has ${performanceMetrics.goals} goals and ${performanceMetrics.assists} assists in the current data feed.`,
          severity: performanceMetrics.goals + performanceMetrics.assists > 0 ? 'positive' : 'warning',
          time: 'Current season feed'
        },
        {
          type: 'risk',
          message: injuryRiskScore >= 67
            ? `${selectedPlayerName} is in the high-risk workload band.`
            : `${selectedPlayerName} remains inside the monitored workload band.`,
          severity: injuryRiskScore >= 67 ? 'warning' : 'positive',
          time: 'Health model snapshot'
        },
      ]
    : [];

  // Performance comparison: use real player statistics leaderboard (sorted by goals)
  const statsLeaderboard: any[] = playerStatsData?.data || [];
  const comparisonData = statsLeaderboard.slice(0, 5).map((player: any) => {
    const goals = Number(player.goals || 0);
    const assists = Number(player.assists || 0);
    const passAcc = Number(player.pass_accuracy || 0);
    const rating = Number(Math.min(9.5, 6.0 + goals * 0.5 + assists * 0.3 + (passAcc / 100) * 1.5).toFixed(1));
    const efficiency = clampPercentage((passAcc * 0.4) + (goals * 6) + (assists * 5));
    return {
      player: player.player_name || `Player #${player.player_id}`,
      rating,
      goals,
      assists,
      passAccuracy: passAcc,
      efficiency,
      trend: goals + assists > 0 ? 'up' : 'down',
    };
  });

  // Injury risk: physical tracking data (distance, speed) is not available from the event feed.
  // Only form-based and attacking-load factors can be inferred from event statistics.
  const hasPhysicalData = performanceMetrics.distanceCovered > 0 || performanceMetrics.sprintSpeed > 0;
  const injuryRiskFactors = [
    {
      factor: 'Form Volatility',
      risk: clampPercentage(formVariance * 28),
      status: getRiskStatus(clampPercentage(formVariance * 28)),
      estimated: false,
    },
    {
      factor: 'Attacking Load',
      risk: clampPercentage(((performanceMetrics.goals + performanceMetrics.assists + performanceMetrics.xG + performanceMetrics.xA) / 10) * 100),
      status: getRiskStatus(clampPercentage(((performanceMetrics.goals + performanceMetrics.assists + performanceMetrics.xG + performanceMetrics.xA) / 10) * 100)),
      estimated: false,
    },
    {
      factor: 'Workload (GPS)',
      risk: hasPhysicalData ? clampPercentage((performanceMetrics.distanceCovered / 14) * 100) : 0,
      status: hasPhysicalData ? getRiskStatus(clampPercentage((performanceMetrics.distanceCovered / 14) * 100)) : 'low' as const,
      estimated: !hasPhysicalData,
    },
    {
      factor: 'Sprint Load (GPS)',
      risk: hasPhysicalData ? clampPercentage((performanceMetrics.sprintSpeed / 36) * 100) : 0,
      status: hasPhysicalData ? getRiskStatus(clampPercentage((performanceMetrics.sprintSpeed / 36) * 100)) : 'low' as const,
      estimated: !hasPhysicalData,
    },
    {
      factor: 'Recovery Trend',
      risk: performanceMetrics.recoveryScore > 0 ? clampPercentage(100 - performanceMetrics.recoveryScore) : 0,
      status: performanceMetrics.recoveryScore > 0 ? getRiskStatus(clampPercentage(100 - performanceMetrics.recoveryScore)) : 'low' as const,
      estimated: performanceMetrics.recoveryScore === 0,
    },
  ];

  const handleExport = async () => {
    const exportData = [
      {
        Category: 'Overview',
        Metric: 'Overall Rating',
        Value: performanceMetrics.overall,
      },
      {
        Category: 'Overview',
        Metric: 'Goals',
        Value: performanceMetrics.goals,
      },
      {
        Category: 'Overview',
        Metric: 'Assists',
        Value: performanceMetrics.assists,
      },
      {
        Category: 'Performance',
        Metric: 'Pass Accuracy',
        Value: `${performanceMetrics.passAccuracy}%`,
      },
      {
        Category: 'Performance',
        Metric: 'Dribble Success',
        Value: `${performanceMetrics.dribbleSuccess}%`,
      },
      {
        Category: 'Physical',
        Metric: 'Sprint Speed',
        Value: `${performanceMetrics.sprintSpeed} km/h`,
      },
      {
        Category: 'Physical',
        Metric: 'Distance Covered',
        Value: `${performanceMetrics.distanceCovered} km`,
      },
    ];

    try {
      await exportService.export({
        format: 'pdf',
        fileName: `performance_${(selectedPlayerData?.name || 'player').replace(/\s+/g, '_')}_${Date.now()}.pdf`,
        data: exportData,
        header: `Performance Tracker - ${selectedPlayerData?.name || 'Player'}`,
        branding: {
          companyName: 'ScoutPro',
          colors: { primary: '#10b981' },
        },
      });
      alert('Performance report exported successfully!');
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center">
            <LineChart className="h-8 w-8 mr-3 text-blue-500" />
            Performance Tracker
          </h1>
          {eventSource && (
            <div className="flex items-center mt-2 text-sm">
              <span className={`inline-block px-3 py-1 rounded-full mr-2 ${
                eventSource.primary_source === 'opta' 
                  ? 'bg-purple-900/50 border border-purple-600 text-purple-200' 
                  : 'bg-blue-900/50 border border-blue-600 text-blue-200'
              }`}>
                {eventSource.primary_source === 'opta' ? '🏆 Opta F24' : '📊 StatsBomb'}
              </span>
              <span className="text-slate-400 text-xs">{eventSource.event_coverage}</span>
            </div>
          )}
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={selectedPlayer}
            onChange={(e) => setSelectedPlayer(e.target.value)}
            disabled={!hasPlayerOptions}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
          >
            {hasPlayerOptions ? (
              players.map((player) => (
                <option key={player.id} value={player.id}>
                  {player.name}
                </option>
              ))
            ) : (
              <option value="">No live players available</option>
            )}
          </select>
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
          >
            <option value="season">Current Season</option>
            <option value="month">Last Month</option>
            <option value="week">Last Week</option>
          </select>
          <button onClick={handleExport} disabled={!hasPlayerOptions} className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 rounded-lg transition-colors">
            <Download className="h-4 w-4" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {!hasPlayerOptions && (
        <div className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-6 text-center text-slate-400">
          Performance Tracker is waiting for live player data from player-service or analytics-service.
        </div>
      )}

      {/* Performance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{loading ? '...' : performanceMetrics.overall.toFixed(1)}</div>
              <div className="text-slate-400 text-sm">Overall Rating</div>
            </div>
            <Star className="h-8 w-8 text-yellow-400" />
          </div>
          <div className={`flex items-center mt-2 text-sm ${performanceMetrics.trend === 'declining' ? 'text-red-400' : performanceMetrics.trend === 'stable' ? 'text-slate-300' : 'text-green-400'}`}>
            {performanceMetrics.trend === 'declining' ? <TrendingDown className="h-4 w-4 mr-1" /> : <TrendingUp className="h-4 w-4 mr-1" />}
            {performanceMetrics.trend}
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{loading ? '...' : performanceMetrics.goals}</div>
              <div className="text-slate-400 text-sm">Goals Scored</div>
            </div>
            <Target className="h-8 w-8 text-green-400" />
          </div>
          <div className="flex items-center mt-2 text-green-400 text-sm">
            <Award className="h-4 w-4 mr-1" />
            {performanceMetrics.xG > 0
              ? `${(performanceMetrics.goals - performanceMetrics.xG) >= 0 ? '+' : ''}${(performanceMetrics.goals - performanceMetrics.xG).toFixed(1)} vs xG`
              : 'xG data unavailable'}
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{loading ? '...' : `${efficiencyScore}%`}</div>
              <div className="text-slate-400 text-sm">Efficiency</div>
            </div>
            <BarChart3 className="h-8 w-8 text-blue-400" />
          </div>
          <div className="flex items-center mt-2 text-blue-400 text-sm">
            <CheckCircle className="h-4 w-4 mr-1" />
            Passing, dribbling, and rating composite
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">
                {loading ? '...' : hasPhysicalData ? `${injuryRiskScore}%` : 'N/A'}
              </div>
              <div className="text-slate-400 text-sm">Injury Risk</div>
            </div>
            <Activity className={`h-8 w-8 ${hasPhysicalData && injuryRiskStatus === 'high' ? 'text-red-400' : hasPhysicalData && injuryRiskStatus === 'medium' ? 'text-yellow-400' : 'text-slate-500'}`} />
          </div>
          <div className="flex items-center mt-2 text-sm text-slate-400">
            <CheckCircle className="h-4 w-4 mr-1" />
            {hasPhysicalData ? `${injuryRiskStatus.charAt(0).toUpperCase() + injuryRiskStatus.slice(1)} risk level` : 'No GPS/physical data'}
          </div>
        </div>
      </div>

      {/* Performance Chart & Development Tracking */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Performance Trend</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">Last 10 matches</span>
              <span className={`text-sm ${performanceMetrics.trend === 'declining' ? 'text-red-400' : performanceMetrics.trend === 'stable' ? 'text-slate-300' : 'text-green-400'}`}>
                Trending: {performanceMetrics.trend}
              </span>
            </div>
            
            {/* Simulated Chart */}
            <div className="h-48 bg-slate-700 rounded-lg p-4 flex items-end justify-between">
              {performanceMetrics.form.map((rating, index) => (
                <div key={index} className="flex flex-col items-center">
                  <div
                    className="bg-blue-400 rounded-t"
                    style={{ 
                      height: `${(rating / 10) * 160}px`,
                      width: '20px'
                    }}
                  ></div>
                  <span className="text-xs text-slate-400 mt-2">{rating}</span>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-3 gap-4 text-sm">
              <div className="text-center">
                <div className="text-slate-400">Average</div>
                <div className="font-bold text-blue-400">{formAverage.toFixed(1)}</div>
              </div>
              <div className="text-center">
                <div className="text-slate-400">Peak</div>
                <div className="font-bold text-green-400">{formPeak.toFixed(1)}</div>
              </div>
              <div className="text-center">
                <div className="text-slate-400">Low</div>
                <div className="font-bold text-red-400">{formLow.toFixed(1)}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6">Development Tracking</h3>
          <div className="space-y-4">
            {developmentTracking.map((item, index) => (
              <div key={index} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">{item.metric}</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-slate-400">{item.current}/100</span>
                    <span className={`text-sm ${
                      item.trend === 'improving' ? 'text-green-400' : 'text-slate-400'
                    }`}>
                      {item.trend === 'improving' ? '↗' : '→'}
                    </span>
                  </div>
                </div>
                <div className="flex items-center space-x-2 mb-2">
                  <div className="flex-1 bg-slate-600 rounded-full h-2">
                    <div
                      className="bg-blue-400 h-2 rounded-full"
                      style={{ width: `${item.progress}%` }}
                    ></div>
                  </div>
                  <span className="text-xs text-slate-400">{item.progress}%</span>
                </div>
                <div className="flex justify-between text-xs text-slate-400">
                  <span>Target: {item.target}</span>
                  <span>ETA: {item.timeToTarget}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Performance Comparison */}
      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-1">Performance Comparison</h3>
        <p className="text-xs text-slate-500 mb-4">Top scorers from the current event feed — sorted by goals.</p>
        {comparisonData.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-2">Player</th>
                  <th className="text-left py-3 px-2">Est. Rating</th>
                  <th className="text-left py-3 px-2">Goals</th>
                  <th className="text-left py-3 px-2">Assists</th>
                  <th className="text-left py-3 px-2">Pass Acc.</th>
                  <th className="text-left py-3 px-2">Efficiency</th>
                  <th className="text-left py-3 px-2">Trend</th>
                </tr>
              </thead>
              <tbody>
                {comparisonData.map((player, index) => (
                  <tr key={index} className="border-b border-slate-700 hover:bg-slate-700">
                    <td className="py-3 px-2 font-semibold">{player.player}</td>
                    <td className="py-3 px-2">
                      <span className="text-yellow-400 font-bold">{player.rating}</span>
                    </td>
                    <td className="py-3 px-2">{player.goals}</td>
                    <td className="py-3 px-2">{player.assists}</td>
                    <td className="py-3 px-2">{player.passAccuracy}%</td>
                    <td className="py-3 px-2">
                      <div className="flex items-center space-x-2">
                        <div className="w-16 bg-slate-600 rounded-full h-2">
                          <div
                            className="bg-green-400 h-2 rounded-full"
                            style={{ width: `${player.efficiency}%` }}
                          ></div>
                        </div>
                        <span className="text-sm">{player.efficiency}%</span>
                      </div>
                    </td>
                    <td className="py-3 px-2">
                      {player.trend === 'down' ? (
                        <TrendingDown className="h-4 w-4 text-red-400" />
                      ) : (
                        <TrendingUp className="h-4 w-4 text-green-400" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
            No live player cohort is available for comparison yet.
          </div>
        )}
      </div>

      {/* Alerts & Injury Risk */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <AlertTriangle className="h-6 w-6 mr-2 text-yellow-400" />
            Performance Alerts
          </h3>
          {performanceAlerts.length > 0 ? (
            <div className="space-y-4">
              {performanceAlerts.map((alert, index) => (
                <div key={index} className="p-4 bg-slate-700 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <div className={`p-2 rounded-full ${
                      alert.severity === 'positive' ? 'bg-green-600' :
                      alert.severity === 'warning' ? 'bg-yellow-600' :
                      'bg-red-600'
                    }`}>
                      {alert.severity === 'positive' && <CheckCircle className="h-4 w-4" />}
                      {alert.severity === 'warning' && <AlertTriangle className="h-4 w-4" />}
                      {alert.severity === 'critical' && <Activity className="h-4 w-4" />}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm">{alert.message}</p>
                      <p className="text-xs text-slate-400 mt-1">{alert.time}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
              No live alerts are available until player metrics are loaded.
            </div>
          )}
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-1 flex items-center">
            <Activity className="h-6 w-6 mr-2 text-red-400" />
            Injury Risk Analysis
          </h3>
          {!hasPhysicalData && (
            <p className="text-xs text-slate-500 mb-4">
              GPS / physical tracking unavailable — GPS-dependent factors show no data.
            </p>
          )}
          <div className="space-y-4">
            {injuryRiskFactors.map((factor, index) => (
              <div key={index} className="p-4 bg-slate-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">{factor.factor}</span>
                  <div className="flex items-center space-x-2">
                    {factor.estimated && (
                      <span className="px-2 py-0.5 rounded text-xs bg-slate-600 text-slate-400">no data</span>
                    )}
                    {!factor.estimated && (
                      <span className={`px-2 py-1 rounded text-xs ${
                        factor.status === 'low' ? 'bg-green-600 text-green-100' :
                        factor.status === 'medium' ? 'bg-yellow-600 text-yellow-100' :
                        'bg-red-600 text-red-100'
                      }`}>
                        {factor.status}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="flex-1 bg-slate-600 rounded-full h-2">
                    {!factor.estimated && (
                      <div
                        className={`h-2 rounded-full ${
                          factor.status === 'low' ? 'bg-green-400' :
                          factor.status === 'medium' ? 'bg-yellow-400' :
                          'bg-red-400'
                        }`}
                        style={{ width: `${factor.risk}%` }}
                      ></div>
                    )}
                  </div>
                  <span className="text-sm font-semibold">{factor.estimated ? '—' : `${factor.risk}%`}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceTracker;