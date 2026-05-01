import React, { useMemo, useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  Users,
  Activity,
  Brain,
  Calendar,
  Loader2,
  Trophy,
  Target,
  Zap,
} from 'lucide-react';
import { useApi } from '../hooks/useApi';
import apiService from '../services/api';

type TrendMetric = 'avgGoals' | 'avgHomeGoals' | 'avgAwayGoals' | 'matchCount';

const METRIC_LABELS: Record<TrendMetric, string> = {
  avgGoals: 'Average Goals',
  avgHomeGoals: 'Home Goals',
  avgAwayGoals: 'Away Goals',
  matchCount: 'Matches Played',
};

const toNumber = (value: unknown): number => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
};

const formatMetric = (value: unknown, digits = 0): string => {
  if (value === undefined || value === null || value === '') {
    return '—';
  }

  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric.toFixed(digits) : String(value);
};

const formatMatchLabel = (match: any) => {
  const home = match.home_team_name || match.homeTeam || match.home_team_id || 'Home';
  const away = match.away_team_name || match.awayTeam || match.away_team_id || 'Away';
  return `${home} vs ${away}`;
};

const AnalyticsDashboard: React.FC = () => {
  const [selectedMetric, setSelectedMetric] = useState<TrendMetric>('avgGoals');
  const [timeframe, setTimeframe] = useState('season');

  const { data: dashboardData, loading: dashLoading } = useApi(
    () => apiService.getDashboardOverview(), []
  );
  const { data: leagueTrends, loading: trendsLoading } = useApi(
    () => apiService.getLeagueTrends(), []
  );
  const loading = dashLoading || trendsLoading;
  const summary = dashboardData?.summary || dashboardData?.data || {};
  const topPlayers = dashboardData?.topPlayers || [];
  const topTeams = dashboardData?.topTeams || [];
  const recentMatches = dashboardData?.recentMatches || [];
  const predictionSummary = dashboardData?.predictions || {};
  const trendLimit = timeframe === 'week' ? 4 : timeframe === 'month' ? 6 : 12;

  const trendRows = useMemo(
    () => (leagueTrends?.trends || []).slice(-trendLimit),
    [leagueTrends, trendLimit],
  );

  const maxTrendValue = Math.max(1, ...trendRows.map((row: any) => toNumber(row[selectedMetric])));

  const playerRows = topPlayers.slice(0, 6).map((player: any) => ({
    id: player.playerID || player.player_id,
    name: player.player_name || player.playerName || `Player #${player.playerID || player.player_id}`,
    rank: player.rank || '—',
    matches: Array.isArray(player.matchIDs) ? player.matchIDs.length : 0,
    goals: toNumber(player.goals),
    shots: toNumber(player.shots),
    completedPasses: toNumber(player.passes_completed),
    duelWinRate: player.duels ? Math.round((toNumber(player.duels_won) / Math.max(toNumber(player.duels), 1)) * 100) : 0,
  }));

  const teamRows = topTeams.slice(0, 5).map((team: any) => ({
    id: team.teamID || team.team_id,
    name: team.team_name || team.name || `Team #${team.teamID || team.team_id}`,
    rank: team.rank || '—',
    goals: toNumber(team.goals),
    shots: toNumber(team.shots),
    completedPasses: toNumber(team.passes_completed),
    passCompletion: team.passes ? Math.round((toNumber(team.passes_completed) / Math.max(toNumber(team.passes), 1)) * 100) : 0,
  }));

  const snapshotCards = [
    {
      label: 'Predictions Generated',
      value: formatMetric(predictionSummary.total ?? summary.transferPredictions),
      tone: 'text-purple-400',
    },
    {
      label: 'Accuracy Score',
      value: formatMetric(predictionSummary.accuracy ?? summary.modelAccuracy, 2),
      tone: 'text-green-400',
    },
    {
      label: 'Live Matches',
      value: formatMetric(summary.liveMatches),
      tone: 'text-blue-400',
    },
    {
      label: 'Response Time',
      value: summary.responseTime != null ? `${formatMetric(summary.responseTime)}ms` : '—',
      tone: 'text-yellow-400',
    },
  ];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <BarChart3 className="h-8 w-8 mr-3 text-purple-500" />
          Analytics Lab
        </h1>
        <div className="flex items-center space-x-4">
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg"
          >
            <option value="season">Current Season</option>
            <option value="month">Last Month</option>
            <option value="week">Last Week</option>
          </select>
          <button className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors">
            <Brain className="h-4 w-4" />
            <span>AI Insights</span>
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-slate-400 text-sm">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading live data...
        </div>
      )}

      {/* Analytics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{summary.totalTeams || 0}</div>
              <div className="text-slate-400 text-sm">Teams Analyzed</div>
            </div>
            <Users className="h-8 w-8 text-blue-400" />
          </div>
          <div className="flex items-center mt-2 text-green-400 text-sm">
            <TrendingUp className="h-4 w-4 mr-1" />
            {summary.totalPlayers || 0} players tracked
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{summary.totalMatches || 0}</div>
              <div className="text-slate-400 text-sm">Matches Analyzed</div>
            </div>
            <Activity className="h-8 w-8 text-green-400" />
          </div>
          <div className="flex items-center mt-2 text-green-400 text-sm">
            <TrendingUp className="h-4 w-4 mr-1" />
            {summary.liveMatches || 0} live now
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{summary.scoutingReports || 0}</div>
              <div className="text-slate-400 text-sm">Scouting Reports</div>
            </div>
            <Target className="h-8 w-8 text-purple-400" />
          </div>
          <div className="flex items-center mt-2 text-purple-400 text-sm">
            <Zap className="h-4 w-4 mr-1" />
            ML Enhanced
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{summary.activeScouts || 0}</div>
              <div className="text-slate-400 text-sm">Active Scouts</div>
            </div>
            <Brain className="h-8 w-8 text-yellow-400" />
          </div>
          <div className="flex items-center mt-2 text-yellow-400 text-sm">
            <Activity className="h-4 w-4 mr-1" />
            {summary.recentActivity || 0} recent actions
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Users className="h-6 w-6 mr-2 text-blue-400" />
            Top Team Output
          </h3>
          {teamRows.length > 0 ? (
            <div className="space-y-4">
              {teamRows.map((team) => (
                <div key={team.id} className="rounded-lg bg-slate-700 p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <div>
                      <div className="font-semibold">{team.name}</div>
                      <div className="text-xs text-slate-400">Rank #{team.rank}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-green-400">{team.goals}</div>
                      <div className="text-xs text-slate-400">Goals</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-slate-400">Shots</div>
                      <div className="font-semibold text-white">{team.shots}</div>
                    </div>
                    <div>
                      <div className="text-slate-400">Completed Passes</div>
                      <div className="font-semibold text-white">{team.completedPasses}</div>
                    </div>
                    <div>
                      <div className="text-slate-400">Pass Accuracy</div>
                      <div className="font-semibold text-blue-400">{team.passCompletion}%</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
              No team analytics are available from the backend yet.
            </div>
          )}
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <TrendingUp className="h-6 w-6 mr-2 text-red-400" />
            Competition Trend Analysis
          </h3>
          <div className="space-y-4">
            <div className="flex items-center space-x-4 mb-4">
              <select
                value={selectedMetric}
                onChange={(e) => setSelectedMetric(e.target.value as TrendMetric)}
                className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-sm"
              >
                {Object.entries(METRIC_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
              <span className="text-sm text-slate-400">Latest {trendRows.length} periods</span>
            </div>

            {trendRows.length > 0 ? trendRows.map((trend: any, index: number) => {
              const metricValue = toNumber(trend[selectedMetric]);

              return (
                <div key={`${trend.name}-${index}`} className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">{trend.name}</span>
                  <span className="text-sm font-semibold">{formatMetric(metricValue, selectedMetric === 'matchCount' ? 0 : 2)}</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                  <div
                    className="h-3 rounded-full bg-red-500"
                    style={{ width: `${(metricValue / maxTrendValue) * 100}%` }}
                  ></div>
                </div>
              </div>
              );
            }) : (
              <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
                No league trend data is available from the backend yet.
              </div>
            )}

            <div className="mt-6 p-4 bg-slate-700 rounded-lg">
              <h4 className="font-semibold mb-2 text-red-400">Trend Snapshot</h4>
              <p className="text-sm text-slate-300">
                The live competition feed reports {formatMetric(summary.avgGoalsPerMatch, 2)} average goals per match
                across {summary.totalMatches || 0} analysed fixtures.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-6">
        <h3 className="text-xl font-semibold mb-6 flex items-center">
          <Trophy className="h-6 w-6 mr-2 text-green-400" />
          Top Player Output
        </h3>
        {playerRows.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-2">Player</th>
                  <th className="text-left py-3 px-2">Rank</th>
                  <th className="text-left py-3 px-2">Matches</th>
                  <th className="text-left py-3 px-2">Goals</th>
                  <th className="text-left py-3 px-2">Shots</th>
                  <th className="text-left py-3 px-2">Completed Passes</th>
                  <th className="text-left py-3 px-2">Duel Win %</th>
                </tr>
              </thead>
              <tbody>
                {playerRows.map((player) => (
                  <tr key={player.id} className="border-b border-slate-700 hover:bg-slate-700">
                    <td className="py-3 px-2 font-semibold">{player.name}</td>
                    <td className="py-3 px-2 text-blue-400">#{player.rank}</td>
                    <td className="py-3 px-2">{player.matches}</td>
                    <td className="py-3 px-2">{player.goals}</td>
                    <td className="py-3 px-2">{player.shots}</td>
                    <td className="py-3 px-2">{player.completedPasses}</td>
                    <td className="py-3 px-2">
                      <span className="font-semibold text-green-400">{player.duelWinRate}%</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
            No player output is available from the analytics backend yet.
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Calendar className="h-6 w-6 mr-2 text-yellow-400" />
            Recent Match Feed
          </h3>
          {recentMatches.length > 0 ? (
            <div className="space-y-4">
              {recentMatches.slice(0, 5).map((match: any) => (
                <div key={match.id} className="rounded-lg bg-slate-700 p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="font-medium">{formatMatchLabel(match)}</span>
                    <span className="text-sm text-yellow-400">{match.status || 'unknown'}</span>
                  </div>
                  <div className="flex justify-between text-sm text-slate-400">
                    <span>{formatMetric(match.home_score)} - {formatMetric(match.away_score)}</span>
                    <span>{formatMetric(match.date)}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-lg bg-slate-700 px-4 py-10 text-center text-slate-400">
              No recent matches are available from the analytics backend yet.
            </div>
          )}
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-semibold mb-6 flex items-center">
            <Brain className="h-6 w-6 mr-2 text-purple-400" />
            Prediction Snapshot
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {snapshotCards.map((card) => (
              <div key={card.label} className="rounded-lg border border-slate-700 bg-slate-700/80 p-4">
                <div className="text-sm text-slate-400">{card.label}</div>
                <div className={`mt-2 text-2xl font-bold ${card.tone}`}>{card.value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;